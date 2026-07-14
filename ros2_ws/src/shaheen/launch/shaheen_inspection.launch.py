"""
SHAHEEN full inspection bring-up (Stage 2).

Starts the complete Perceive -> Decide -> Act pipeline with one command:

    ros_gz_bridge          camera + clock  (Gazebo -> ROS)
    yolo_detector          YOLOv8n hazard detection
    tower                  clearance service
    mission_supervisor     action server + MAVSDK flight
    static_transform_publisher   base_link -> camera_link (fixed mount, Day 8)
    rviz2                  visualization (Day 9)

Trigger an inspection from a separate terminal:
    ros2 action send_goal /shaheen/inspect_runway \\
        shaheen_interfaces/action/InspectRunway "{altitude: 4.0}" --feedback
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('shaheen')
    perception_params = os.path.join(pkg_share, 'config', 'perception.yaml')
    mission_params = os.path.join(pkg_share, 'config', 'mission.yaml')
    model_path = os.path.join(pkg_share, 'models', 'best.pt')
    rviz_config = os.path.join(pkg_share, 'rviz', 'shaheen.rviz')

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
        package='shaheen', executable='yolo_detector', name='yolo_detector',
        parameters=[perception_params, {'model_path': model_path}],
        output='screen',
    )

    tower = Node(
        package='shaheen', executable='tower', name='tower',
        parameters=[mission_params], output='screen',
    )

    mission_supervisor = Node(
        package='shaheen', executable='mission_supervisor', name='mission_supervisor',
        parameters=[mission_params], output='screen',
    )

    # Fixed camera mount on the drone body (OakD pose from the x500_x model).
    static_tf = Node(
        package='tf2_ros', executable='static_transform_publisher',
        name='base_to_camera',
        arguments=['0.12', '0.03', '0.242', '0', '0', '0', 'base_link', 'camera_link'],
        output='screen',
    )

    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', rviz_config], output='screen',
    )

    return LaunchDescription([
        camera_bridge, yolo_detector, tower, mission_supervisor, static_tf, rviz,
    ])
