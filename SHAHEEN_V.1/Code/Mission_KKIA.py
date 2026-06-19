import asyncio
import random
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

DRONE_NAME = "SHAHEEN-1"
TOWER_NAME = "RUH TOWER"

RUNWAY_START = (24.9775425, 46.7015176)
RUNWAY_END = (24.9432201, 46.7231966)

FOD_WAYPOINT = 2
BIRD_WAYPOINT = 3
BIRD_DIVERT_LOCATION = (24.945, 46.805, 20, 90)


def setup_mission_points():
    mission_items = []
    for i in range(30):
        lat = RUNWAY_START[0] + ((RUNWAY_END[0] - RUNWAY_START[0]) / 29) * i
        lon = RUNWAY_START[1] + ((RUNWAY_END[1] - RUNWAY_START[1]) / 29) * i

        mission_items.append(
            MissionItem(
                lat, lon,
                10, 5, True,
                float('nan'), float('nan'),
                MissionItem.CameraAction.NONE,
                float('nan'), float('nan'), float('nan'), float('nan'), float('nan'),
                MissionItem.VehicleAction.NONE
            )
        )
    return mission_items


# ==========================================
async def check_connection(drone: System):
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[SYSTEM] Drone connected successfully")
            return


async def check_arming(drone: System):
    async for armed in drone.telemetry.armed():
        if armed:
            print(f"[SYSTEM] Arming confirmed: {armed}")
            return


async def check_takingoff(drone: System):
    async for state in drone.telemetry.landed_state():
        if state == state.IN_AIR:
            print("[SYSTEM] Drone is IN AIR. Takeoff successful")
            return


# ==========================================

async def check_drone_state(drone):
    async for landed_state in drone.telemetry.landed_state():
        if landed_state == landed_state.ON_GROUND:
            print("\n[SUCCESS] Landing confirmed. Mission ended successfully.")
            break


async def battery_checker(drone):
    async for battery in drone.telemetry.battery():
        if battery.remaining_percent < 20:
            print(f"[{DRONE_NAME}] Battery critical! Returning to launch...")
            await drone.action.return_to_launch()
            break


async def handle_fod(pos):
    conf = random.uniform(95.0, 99.5)
    print(f"\n[AI VISION] FOD Detected! Confidence: {conf:.1f}%")
    print(f"[SYSTEM] FOD located at: {pos.latitude_deg:.6f}, {pos.longitude_deg:.6f}")
    print("[SYSTEM] Maintenance team notified...")
    await asyncio.sleep(2)


async def handle_bird_flock(drone):
    conf = random.uniform(90.0, 99.9)
    print(f"\n[AI VISION] Bird Flock Detected! Confidence: {conf:.1f}%")
    print("[SYSTEM] Pausing main mission...")
    print("[SYSTEM] Diverting to perimeter...")

    await drone.mission.pause_mission()
    await drone.action.goto_location(*BIRD_DIVERT_LOCATION)
    await asyncio.sleep(10)

    print("[DRONE] Activating Ultrasonic Dispersal System...")
    await asyncio.sleep(10)

    print("[DRONE] Scanning surroundings for biological threats...")
    await asyncio.sleep(5)

    print("[DRONE] Area cleared. No bird activity detected.")
    await asyncio.sleep(5)

    print("[DRONE] Requesting tower permission to resume inspection...")
    await asyncio.sleep(15)

    print(f"\n[{TOWER_NAME}] Incoming traffic on runway. ACCESS DENIED. Execute RTL!")
    await drone.action.return_to_launch()
    await check_drone_state(drone)


async def run_mission():
    drone = System()
    print('Connecting to drone...')
    await drone.connect(system_address="udp://:14540")

    await check_connection(drone)

    battery_task = asyncio.create_task(battery_checker(drone))

    print(f"[{DRONE_NAME}] Requesting clearance for Runway Inspection...")
    await asyncio.sleep(3)
    print(f"[{TOWER_NAME}] Clearance GRANTED. Runway clear. Proceed.")

    await drone.mission.clear_mission()

    mission_items = setup_mission_points()
    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(mission_plan)

    print("Arming drone...")
    await drone.action.arm()
    await check_arming(drone)

    print("Taking off...")
    await drone.action.takeoff()
    await check_takingoff(drone)
    await asyncio.sleep(5)

    print("Starting Runway Inspection Mission...")
    await drone.mission.start_mission()

    async for progress in drone.mission.mission_progress():
        flight_mode = await anext(drone.telemetry.flight_mode())
        pos = await anext(drone.telemetry.position())

        print(
            f"[{DRONE_NAME}] "
            f"WP: {progress.current:02d} | "
            f"Mode: {flight_mode.name}"
        )

        if progress.current == FOD_WAYPOINT:
            await handle_fod(pos)

        elif progress.current == BIRD_WAYPOINT:
            await handle_bird_flock(drone)
            break

    battery_task.cancel()



asyncio.run(run_mission())
