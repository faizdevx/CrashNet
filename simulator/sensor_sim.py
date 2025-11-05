# simulator/sensor_sim.py
import requests, time, random
import numpy as np

API_URL = "http://localhost:8000/telemetry"  # when running locally
DEVICE_ID = "sim-device-1"

def make_telemetry():
    speed = float(np.random.normal(40, 12))
    accel = float(np.random.normal(0, 1.5))
    gyro = float(np.random.normal(0, 0.5))
    distance = float(np.random.exponential(25))
    return dict(device_id=DEVICE_ID, speed=speed, accel=accel, gyro=gyro, distance=distance, ts=time.time())

if __name__ == "__main__":
    while True:
        t = make_telemetry()
        try:
            r = requests.post(API_URL, json=t, timeout=2)
            print("sent", t, "->", r.status_code, r.json() if r.ok else r.text)
        except Exception as e:
            print("send failed", e)
        time.sleep(0.5)
