# SHAHEEN: Autonomous Runway Sentinel System

**SHAHEEN** is an advanced autonomous drone-based solution engineered for the automated inspection of airport runways. Designed to enhance aviation safety at **King Khalid International Airport (KKIA)**, the system uses intelligent flight logic to detect Foreign Object Debris (FOD) and manage biological threats such as bird flocks in real time.

The project is built on the PX4 + Gazebo + MAVSDK stack and follows the engineering methodology of the Unmanned Systems Bootcamp reference project (`PX4-Sim-Starter`).

---

## Project Structure

The repository is organized by **capability** rather than by version. The current
system lives at the top level; the initial iteration is archived under `legacy/`
for provenance.

```text
SHAHEEN/
├── flight/                     # Canonical MAVSDK mission controller
│   └── shaheen_mission.py
├── simulation/                 # Gazebo simulation assets
│   ├── worlds/                 # Airport world (SHAHEEN_World.sdf)
│   └── models/                 # Custom 3D models (drone, sensors, FOD, wildlife, scenery)
├── docs/                       # Technical documentation and media
│   ├── README.md               # Canonical technical guide
│   ├── presentations/          # Project presentations (PDF)
│   └── media/                  # Screenshots and captures
├── legacy/                     # Archived earlier iteration (SHAHEEN V.1)
│   └── SHAHEEN_V.1/
└── README.md                   # This file
```

---

## Deployment Guide

Follow these steps to initialize the environment and execute the inspection mission.

### Step 1: Environment Configuration

From the repository root, expose the custom models and world to the Gazebo
resource path so the simulation engine can locate the airport assets:

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/simulation/models:$PWD/simulation/worlds
```

### Step 2: Launch the Simulation

Navigate to your `PX4-Autopilot` directory to initialize the flight stack, load
the custom KKIA airport world, and spawn the drone:

```bash
PX4_SYS_AUTOSTART=4001 \
PX4_GZ_MODEL_POSE="0,-0.06,0.20,0.01,0,0.13" \
PX4_GZ_WORLD=SHAHEEN_World \
PX4_SIM_MODEL=gz_x500_x \
./build/px4_sitl_default/bin/px4
```

### Step 3: Execute the Mission

Once the simulation is stable, open a new terminal, return to the repository
root, and run the Python control script to begin the autonomous inspection:

```bash
python3 flight/shaheen_mission.py
```

See [`docs/README.md`](docs/README.md) for the full technical guide,
dependencies, and troubleshooting.

---

## Technical Highlights

* **Intelligent Flight Logic:** Uses `MAVSDK` and `PX4` for precise mission execution across a 10-waypoint runway scan.
* **Asynchronous Processing:** Uses Python's `asyncio` to manage telemetry and mission tasks concurrently.
* **Safety Protocols:** Automated **Return to Launch (RTL)** triggered by low battery or tower abort orders.
* **Real-time Monitoring:** Supports integration with **QGroundControl** for live telemetry and flight-path visualization.

---

## Roadmap & Future Development

| Phase | Technology | Goal |
| --- | --- | --- |
| **Current** | MAVSDK / PX4 / Gazebo | Runway inspection & FOD/bird simulation |
| **Phase 3** | ROS 2 (Humble) + YOLO | Real-time, camera-driven object detection |
| **Future** | Swarm + Micro-XRCE-DDS | Multi-drone coordinated coverage |

---

## Developer Information

* **Developer:** Eng. Mohammed S. Alajmi
* **Affiliation:** Tuwaiq Academy

*This project follows open-source automation standards to ensure compatibility with future smart-airport infrastructures.*
