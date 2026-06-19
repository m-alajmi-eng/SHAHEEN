# SHAHEEN V.2 - Autonomous Runway Sentinel

**SHAHEEN V.2** is an advanced autonomous drone-based solution engineered for the automated inspection of airport runways. Designed to enhance aviation safety at **King Khalid International Airport (KKIA)**, the system utilizes intelligent flight logic to detect Foreign Object Debris (FOD) and manage biological threats (bird flocks) in real-time.

---

## Project Structure

```text
SHAHEEN_V.2/
├── models/          # Custom 3D assets (Drone, FOD, Wildlife)
├── worlds/          # Airport simulation environment (aaa.sdf)
├── scripts/         # Intelligent control logic (ppp.py)
└── README.md        # Technical documentation

```

---

## Deployment Guide

Follow these steps to initialize the SHAHEEN V.2 environment and execute the inspection mission.

### Step 1: Configure the Environment

You must inform the Gazebo simulation engine about your custom project assets. Execute this command inside the `SHAHEEN_V.2` root directory:

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/models:$PWD/worlds

```

### Step 2: Launch the Simulation

Navigate to your `PX4-Autopilot` directory and launch the simulation environment. This command initializes the flight stack, loads the custom airport world, and positions the drone:

```bash
PX4_SYS_AUTOSTART=4001 \
PX4_GZ_MODEL_POSE="0,-0.06,0.20,0.01,0,0.13" \
PX4_GZ_WORLD=aaa \
PX4_SIM_MODEL=gz_x500_x \
./build/px4_sitl_default/bin/px4

```

**Configuration Breakdown:**

* **`PX4_SYS_AUTOSTART=4001`**: Loads the pre-configured airframe settings.
* **`PX4_GZ_MODEL_POSE`**: Defines the precise takeoff coordinates within the airport environment.
* **`PX4_GZ_WORLD=aaa`**: Loads your custom airport world file.
* **`PX4_SIM_MODEL=gz_x500_x`**: Specifies the modified SHAHEEN drone model.

### Step 3: Execute the Mission

Once the simulation is stable, open a new terminal window, navigate to your project folder, and run the Python control script to begin the autonomous inspection:

```bash
python3 scripts/ppp.py

```

---

## Future Roadmap

* **Computer Vision:** Integration of **YOLOv8** for real-time, high-accuracy object detection.
* **Swarm Intelligence:** Deployment of multi-drone coordinated coverage for faster runway clearing.
* **ROS2 Integration:** Transitioning to **ROS2** to support distributed processing and enhanced scalability.

---

## Key Dependencies
* **PX4 Autopilot:** Firmware v1.14+
* **Gazebo:** Harmonic or Garden
* **MAVSDK:** Python Wrapper
* **Python:** 3.10+ (with `asyncio` support)


---

## Developer Information

* **Developer:** Eng. Mohammed S. Alajmi
* **Affiliation:** Tuwaiq Academy

*This project is built following open-source automation standards to ensure compatibility with future smart airport infrastructures.*
