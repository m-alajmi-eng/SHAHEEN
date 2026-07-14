"""
SHAHEEN mission supervisor - the "Decide + Act" brain of Phase 3.

This is the ROS 2 evolution of flight/shaheen_mission.py. It combines the
Bootcamp concepts around a single real workflow:

  * Action server  (Day 6) : /shaheen/inspect_runway - a long-running,
                             cancelable inspection with waypoint feedback.
  * Service client (Day 4) : asks the KKIA tower for clearance before flying.
  * Subscriber     (Day 3) : /shaheen/detections - YOLOv8n hazard events that
                             drive the threat responses (no more waypoint-index
                             faking).
  * Parameters     (Day 5) : connection, altitudes, battery + confidence limits.
  * TF2            (Day 8) : broadcasts map -> base_link from PX4 telemetry.
  * Marker         (Day 9) : flags detected hazards in RViz2.
  * MAVSDK       (Day 16+) : arms, takes off, flies the mission, RTLs.

ROS 2 (callbacks) and MAVSDK (asyncio) are combined with the curriculum's
Day 19/20 approach: the action runs the MAVSDK mission on its own asyncio loop,
while a MultiThreadedExecutor keeps the detections subscription and tower client
responsive.
"""

import asyncio
import threading

import rclpy
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from std_srvs.srv import Trigger
from geometry_msgs.msg import Point, TransformStamped
from visualization_msgs.msg import Marker
from tf2_ros import TransformBroadcaster

from shaheen_interfaces.msg import Detection
from shaheen_interfaces.action import InspectRunway

from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

# Local (x, y) runway waypoints in metres, relative to the drone home point
# (ported unchanged from flight/shaheen_mission.py).
WAYPOINTS_XY = [
    (-45.53, -6.59), (-40.00, -6.09), (-37.50, -5.86), (-35.56, -5.19),
    (-30.00, -4.68), (-15.00, -3.33), (0.00, -1.97), (15.00, -0.61),
    (27.48, 0.00), (-13.50, -24.00),
]

FOD_LABELS = ('fod', 'cone', 'traffic cone', 'traffic-cone')
BIRD_LABELS = ('bird', 'birds')


class MissionSupervisor(Node):
    def __init__(self):
        super().__init__('mission_supervisor')

        # --- Parameters (Day 5) --------------------------------------------
        self.declare_parameter('connection_url', 'udpin://0.0.0.0:14540')
        self.declare_parameter('cruise_altitude', 4.0)
        self.declare_parameter('rtl_altitude', 4.0)
        self.declare_parameter('low_battery_threshold', 0.20)
        self.declare_parameter('detection_confidence_min', 0.5)

        self.connection_url = self.get_parameter('connection_url').value
        self.cruise_altitude = float(self.get_parameter('cruise_altitude').value)
        self.rtl_altitude = float(self.get_parameter('rtl_altitude').value)
        self.low_battery = float(self.get_parameter('low_battery_threshold').value)
        self.conf_min = float(self.get_parameter('detection_confidence_min').value)

        # --- Shared state set from the detections callback -----------------
        self._pending_fod = False
        self._pending_bird = False

        group = ReentrantCallbackGroup()

        # --- ROS interfaces -------------------------------------------------
        self.create_subscription(
            Detection, '/shaheen/detections', self.on_detection, 10,
            callback_group=group)
        self.clearance_client = self.create_client(
            Trigger, '/shaheen/request_clearance', callback_group=group)
        self.marker_pub = self.create_publisher(Marker, '/shaheen/marker', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self._action_server = ActionServer(
            self, InspectRunway, '/shaheen/inspect_runway',
            execute_callback=self.execute_inspection,
            callback_group=group)

        self.get_logger().info('mission_supervisor ready - awaiting inspection goal')

    # ---------------------------------------------------------------------
    # Perceive: record hazard detections (runs on an executor thread).
    # ---------------------------------------------------------------------
    def on_detection(self, msg):
        if msg.confidence < self.conf_min:
            return
        label = msg.label.lower()
        if any(k in label for k in FOD_LABELS):
            self._pending_fod = True
        elif any(k in label for k in BIRD_LABELS):
            self._pending_bird = True

    # ---------------------------------------------------------------------
    # Tower clearance (Day 4 service client), waited on across threads.
    # ---------------------------------------------------------------------
    def request_clearance(self):
        if not self.clearance_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().warn('Tower service unavailable - proceeding without clearance')
            return True
        future = self.clearance_client.call_async(Trigger.Request())
        done = threading.Event()
        future.add_done_callback(lambda _f: done.set())
        done.wait(timeout=5.0)
        response = future.result()
        if response is None:
            self.get_logger().warn('No clearance response - aborting')
            return False
        self.get_logger().info(f'[KKIA TOWER] {response.message}')
        return response.success

    # ---------------------------------------------------------------------
    # Act: the action server runs the MAVSDK mission on its own asyncio loop.
    # ---------------------------------------------------------------------
    def execute_inspection(self, goal_handle):
        self.get_logger().info('Inspection goal accepted')
        if not self.request_clearance():
            goal_handle.abort()
            result = InspectRunway.Result()
            result.completed = False
            return result

        self._pending_fod = False
        self._pending_bird = False
        return asyncio.run(self._fly(goal_handle))

    async def _fly(self, goal_handle):
        result = InspectRunway.Result()
        fod_count = 0
        bird_detected = False

        altitude = float(goal_handle.request.altitude) or self.cruise_altitude

        drone = System()
        self.get_logger().info(f'Connecting to {self.connection_url} ...')
        await drone.connect(system_address=self.connection_url)
        async for state in drone.core.connection_state():
            if state.is_connected:
                self.get_logger().info('Flight controller connected')
                break

        battery_task = asyncio.ensure_future(self._battery_guard(drone))
        tf_task = asyncio.ensure_future(self._broadcast_tf(drone))

        await drone.action.set_return_to_launch_altitude(self.rtl_altitude)

        home = await anext(drone.telemetry.home())
        mission_items = self._build_mission_items(home.latitude_deg, home.longitude_deg, altitude)
        total = len(mission_items)

        await drone.mission.set_return_to_launch_after_mission(True)
        await drone.mission.upload_mission(MissionPlan(mission_items))

        await drone.action.arm()
        async for armed in drone.telemetry.armed():
            if armed:
                break

        await drone.action.set_takeoff_altitude(altitude)
        await drone.action.takeoff()
        self._publish_feedback(goal_handle, 0, total, 'taking off')

        await drone.mission.start_mission()

        async for progress in drone.mission.mission_progress():
            self._publish_feedback(goal_handle, progress.current, progress.total,
                                   'scanning runway')

            if self._pending_fod:
                self._pending_fod = False
                fod_count += 1
                await self._handle_fod(drone)

            elif self._pending_bird:
                self._pending_bird = False
                bird_detected = True
                await self._handle_bird_flock(drone)
                break

            if progress.current >= progress.total:
                break

        battery_task.cancel()
        tf_task.cancel()

        goal_handle.succeed()
        result.completed = True
        result.fod_count = fod_count
        result.bird_detected = bird_detected
        self.get_logger().info(
            f'Inspection complete - FOD: {fod_count}, bird: {bird_detected}')
        return result

    # ---------------------------------------------------------------------
    # Threat responses (ported from flight/shaheen_mission.py).
    # ---------------------------------------------------------------------
    async def _handle_fod(self, drone):
        await drone.mission.pause_mission()
        self.get_logger().info('Alert: FOD identified on runway. Report sent to ATC / Maintenance / KKIA HQ')
        await self._mark_hazard(drone, 'FOD', r=1.0, g=0.5, b=0.0)
        await asyncio.sleep(5)
        self.get_logger().info('Resuming runway scan.')
        await drone.mission.start_mission()

    async def _handle_bird_flock(self, drone):
        await drone.mission.pause_mission()
        self.get_logger().info('Alert: Bird flock detected. Deterrence protocol active.')
        await self._mark_hazard(drone, 'BIRD', r=1.0, g=0.0, b=0.0)
        await asyncio.sleep(5)
        self.get_logger().info('Ultrasound ON, locating wildlife')
        await asyncio.sleep(2)
        self.get_logger().info('[KKIA TOWER] Incoming traffic. Execute RTL immediately.')
        await drone.action.return_to_launch()

    # ---------------------------------------------------------------------
    # Concurrent MAVSDK helpers.
    # ---------------------------------------------------------------------
    async def _battery_guard(self, drone):
        async for battery in drone.telemetry.battery():
            if battery.remaining_percent < self.low_battery:
                self.get_logger().warn('Battery critical - returning to launch')
                await drone.action.return_to_launch()
                return

    async def _broadcast_tf(self, drone):
        """Publish map -> base_link from PX4 NED telemetry (ENU for ROS)."""
        async for ned in drone.telemetry.position_velocity_ned():
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'map'
            t.child_frame_id = 'base_link'
            t.transform.translation.x = ned.position.east_m
            t.transform.translation.y = ned.position.north_m
            t.transform.translation.z = -ned.position.down_m
            t.transform.rotation.w = 1.0
            self.tf_broadcaster.sendTransform(t)

    async def _mark_hazard(self, drone, label, r, g, b):
        pos = await anext(drone.telemetry.position_velocity_ned())
        m = Marker()
        m.header.frame_id = 'map'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = label
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose.position = Point(x=pos.position.east_m, y=pos.position.north_m,
                                z=-pos.position.down_m)
        m.pose.orientation.w = 1.0
        m.scale.x = m.scale.y = m.scale.z = 1.0
        m.color.r, m.color.g, m.color.b, m.color.a = r, g, b, 1.0
        self.marker_pub.publish(m)

    # ---------------------------------------------------------------------
    # Helpers.
    # ---------------------------------------------------------------------
    def _build_mission_items(self, home_lat, home_lon, altitude):
        items = []
        for x, y in WAYPOINTS_XY:
            lat = home_lat + y * 8.983e-6
            lon = home_lon + x * 1.327e-5
            items.append(MissionItem(
                lat, lon, altitude, 7, True,
                float('nan'), float('nan'), MissionItem.CameraAction.NONE,
                float('nan'), float('nan'), 1.0,
                float('nan'), float('nan'), MissionItem.VehicleAction.NONE))
        return items

    def _publish_feedback(self, goal_handle, current, total, status):
        fb = InspectRunway.Feedback()
        fb.current_waypoint = int(current)
        fb.total_waypoints = int(total)
        fb.status = status
        goal_handle.publish_feedback(fb)


def main(args=None):
    rclpy.init(args=args)
    node = MissionSupervisor()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
