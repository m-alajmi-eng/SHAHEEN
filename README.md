# SHAHEEN: Autonomous Runway Sentinel System

**SHAHEEN** is an advanced autonomous drone-based solution engineered for the automated inspection of airport runways. Designed to enhance aviation safety at **King Khalid International Airport (KKIA)**, the system utilizes intelligent flight logic to detect Foreign Object Debris (FOD) and manage biological threats such as bird flocks in real-time.

---

## Project Structure

The repository is organized to maintain a clear distinction between core flight logic, simulation assets, and historical project documentation:

```text
SHAHEEN/
├── SHAHEEN_V1/          # Initial project iteration and mission logic
├── SHAHEEN_V2/          # Advanced simulation environment and models
│   ├── models/          # Custom 3D assets (Drone, FOD, Wildlife)
│   ├── worlds/          # Airport simulation environment (aaa.sdf)
│   └── scripts/         # Intelligent control logic (ppp.py)
└── README.md            # Technical documentation

```

---

## Deployment Guide

Follow these steps to initialize the environment and execute the inspection mission.

### Step 1: Environment Configuration

Before launching the simulation, you must configure the resource path so the simulation engine can locate your custom airport assets. Run the following command within the project root:

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/SHAHEEN_V2/models:$PWD/SHAHEEN_V2/worlds

```

### Step 2: Launch the Simulation

Navigate to your `PX4-Autopilot` directory to initialize the flight stack, load the custom KKIA airport world, and position the drone. Execute the following command:

```bash
PX4_SYS_AUTOSTART=4001 \
PX4_GZ_MODEL_POSE="0,-0.06,0.20,0.01,0,0.13" \
PX4_GZ_WORLD=aaa \
PX4_SIM_MODEL=gz_x500_x \
./build/px4_sitl_default/bin/px4

```

### Step 3: Execute Mission

Once the simulation environment is stable, open a new terminal, navigate to the `SHAHEEN_V2` folder, and execute the Python control script to begin the autonomous inspection:

```bash
python3 scripts/ppp.py

```

---

## Technical Highlights

* **Intelligent Flight Logic:** Uses `MAVSDK` and `PX4` for precise mission execution, including a 30-waypoint flight plan.
* **Asynchronous Processing:** Utilizes Python’s `asyncio` to manage telemetry and mission tasks concurrently.
* **Safety Protocols:** Implements automated **Return to Launch (RTL)** logic triggered by low battery or critical system faults.
* **Real-time Monitoring:** Supports integration with **QGroundControl** for live telemetry and flight path visualization.

---

## Roadmap & Future Development

* **Computer Vision:** Integration of **YOLOv8** for high-accuracy object detection.
* **Swarm Intelligence:** Deployment of multi-drone coordinated coverage.
* **ROS2 Transition:** Moving to **ROS2** to support distributed processing and enhanced scalability.

---

## Developer Information

* **Developer:** Eng. Mohammed S. Alajmi
* **Affiliation:** Tuwaiq Academy

*This project follows open-source automation standards to ensure compatibility with future smart airport infrastructures.*
