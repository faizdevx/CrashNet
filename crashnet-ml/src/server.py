# crashnet-ml/src/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, os, threading, time
import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler

app = FastAPI(title="CrashNet-ML-Online")
MODEL_PATH = "models/model.pkl"
SCALER_PATH = "models/scaler.pkl"
LOCK = threading.Lock()

# create model scaffold if not exists
if not os.path.exists("models"):
    os.makedirs("models", exist_ok=True)

# incremental model: SGDClassifier supports partial_fit
if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
    clf = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
else:
    print("⚙️  No model found — creating new scaler + classifier")
    os.makedirs("models", exist_ok=True)
    scaler = StandardScaler()
    X_init = np.array([[0,0,0,0]])
    scaler.fit(X_init)
    clf = SGDClassifier(max_iter=1000, tol=1e-3)
    clf.partial_fit(scaler.transform(X_init), [0], classes=np.array([0,1]))
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)


# background saver
def _periodic_save():
    while True:
        time.sleep(10)
        with LOCK:
            joblib.dump(clf, MODEL_PATH)
            joblib.dump(scaler, SCALER_PATH)
_thread = threading.Thread(target=_periodic_save, daemon=True)
_thread.start()

class Telemetry(BaseModel):
    device_id: str | None = None
    speed: float
    accel: float
    gyro: float
    distance: float
    ts: float | None = None

class TrainSample(BaseModel):
    # labelled example to use for incremental training
    speed: float
    accel: float
    gyro: float
    distance: float
    label: int  # 0 normal, 1 accident

@app.get("/health")
def health():
    return {"status":"ok", "model_loaded": os.path.exists(MODEL_PATH)}

@app.post("/infer")
def infer(t: Telemetry):
    X = pd.DataFrame([dict(speed=t.speed,accel=t.accel,gyro=t.gyro,distance=t.distance)])
    with LOCK:
        Xs = scaler.transform(X)
        pred = int(clf.predict(Xs)[0])
        prob = float(clf.decision_function(Xs)[0]) if hasattr(clf, "decision_function") else 0.0
    return {"accident": bool(pred), "score": prob}

@app.post("/train")
def train(sample: TrainSample):
    X = np.array([[sample.speed, sample.accel, sample.gyro, sample.distance]])
    with LOCK:
        try:
            Xs = scaler.transform(X)
        except Exception:
            scaler.fit(X)
            Xs = scaler.transform(X)
        clf.partial_fit(Xs, [sample.label])
        joblib.dump(clf, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
    return {"status": "trained"}


# simple helper to allow trainer to reset model if needed
@app.post("/reset")
def reset():
    global clf, scaler
    with LOCK:
        scaler = StandardScaler()
        scaler.fit(np.array([[0,0,0,0]]))
        clf = SGDClassifier(max_iter=1000, tol=1e-3)
        clf.partial_fit(scaler.transform(np.array([[0,0,0,0]])), [0], classes=np.array([0,1]))
        joblib.dump(clf, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
    return {"status":"reset"}
