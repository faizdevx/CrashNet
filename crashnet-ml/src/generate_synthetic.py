import numpy as np
import pandas as pd
import os

# ensure directories under /app (WORKDIR) are used
os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)

def make(n=2000):
    speed = np.random.normal(40, 12, n)
    accel = np.random.normal(0, 1.5, n)
    gyro = np.random.normal(0, 0.5, n)
    distance = np.random.exponential(25, n)
    label = ((accel < -3) & (distance < 5)).astype(int)
    df = pd.DataFrame(dict(speed=speed, accel=accel, gyro=gyro, distance=distance, label=label))
    df.to_csv("data/synthetic_example.csv", index=False)
    print("Saved data/synthetic_example.csv")

if __name__ == "__main__":
    make()
