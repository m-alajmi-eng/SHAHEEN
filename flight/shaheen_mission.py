"""
SHAHEEN - Autonomous Runway Sentinel.

Canonical mission controller for the automated runway inspection of
King Khalid International Airport (KKIA).

The flight logic follows the Unmanned Systems Bootcamp (PX4-Sim-Starter)
methodology:

  * asyncio + MAVSDK ``System()`` over ``udp://:14540``
  * home-relative waypoint generation
  * concurrent telemetry monitors created with ``asyncio.create_task``
  * ``MissionItem`` / ``MissionPlan`` upload with return-to-launch after mission
  * explicit takeoff sequence with an altitude-reached check

SHAHEEN-specific behaviour (FOD detection and bird-flock deterrence) is
preserved from SHAHEEN V.2 and factored into dedicated coroutines so that the
Phase 3 perception layer can trigger them from real detections.
"""

import asyncio

from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

# --- Configuration -----------------------------------------------------------
DRONE_NAME = "SHAHEEN-1"
SYSTEM_ADDRESS = "udp://:14540"

CRUISE_ALTITUDE_M = 4.0
RTL_ALTITUDE_M = 4.0
LOW_BATTERY_THRESHOLD = 0.20  # fraction remaining (20 %)

FOD_WAYPOINT = 2    # traffic cone (Foreign Object Debris) location
BIRD_WAYPOINT = 10  # bird-flock location

# Local (x, y, altitude) waypoints in metres, relative to the drone home point.
WAYPOINTS_XY_ALT = [
    (-45.53, -6.59, CRUISE_ALTITUDE_M),   # WP 1
    (-40.00, -6.09, CRUISE_ALTITUDE_M),   # WP 2  FOD (traffic cone) location
    (-37.50, -5.86, CRUISE_ALTITUDE_M),   # WP 3
    (-35.56, -5.19, CRUISE_ALTITUDE_M),   # WP 4
    (-30.00, -4.68, CRUISE_ALTITUDE_M),   # WP 5
    (-15.00, -3.33, CRUISE_ALTITUDE_M),   # WP 6
    (  0.00, -1.97, CRUISE_ALTITUDE_M),   # WP 7
    ( 15.00, -0.61, CRUISE_ALTITUDE_M),   # WP 8
    ( 27.48,  0.00, CRUISE_ALTITUDE_M),   # WP 9
    (-13.50, -24.00, CRUISE_ALTITUDE_M),  # WP 10  bird-flock location
]


# --- Telemetry monitors (Bootcamp idiom) ------------------------------------
async def wait_for_connection(drone: System):
    """Block until the flight controller reports a connection."""
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"[{DRONE_NAME}] Connected to flight controller")
            return


async def wait_until_armed(drone: System):
    """Block until the vehicle confirms it is armed."""
    async for armed in drone.telemetry.armed():
        if armed:
            print(f"[{DRONE_NAME}] Armed")
            return


async def wait_for_takeoff_altitude(drone: System, target_min: float, target_max: float):
    """Block until the relative altitude is within the requested band."""
    async for position in drone.telemetry.position():
        if target_min <= position.relative_altitude_m <= target_max:
            print(f"[{DRONE_NAME}] Reached takeoff altitude "
                  f"({position.relative_altitude_m:.1f} m)")
            return


async def battery_checker(drone: System):
    """Trigger a return-to-launch when the battery drops below the threshold."""
    async for battery in drone.telemetry.battery():
        if battery.remaining_percent < LOW_BATTERY_THRESHOLD:
            print(f"[{DRONE_NAME}] Battery critical - returning to launch")
            await drone.action.return_to_launch()
            return


# --- Waypoint construction ---------------------------------------------------
def build_mission_items(home_lat: float, home_lon: float):
    """Convert the local (x, y) offsets in metres into a list of MissionItems."""

    def to_lat_lon(x, y):
        lat = home_lat + y * 8.983e-6
        lon = home_lon + x * 1.327e-5
        return lat, lon

    mission_items = []
    for x, y, altitude in WAYPOINTS_XY_ALT:
        target_lat, target_lon = to_lat_lon(x, y)
        mission_items.append(
            MissionItem(
                target_lat, target_lon,
                altitude,
                7,             # speed (m/s)
                True,          # fly-through
                float('nan'), float('nan'),
                MissionItem.CameraAction.NONE,
                float('nan'), float('nan'),
                1.0,           # acceptance radius (m)
                float('nan'), float('nan'),
                MissionItem.VehicleAction.NONE,
            )
        )
    return mission_items


# --- Threat-response coroutines (SHAHEEN behaviour, preserved) ---------------
async def handle_fod(drone: System):
    """Pause the scan, report the FOD, then resume the runway inspection."""
    await drone.mission.pause_mission()
    print(f"[{DRONE_NAME}] Alert: Runway debris (FOD) identified at waypoint {FOD_WAYPOINT}.")
    print(f"[{DRONE_NAME}] Report sent to ATC, Maintenance, KKIA HQ")
    await asyncio.sleep(5)
    print(f"[{DRONE_NAME}] Resuming runway scan.")
    await drone.mission.start_mission()


async def handle_bird_flock(drone: System):
    """Run the bird-flock deterrence protocol and return to launch on tower order."""
    await drone.mission.pause_mission()
    print(f"[{DRONE_NAME}] Alert: Bird flock detected at waypoint {BIRD_WAYPOINT}. "
          f"Deterrence protocol active.")
    await asyncio.sleep(5)

    print(f"[{DRONE_NAME}] Ultrasound ON, locating wildlife")
    await asyncio.sleep(2)
    print("\n--- RADIO COMM ---")
    print(f"[{DRONE_NAME}] KKIA Tower, this is {DRONE_NAME}. Bird threat neutralized. "
          f"Requesting clearance to resume.")
    await asyncio.sleep(2)
    print(f"[KKIA TOWER] {DRONE_NAME}, this is Tower. Negative on clearance. "
          f"Incoming commercial traffic.")
    await asyncio.sleep(2)
    print("[KKIA TOWER] Abort mission and execute RTL immediately.")
    await asyncio.sleep(1)
    print(f"[{DRONE_NAME}] Copy Tower. Executing RTL at current altitude "
          f"({CRUISE_ALTITUDE_M:.1f} m).\n------------------\n")

    await drone.action.return_to_launch()


# --- Mission entry point -----------------------------------------------------
async def run():
    drone = System()

    print(f"[{DRONE_NAME}] Connecting to {SYSTEM_ADDRESS} ...")
    await drone.connect(system_address=SYSTEM_ADDRESS)
    await wait_for_connection(drone)

    # Concurrent safety monitor (Bootcamp idiom).
    battery_task = asyncio.create_task(battery_checker(drone))

    await drone.action.set_return_to_launch_altitude(RTL_ALTITUDE_M)

    home = await anext(drone.telemetry.home())
    mission_items = build_mission_items(home.latitude_deg, home.longitude_deg)

    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(MissionPlan(mission_items))

    await drone.action.arm()
    await wait_until_armed(drone)

    print(f"[{DRONE_NAME}] Taking off ...")
    await drone.action.set_takeoff_altitude(CRUISE_ALTITUDE_M)
    await drone.action.takeoff()
    await wait_for_takeoff_altitude(drone, CRUISE_ALTITUDE_M - 0.5, CRUISE_ALTITUDE_M + 0.5)

    print(f"[{DRONE_NAME}] Starting runway inspection mission")
    await drone.mission.start_mission()

    handled_fod = False
    handled_birds = False

    async for progress in drone.mission.mission_progress():
        print(f"[{DRONE_NAME}] Mission progress: {progress.current}/{progress.total}")

        if progress.current == FOD_WAYPOINT and not handled_fod:
            handled_fod = True
            await handle_fod(drone)

        elif progress.current == BIRD_WAYPOINT and not handled_birds:
            handled_birds = True
            await handle_bird_flock(drone)
            break

    battery_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())
