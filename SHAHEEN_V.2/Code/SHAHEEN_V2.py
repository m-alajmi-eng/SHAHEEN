import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

async def run():
    drone = System() 

   
    await drone.connect(system_address="udp://:14540")
    print("SHAHEEN-1 connected")

  
    await drone.action.set_return_to_launch_altitude(4.0)

    mission_items = []

  
    home = await anext(drone.telemetry.home())
    ab_lat = home.latitude_deg
    ab_lon = home.longitude_deg

    def get_lat_lon(x, y):
        lat_offset = y * 8.983e-6
        lon_offset = x * 1.327e-5
        return ab_lat + lat_offset, ab_lon + lon_offset

   
    points_xy_alt = [
        (-45.53, -6.59, 4.0),  # WP 1
        (-40.00, -6.09, 4.0),  # WP 2: موقع اكتشاف القمع (FOD)
        (-37.50, -5.86, 4.0),  # WP 3
        (-35.56, -5.19, 4.0),  # WP 4
        (-30.00, -4.68, 4.0),  # WP 5
        (-15.00, -3.33, 4.0),  # WP 6
        ( 0.00,  -1.97, 4.0),  # WP 7
        (15.00,  -0.61, 4.0),  # WP 8
        (27.48,   0.00, 4.0),  # WP 9
        (-13.50,-24.00, 4.0),  # WP 10: موقع الطيور
    ]

    for x, y, alt in points_xy_alt:
        target_lat, target_lon = get_lat_lon(x, y)
        mission_items.append(MissionItem(
            target_lat, target_lon, 
            alt,  
            7,  
            True, 
            float('nan'), float('nan'), MissionItem.CameraAction.NONE, 
            float('nan'), float('nan'), 
            1.0, 
            float('nan'), float('nan'), MissionItem.VehicleAction.NONE
        ))

    await drone.mission.set_return_to_launch_after_mission(True)
    mission_plan = MissionPlan(mission_items)

    await drone.mission.upload_mission(mission_plan)

    await drone.action.arm()

    async for armed in drone.telemetry.armed():
        if armed:
            print("SHAHEEN-1 armed")
            break

    await drone.mission.start_mission()

    handled_cone = False
    handled_birds = False

    async for mission_progress in drone.mission.mission_progress():
        wp = mission_progress.current
        total = mission_progress.total
        print(f"Mission progress: {wp}/{total}")

    
        if wp == 2 and not handled_cone:
            handled_cone = True
            await drone.mission.pause_mission()
            print("[SHAHEEN-1] Alert: Runway debris (FOD) identified at waypoint 2.")
            print("[SHAHEEN-1] Report sent to ATC,Maintence,KKIA HQ")
            await asyncio.sleep(5)
            print("[SHAHEEN-1] Resuming runway scan.")
            await drone.mission.start_mission()

       
        elif wp == 10 and not handled_birds:
            handled_birds = True
            await drone.mission.pause_mission()
            print("[SHAHEEN-1] Alert: Bird flock detected at waypoint 10. Deterrence protocol active.")
            await asyncio.sleep(5)
            
           
            print("[SHAHEEN-1] Ultrasound  ON, Locating wildlife ")
            await asyncio.sleep(2)
            print("\n--- RADIO COMM ---")
            print("[SHAHEEN-1] KKIA Tower, this is SHAHEEN-1. Bird threat neutralized. Requesting clearance to resume.")
            await asyncio.sleep(2)
            print("[KKIA TOWER] SHAHEEN-1, this is Tower. Negative on clearance. Incoming commercial traffic.")
            await asyncio.sleep(2)
            print("[KKIA TOWER] Abort mission and execute RTL immediately.")
            await asyncio.sleep(1)
            print("[SHAHEEN-1] Copy Tower. Executing RTL at current altitude (4.0m).\n------------------\n")
            
            await drone.action.return_to_launch()
            break 

if __name__ == "__main__":
    asyncio.run(run())
