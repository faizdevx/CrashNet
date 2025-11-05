# simulator/full_simulator.py
import requests, time, math, random, threading
import uuid
from datetime import datetime
import numpy as np
import asyncio, websockets, json

API_URL = "http://localhost:8000/telemetry"   # API endpoint
RUN_INTERVAL = 0.5      # seconds between sends per device
NUM_DEVICES = 50        # increase to simulate heavier traffic
CITY_CENTER = (28.6139, 77.2090)  # example: New Delhi lat,lon
CITY_RADIUS_KM = 20     # radius to scatter devices
ACCIDENT_PROB_PER_MIN = 0.02  # low probability a device will have an accident event

async def push_to_ws(event):
    async with websockets.connect("ws://localhost:8002/ws") as ws:
        await ws.send(json.dumps(event))

def random_point_around(center, radius_km):
    lat0, lon0 = center
    # rough conversion: 1 deg latitude ~ 111 km
    r = radius_km / 111.0
    u = random.random()
    v = random.random()
    w = r * math.sqrt(u)
    t = 2 * math.pi * v
    dx = w * math.cos(t)
    dy = w * math.sin(t)
    lat = lat0 + dx
    lon = lon0 + dy / math.cos(math.radians(lat0))
    return lat, lon

def simulate_device(device_id, start_pos):
    lat, lon = start_pos
    speed = max(10.0, random.gauss(40, 8))  # km/h
    accel = 0.0
    last_ts = time.time()
    while True:
        # random wander + occasional slow zone / congestion
        if random.random() < 0.005:
            # slow zone: reduce speed for a short period
            slow_down_for = random.randint(5, 20)
            for _ in range(slow_down_for):
                speed = max(2, speed * random.uniform(0.3, 0.7))
                lat += (random.uniform(-1e-4,1e-4))
                lon += (random.uniform(-1e-4,1e-4))
                send_tick(device_id, lat, lon, speed, accel)
                time.sleep(RUN_INTERVAL)
            speed = max(15, random.gauss(40,8))

        # accident chance (rare)
        accident_now = (random.random() < (ACCIDENT_PROB_PER_MIN * RUN_INTERVAL / 60.0))
        if accident_now:
            # simulate sudden decel: negative accel spike and very low distance
            accel = -6.0 + random.uniform(-1,1)
            speed = max(0, speed + accel)
            distance = random.uniform(0.1, 3.0)  # dangerously low
            send_tick(device_id, lat, lon, speed, accel, distance, accident_flag=True)
            # after accident, device stops for a bit
            for _ in range(random.randint(10, 30)):
                send_tick(device_id, lat, lon, 0.0, 0.0, distance=0.0)
                time.sleep(RUN_INTERVAL)
            # resume with random speed
            speed = max(5., random.gauss(30,10))
            accel = 0.0
            continue

        # normal step
        # small heading change and movement using speed (approx)
        heading = random.uniform(0, 2*math.pi)
        # convert km/h to degrees offset roughly:
        km_per_sec = speed/3600.0
        deg_lat = (km_per_sec / 111.0) * math.cos(heading)
        deg_lon = (km_per_sec / (111.0 * math.cos(math.radians(lat)))) * math.sin(heading)
        lat += deg_lat + random.uniform(-1e-5,1e-5)
        lon += deg_lon + random.uniform(-1e-5,1e-5)
        # small accel noise
        accel = random.gauss(0, 0.6)
        # estimate a fake distance-to-object sensor
        distance = max(0.5, random.expovariate(1/25.0) - (0.05*max(0,40-speed)))
        send_tick(device_id, lat, lon, speed, accel, distance)
        # slight speed drift
        speed += random.gauss(0, 0.8)
        speed = max(0, min(speed, 120))
        time.sleep(RUN_INTERVAL)

def send_tick(device_id, lat, lon, speed, accel, distance=None, accident_flag=False):
    if distance is None:
        distance = max(0.2, random.expovariate(1/25.0))
    payload = {
        "device_id": device_id,
        "lat": lat,
        "lon": lon,
        "speed": float(speed),
        "accel": float(accel),
        "gyro": float(random.gauss(0, 0.2)),
        "distance": float(distance),
        "ts": time.time()
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=2)
        if r.ok:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] sent {device_id} -> ok {r.json()}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] sent {device_id} -> FAIL {r.status_code} {r.text}")
    except Exception as e:
        print("send error", e)
    # send a lightweight WS event after each simulated reading
    # map provided fields: sensor_id -> device_id, accident -> accident_flag
    # compute a simple score heuristic (1.0 if accident else scaled by distance)
    score = 1.0 if accident_flag else float(max(0.0, min(1.0, 1.0 - (distance / 200.0))))
    event = {"id": device_id, "coords": [lat, lon], "accident": accident_flag, "score": score}
    try:
        asyncio.run(push_to_ws(event))
    except Exception as e:
        # fail silently for WS errors to avoid crashing simulator threads
        print("ws push error", e)

def spawn_all(n):
    for i in range(n):
        dev_id = f"sim-{i}-{str(uuid.uuid4())[:6]}"
        start = random_point_around(CITY_CENTER, CITY_RADIUS_KM)
        t = threading.Thread(target=simulate_device, args=(dev_id, start), daemon=True)
        t.start()
        time.sleep(0.05)

if __name__ == "__main__":
    print("spawning devices...")
    spawn_all(NUM_DEVICES)
    # keep main thread alive
    while True:
        time.sleep(10)
