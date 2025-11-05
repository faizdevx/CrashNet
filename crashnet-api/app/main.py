from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI(title="CrashNet-API")
ML_URL = os.getenv("ML_URL", "http://localhost:8001")
WS_URL = os.getenv("WS_URL", "http://localhost:8002")

class Telemetry(BaseModel):
    device_id: str
    speed: float
    accel: float
    gyro: float
    distance: float
    ts: float | None = None

@app.get("/health")
def health():
    return {"status":"ok", "ml": ML_URL, "ws": WS_URL}

@app.post("/telemetry")
def telemetry(t: Telemetry):
    # forward to ML inference
    try:
        resp = requests.post(f"{ML_URL}/infer", json={
            "device_id": t.device_id,
            "speed": t.speed,
            "accel": t.accel,
            "gyro": t.gyro,
            "distance": t.distance
        }, timeout=5)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML service call failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"ML returned {resp.status_code}: {resp.text}")

    result = resp.json()
    # if accident detected -> notify websocket server (alerts)
    if result.get("accident"):
        try:
            requests.post(f"{WS_URL}/alert", json={"device_id": t.device_id, "type": "accident", "details": result}, timeout=3)
        except Exception:
            # non-fatal: log in real project
            pass

    return {"status":"ok", "ml": result}
