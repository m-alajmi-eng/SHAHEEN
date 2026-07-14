# SHAHEEN: Autonomous Runway Sentinel System

**Tuwaiq Academy Project**
**Eng:Mohammed S. Alajmi**
---

## 1. Project Overview

**SHAHEEN** is an advanced autonomous drone-based solution designed for the automated inspection of airport runways, specifically tailored for King Khalid International Airport (KKIA). The system enhances aviation safety by autonomously detecting Foreign Object Debris (FOD) and managing biological threats (bird flocks) using intelligent flight logic powered by **MAVSDK** and **PX4**.

---

## 2. Prerequisites

* **OS:** Native Linux Environment
* **Language:** Python 3.x
* **Core Libraries:** `pip install mavsdk asyncio`
* **Simulation:** PX4 SITL (Software In The Loop)

---

## 3. Getting Started from Scratch

Follow these steps to initialize and execute your first mission:

### I. Launch the Simulation (PX4 SITL)

Open a terminal, navigate to your `PX4-Autopilot` directory, and launch the simulation environment with the coordinate configuration:

```bash
cd ~/PX4-Autopilot
export PX4_HOME_LAT=24.9777592
export PX4_HOME_LON=46.7020021
make px4_sitl jmavsim

```

### II. Initialize Ground Control

Open **QGroundControl**. The application will automatically detect the simulation running on your local machine and display the drone's position, telemetry, and flight path in real-time.

### III. Execute Mission

In a new terminal window, navigate to your project directory and execute your Python mission script:

```bash
python3 Mission_KKIA.py
```

### IV. Monitor Execution

Observe the drone in the simulation window as it executes the 30-waypoint mission, performs obstacle detection, and handles system triggers autonomously.

---

## 4. Technical Highlights

* **Asynchronous Flight:** Utilizes `asyncio` to manage multiple mission tasks concurrently without blocking operations.
* **Safety Standards:** Implements automated **Return to Launch (RTL)** logic triggered by low battery or critical system faults.
* **Threat Response:** Intelligent logic for handling bird flock encounters via secure deviation maneuvers and automated dispersal systems.

---

## 5. Code Structure

* `setup_mission_points()`: Generates the precise 30-waypoint flight path for the runway.
* `check_drone_state()`: Real-time monitoring functions for telemetry and flight health.
* `handle_fod()` & `handle_bird_flock()`: Decision-making modules for identifying and responding to runway obstructions.

---

## 6. Troubleshooting

* **Simulation Fails to Launch:** Ensure your `PX4-Autopilot` dependencies are fully installed.
* **Connection Timeout:** If the script fails to connect, ensure the SITL instance is fully booted and no other processes are using port `14540`.
* **Mission Stalls:** Confirm that the drone is in "Guided" or "Offboard" mode via the QGroundControl interface.

---

## 7. Future Roadmap

| Phase | Technology | Goal |
| --- | --- | --- |
| **Current** | MAVSDK/PX4 | Runway Inspection & FOD Simulation |
| **Phase 2** | Gazebo | Real-time simulation |
| **Phase 3** | ROS2/YOLO | Real-time Object Detection |
