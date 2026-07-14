# SHAHEEN ROS 2 Workspace

Phase 3 ROS 2 packages for SHAHEEN, built with the Bootcamp methodology
(ROS 2 Humble, `colcon`, `ament`). Stage 1 delivers the **perception half** of
the pipeline:

```
Gazebo OakD camera --(ros_gz_bridge)--> /shaheen/camera/image
    --> yolo_detector (YOLOv8n, offline) --> /shaheen/detections (Detection.msg)
                                         --> /shaheen/detection_image
```

The Decide/Act half (mission_supervisor, tower service, InspectRunway action,
MAVSDK) arrives in Stage 2.

## Packages

| Package | Build type | Contents |
|---------|-----------|----------|
| `shaheen_interfaces` | ament_cmake | `msg/Detection.msg` |
| `shaheen` | ament_python | `yolo_detector` node, launch, config, models |

## Prerequisites

```bash
# ROS 2 Humble + bridge + cv_bridge (apt)
sudo apt install ros-humble-desktop ros-humble-ros-gz ros-humble-cv-bridge
# Python perception dependency (pip)
pip install -r src/shaheen/requirements.txt   # ultralytics (pulls torch)
```

Then download the YOLOv8n weights once into
`src/shaheen/models/best.pt` — see `src/shaheen/models/README.md`.

## Build

```bash
cd ros2_ws
colcon build --packages-select shaheen_interfaces shaheen
source install/setup.bash
```

## Run (perception smoke test)

1. Launch PX4 SITL + Gazebo with the SHAHEEN world (see repository root README).
2. Bring up the bridge + detector:

```bash
ros2 launch shaheen perception.launch.py
```

3. Verify the pipeline:

```bash
ros2 topic hz /shaheen/camera/image        # camera is flowing from Gazebo
ros2 topic echo /shaheen/detections        # Detection.msg on each hit
ros2 run rqt_image_view rqt_image_view /shaheen/detection_image   # annotated view
```

If `/shaheen/camera/image` shows no data, the Gazebo `Sensors` system is not
publishing the camera — enable it at the world level (a Stage 1 contingency)
and re-run.
