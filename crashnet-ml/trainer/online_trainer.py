# crashnet-ml/trainer/online_trainer.py
import requests, time, random
import numpy as np

ML_TRAIN_URL = "http://localhost:8001/train"  # local API
SLEEP = 0.25

def make_labelled():
    # generate one labelled sample
    speed = float(np.random.normal(40, 12))
    accel = float(np.random.normal(0, 1.5))
    gyro = float(np.random.normal(0, 0.5))
    distance = float(np.random.exponential(25))
    # create label rule - same as infer rule: high negative accel + small distance -> accident
    label = int((accel < -3) and (distance < 5))
    return dict(speed=speed, accel=accel, gyro=gyro, distance=distance, label=label)

if __name__ == "__main__":
    while True:
        sample = make_labelled()
        try:
            r = requests.post(ML_TRAIN_URL, json=sample, timeout=2)
            if r.ok:
                print("trained", sample, r.text)
            else:
                print("train failure", r.status_code, r.text)
        except Exception as e:
            print("train failed", e)
        time.sleep(SLEEP)
