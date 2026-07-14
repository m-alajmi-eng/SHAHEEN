# SHAHEEN - Technical Guide

**SHAHEEN** is an autonomous drone-based system for the automated inspection of
airport runways at **King Khalid International Airport (KKIA)**. It detects
Foreign Object Debris (FOD) and manages biological threats (bird flocks) using
intelligent flight logic powered by **MAVSDK** and **PX4**, simulated in
**Gazebo**.

This guide follows the engineering methodology of the Unmanned Systems Bootcamp
reference project (`PX4-Sim-Starter`).

---

## Repository Layout

```text
SHAHEEN/
├── flight/shaheen_mission.py   # Canonical MAVSDK mission controller
├── simulation/
│   ├── worlds/SHAHEEN_World.sdf # KKIA airport world
│   └── models/                 # Drone (x500_x), sensors (OakD-Lite, lidar), threats, scenery
├── docs/                       # This guide, presentations, media
└── legacy/SHAHEEN_V.1/         # Archived first iteration
```

---

## Key Dependencies

* **PX4 Autopilot:** Firmware v1.14+
* **Gazebo:** Harmonic or Garden
* **MAVSDK:** Python wrapper (`pip install mavsdk`)
* **Python:** 3.10+ (with `asyncio`)
* **OS:** Ubuntu 22.04 LTS (recommended)
* **QGroundControl:** optional, for live telemetry

---

## Deployment Guide

### Step 1: Configure the Environment

From the repository root, expose the custom assets to Gazebo:

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/simulation/models:$PWD/simulation/worlds
```

### Step 2: Launch the Simulation

From your `PX4-Autopilot` directory:

```bash
PX4_SYS_AUTOSTART=4001 \
PX4_GZ_MODEL_POSE="0,-0.06,0.20,0.01,0,0.13" \
PX4_GZ_WORLD=SHAHEEN_World \
PX4_SIM_MODEL=gz_x500_x \
./build/px4_sitl_default/bin/px4
```

**Configuration breakdown:**

* `PX4_SYS_AUTOSTART=4001` - loads the pre-configured airframe settings.
* `PX4_GZ_MODEL_POSE` - defines the spawn pose within the airport environment.
* `PX4_GZ_WORLD=SHAHEEN_World` - loads `simulation/worlds/SHAHEEN_World.sdf`.
* `PX4_SIM_MODEL=gz_x500_x` - spawns the SHAHEEN drone model (`simulation/models/x500_x`).

### Step 3: Execute the Mission

From the repository root, in a new terminal:

```bash
python3 flight/shaheen_mission.py
```

---

## Mission Structure (`flight/shaheen_mission.py`)

* `build_mission_items()` - converts local (x, y) offsets in metres, relative to the drone home point, into the runway waypoint plan.
* `wait_for_connection()` / `wait_until_armed()` / `wait_for_takeoff_altitude()` - telemetry monitors following the Bootcamp async idiom.
* `battery_checker()` - concurrent safety monitor that triggers RTL below 20 % battery.
* `handle_fod()` / `handle_bird_flock()` - threat-response coroutines for identifying and responding to runway obstructions.
* `run()` - connect -> upload -> arm -> takeoff -> start mission -> monitor progress.

---

## Troubleshooting

* **World fails to load:** confirm `GZ_SIM_RESOURCE_PATH` includes both `simulation/models` and `simulation/worlds`, and that `PX4_GZ_WORLD` matches the world file name `SHAHEEN_World`.
* **Connection timeout:** ensure the PX4 SITL instance is fully booted and nothing else is bound to port `14540`.
* **Mission stalls:** confirm the drone is in `Hold`/`Mission` mode in QGroundControl.
* **Camera topics absent (needed for Phase 3):** verify the simulation is publishing the OakD-Lite camera with `gz topic -l | grep -i camera`. If empty, the world-level Gazebo sensors system will be enabled during Phase 3.

---

## Roadmap

| Phase | Technology | Goal |
| --- | --- | --- |
| **Current** | MAVSDK / PX4 / Gazebo | Runway inspection & FOD/bird simulation |
| **Phase 3** | ROS 2 (Humble) + YOLO | Real-time, camera-driven object detection |
| **Future** | Swarm + Micro-XRCE-DDS | Multi-drone coordinated coverage |

---

## Developer Information

* **Developer:** Eng. Mohammed S. Alajmi
* **Affiliation:** Tuwaiq Academy
