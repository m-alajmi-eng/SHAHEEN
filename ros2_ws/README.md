# SHAHEEN ROS 2 Workspace

Phase 3 ROS 2 packages for SHAHEEN, built with the Bootcamp methodology
(ROS 2 Humble, `colcon`, `ament`). The pipeline is **Perceive → Decide → Act**:

```
Gazebo OakD camera --(ros_gz_bridge)--> /shaheen/camera/image
    --> yolo_detector (YOLOv8n, offline) --> /shaheen/detections
    --> mission_supervisor  --(MAVSDK)-->  PX4   (arm / takeoff / mission / RTL)
        ^ tower clearance service   |  TF map->base_link   |  /shaheen/marker
```

## Packages

| Package | Build type | Contents |
|---------|-----------|----------|
| `shaheen_interfaces` | ament_cmake | `msg/Detection.msg`, `action/InspectRunway.action` |
| `shaheen` | ament_python | `yolo_detector`, `tower`, `mission_supervisor` nodes, launch, config, rviz, models |

## Bootcamp concept → SHAHEEN feature

| Concept | Where |
|---------|-------|
| Pub/Sub (Day 3) | camera image → detector → detections |
| Service (Day 4) | `tower` clearance before inspection |
| Parameters (Day 5) | `config/perception.yaml`, `config/mission.yaml` |
| Launch (Day 5/12) | `shaheen_inspection.launch.py` |
| Action (Day 6) | `/shaheen/inspect_runway` with feedback |
| Custom interfaces (Day 7) | `Detection.msg`, `InspectRunway.action` |
| TF2 (Day 8) | `base_link→camera_link` (static), `map→base_link` (telemetry) |
| RViz2 (Day 9) | `rviz/shaheen.rviz` (image + TF + marker) |
| Rosbag2 (Day 10) | record the run (see below) |
| Camera bridge / OpenCV / MAVSDK (Day 12/13/16+) | detector + supervisor |

## Prerequisites

```bash
sudo apt install ros-humble-desktop ros-humble-ros-gz ros-humble-cv-bridge
pip install -r src/shaheen/requirements.txt          # ultralytics + mavsdk
```

Download the YOLOv8n weights once into `src/shaheen/models/best.pt`
(see `src/shaheen/models/README.md`).

## Build

```bash
cd ros2_ws
colcon build --packages-select shaheen_interfaces shaheen
source install/setup.bash
```

## Run — full inspection

```bash
# 1) PX4 SITL + Gazebo SHAHEEN world (repository root README)
# 2) whole pipeline:
ros2 launch shaheen shaheen_inspection.launch.py
# 3) trigger the inspection (separate terminal):
ros2 action send_goal /shaheen/inspect_runway \
    shaheen_interfaces/action/InspectRunway "{altitude: 4.0}" --feedback
```

## Run — perception only (for detector tuning / rosbag replay)

```bash
ros2 launch shaheen perception.launch.py
ros2 run rqt_image_view rqt_image_view /shaheen/detection_image
```

## Rosbag2 — record & replay (Day 10)

```bash
ros2 bag record -o kkia_inspection_1 \
  /shaheen/camera/image /shaheen/detections /shaheen/detection_image \
  /shaheen/marker /tf /tf_static
ros2 bag play kkia_inspection_1        # replay to re-tune the detector offline
```
