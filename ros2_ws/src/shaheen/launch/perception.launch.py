"""
SHAHEEN Stage 1 perception bring-up.

Starts the Gazebo -> ROS 2 camera bridge and the YOLOv8n detector with one
command (Day 5 launch files, Day 12 ros_gz_bridge in a launch file):

    Gazebo camera --(ros_gz_bridge)--> /shaheen/camera/image --> yolo_detector
                                                              --> /shaheen/detections
                                                              --> /shaheen/detection_image

The YOLOv8n weights are loaded offline from this package's installed
'models/best.pt'. Download them once (see models/README.md) before building.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('shaheen')
    params_file = os.path.join(pkg_share, 'config', 'perception.yaml')
    model_path = os.path.join(pkg_share, 'models', 'best.pt')

    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='camera_bridge',
        arguments=[
            '/shaheen/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    yolo_detector = Node(
        package='shaheen',
        executable='yolo_detector',
        name='yolo_detector',
        parameters=[params_file, {'model_path': model_path}],
        output='screen',
    )

    return LaunchDescription([camera_bridge, yolo_detector])
