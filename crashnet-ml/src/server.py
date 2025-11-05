from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="CrashNet-ML")
MODEL_PATH = "/app/models/model.pkl"

# Load model if exists; else start without and warn
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)

class Telemetry(BaseModel):
    device_id: str | None = None
    speed: float
    accel: float
    gyro: float
    distance: float

@app.get("/health")
def health():
    return {"status":"ok", "model_loaded": bool(model)}

@app.post("/infer")
def infer(t: Telemetry):
    global model
    if model is None:
        return {"error":"model not found"}
    row = pd.DataFrame([dict(speed=t.speed,accel=t.accel,gyro=t.gyro,distance=t.distance)])
    pred = int(model.predict(row)[0])
    return {"accident": bool(pred)}
