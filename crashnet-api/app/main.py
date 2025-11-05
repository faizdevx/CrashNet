# crashnet-api/app/main.py (replace or merge into existing)
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests, os, json, time

app = FastAPI()
ML_URL = os.getenv("ML_URL", "http://crashnet-ml:8001")
WS_URL = os.getenv("WS_URL", "http://crashnet-ws:8002")

class Telemetry(BaseModel):
    device_id: str
    lat: float | None = None
    lon: float | None = None
    speed: float
    accel: float
    gyro: float | None = 0.0
    distance: float | None = None
    ts: float | None = None

@app.post("/telemetry")
def telemetry(t: Telemetry, background: BackgroundTasks):
    payload = t.dict()
    # 1) write to mock cloud (file) - optional
    with open("cloud_ingest.log", "a") as f:
        f.write(json.dumps(payload) + "\n")

    # 2) call ML infer
    try:
        resp = requests.post(f"{ML_URL}/infer", json=payload, timeout=3)
        mlresult = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ML call failed: {e}")

    # 3) build ws payload (always send telemetry for live map)
    ws_payload = {
        "id": payload.get("device_id"),
        "coords": [payload.get("lat") or 0.0, payload.get("lon") or 0.0],
        "accident": bool(mlresult.get("accident", False)),
        "score": float(mlresult.get("score", 0.0)),
        "ts": payload.get("ts") or time.time()
    }

    # 4) send to WS server in background (non-blocking)
    def post_to_ws(p):
        try:
            requests.post(f"{WS_URL}/telemetry", json=p, timeout=1)
        except Exception:
            pass

    background.add_task(post_to_ws, ws_payload)

    # 5) If accident true, also send to /alert (optional)
    if ws_payload["accident"]:
        def post_alert(p):
            try:
                requests.post(f"{WS_URL}/alert", json=p, timeout=1)
            except Exception:
                pass
        background.add_task(post_alert, ws_payload)

    # 6) respond to device
    return {"status": "ok", "ml": mlresult}
