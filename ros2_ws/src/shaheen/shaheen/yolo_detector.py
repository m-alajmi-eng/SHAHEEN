"""
SHAHEEN perception node - YOLOv8n runway-hazard detector.

Follows the Bootcamp curriculum's detector pattern (Day 13 image processing,
Day 14 ArUco detector): a single rclpy Node that subscribes to the camera
image, converts it with cv_bridge, runs inference, and publishes results.

The only difference from the curriculum's classical-OpenCV example is that the
detector is a pretrained YOLOv8n model loaded with Ultralytics. The weights are
stored locally and loaded offline - the node never contacts any online service.

Pipeline position:
    ros_gz_bridge -> /shaheen/camera/image -> [this node] -> /shaheen/detections
"""

import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point
from cv_bridge import CvBridge

from shaheen_interfaces.msg import Detection


class YoloDetector(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        # --- Parameters (Day 5) --------------------------------------------
        self.declare_parameter('camera_topic', '/shaheen/camera/image')
        self.declare_parameter('model_path', '')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('detect_rate_hz', 5.0)

        camera_topic = self.get_parameter('camera_topic').value
        model_path = self.get_parameter('model_path').value
        self.confidence = float(self.get_parameter('confidence_threshold').value)
        rate = float(self.get_parameter('detect_rate_hz').value)
        self.min_period = (1.0 / rate) if rate > 0.0 else 0.0
        self.last_infer_s = 0.0

        # --- Load the model once, offline ----------------------------------
        if not model_path or not os.path.isfile(model_path):
            self.get_logger().error(
                f"YOLOv8n weights not found at '{model_path}'. "
                "Download them once (see ros2_ws/src/shaheen/models/README.md) "
                "and rebuild. The node loads the weights offline.")
            raise SystemExit(1)

        # Imported here so the module still syntax-checks without ultralytics
        # installed; the real dependency is required only at runtime.
        from ultralytics import YOLO
        self.get_logger().info(f'Loading YOLOv8n weights (offline): {model_path}')
        self.model = YOLO(model_path)

        # --- ROS interfaces (Day 3) ----------------------------------------
        self.bridge = CvBridge()
        self.sub = self.create_subscription(Image, camera_topic, self.on_image, 10)
        self.det_pub = self.create_publisher(Detection, '/shaheen/detections', 10)
        self.image_pub = self.create_publisher(Image, '/shaheen/detection_image', 10)

        self.get_logger().info(
            f"yolo_detector ready - subscribing to '{camera_topic}', "
            f"conf>={self.confidence}, rate={rate} Hz")

    def on_image(self, msg):
        # Throttle inference to keep YOLOv8n light on CPU.
        now_s = self.get_clock().now().nanoseconds * 1e-9
        if self.min_period and (now_s - self.last_infer_s) < self.min_period:
            return
        self.last_infer_s = now_s

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(frame, conf=self.confidence, verbose=False)[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            det = Detection()
            det.header = msg.header
            det.label = self.model.names.get(cls_id, str(cls_id))
            det.confidence = float(box.conf[0])
            det.position = Point(x=(x1 + x2) / 2.0, y=(y1 + y2) / 2.0, z=0.0)
            det.area = float((x2 - x1) * (y2 - y1))
            self.det_pub.publish(det)

            self.get_logger().info(
                f'Detected {det.label} ({det.confidence:.2f}) '
                f'at ({det.position.x:.0f}, {det.position.y:.0f})')

        # Publish the annotated frame for rqt_image_view / RViz2.
        annotated = results.plot()
        out = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        out.header = msg.header
        self.image_pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
