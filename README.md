# 🚦 CrashNet – AI-Powered IoT Road Safety Network

### *Real-time Accident Detection • Traffic Congestion Prediction • Helmet Compliance Tracking*

---

## 🧭 Overview

**CrashNet** is an end-to-end **AI + IoT platform** that connects edge IoT sensors, a cloud inference engine, and a real-time government dashboard — predicting accidents, optimizing traffic flow, and enforcing helmet & safety rules.

> The system continuously ingests live telemetry (speed, acceleration, gyro, distance, GPS) from simulated sensors, runs ML inference in real-time, and streams results to a live dashboard through WebSockets.

---

## 🧩 Architecture

    ┌──────────────────────────────────────────────┐
    │               IoT Sensor Simulator           │
    │  (Python → sends JSON telemetry)             │
    └──────────────────────────────────────────────┘
                         │  HTTP / JSON
                         ▼
    ┌──────────────────────────────────────────────┐
    │           crashnet-api (FastAPI)             │
    │  - Receives telemetry                        │
    │  - Calls crashnet-ml for inference           │
    │  - Broadcasts to crashnet-ws (WebSocket)     │
    └──────────────────────────────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────────┐
    │           crashnet-ml (FastAPI)              │
    │  - Loads & retrains model (model.pkl)        │
    │  - /health /infer /train endpoints           │
    └──────────────────────────────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────────┐
    │           crashnet-ws (FastAPI + WS)         │
    │  - Broadcasts telemetry & alerts via WS      │
    │  - Listened by dashboard clients             │
    └──────────────────────────────────────────────┘
                         │
                         ▼
    ┌──────────────────────────────────────────────┐
    │        crashnet-web (React + Leaflet)        │
    │  - Live map, heatmap, charts & analytics     │
    └──────────────────────────────────────────────┘

---

## 🧠 Features

- 🚗 Accident Detection – ML model detects crash patterns from IMU telemetry.  
- 🌆 Traffic Congestion Prediction – Simulated road congestion based on aggregated flow.  
- 🪖 Helmet Compliance Tracking – Placeholder model for helmet-rule enforcement.  
- 🛰️ Live IoT Telemetry Stream – 50+ simulated vehicles streaming at 1 Hz.  
- ⚙️ Online Model Training – Incremental learning via `online_trainer.py`.  
- 📡 WebSocket Dashboard – Realtime updates on map & analytics cards.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.10) |
| Machine Learning | scikit-learn, joblib, NumPy |
| Streaming | FastAPI WebSocket, requests |
| Frontend | React + Leaflet + Recharts |
| Containerization | Docker & Docker Compose |
| Simulator | Python synthetic telemetry generator |

---

## ⚙️ Project Setup

### 1. Clone & Build

```bash
git clone https://github.com/faizdevx/CrashNet.git
cd CrashNet
docker compose build
```

### 2. Run all services

```bash
docker compose up -d
```

Expected running services:

| Service       | Port | Description                         |
|---------------|------|-------------------------------------|
| crashnet-ml   | 8001 | ML inference & model server         |
| crashnet-api  | 8000 | Main API gateway                    |
| crashnet-ws   | 8002 | WebSocket broadcast server          |
| crashnet-web  | 3000 | React dashboard (manual start)      |

Check status:

```bash
docker compose ps
```

### 3. Verify each component

ML health:

```bash
curl http://localhost:8001/health
```

API docs:

```bash
curl http://localhost:8000/docs
```

WS test (PowerShell):

```powershell
Invoke-RestMethod -Uri "http://localhost:8002/telemetry" -Method POST -ContentType "application/json" -Body '{"id":"test1","coords":[26.85,80.95],"accident":false,"score":1.2}'
```

### 4. Start the Simulator

```bash
python simulator/full_simulator.py
```

Simulates 50 virtual vehicles sending speed, acceleration, gyro, and GPS data to the API → ML → WS → dashboard.

Output example:

```text
[03:39:43] sent sim-14 → ok {'status':'ok','ml':{'accident':False,'score':-10.0}}
```

### 5. (Optional) Online Model Trainer

```bash
python crashnet-ml/trainer/online_trainer.py
```

Continuously retrains model weights on incoming synthetic batches.

### 6. Start the Frontend Dashboard

```bash
cd crashnet-web
npm install
npm start
```

Open http://localhost:3000

You’ll see:
- Live map of vehicle telemetry
- Real-time accident markers & traffic congestion zones
- Line chart of model confidence over time
- System metrics: active vehicles, recent alerts, SOS response time

---

## 🧪 Local Test Commands

Post synthetic telemetry (PowerShell):

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/telemetry" -Method POST -ContentType "application/json" -Body '{"device_id":"car-42","lat":26.85,"lon":80.95,"speed":75,"accel":5.3,"gyro":0.8,"distance":20}'
```

Check ML inference directly (PowerShell):

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/infer" -Method POST -ContentType "application/json" -Body '{"speed":75,"accel":5.3,"gyro":0.8,"distance":20}'
```

---

## 🧰 Folder Structure

```
CrashNet/
│
├── crashnet-ml/
│   ├── src/
│   │   ├── server.py
│   │   ├── generate_synthetic.py
│   │   └── train.py
│   └── trainer/online_trainer.py
│
├── crashnet-api/
│   └── app/main.py
│
├── crashnet-ws/
│   └── src/app.py
│
├── crashnet-web/
│   ├── src/components/MapDashboard.jsx
│   └── package.json
│
├── simulator/
│   ├── sensor_sim.py
│   └── full_simulator.py
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Deploying to Docker Hub

```bash
docker login -u faizdevx
docker tag crashnet-crashnet-ml faizdevx/crashnet-ml:latest
docker push faizdevx/crashnet-ml:latest
```

Repeat for crashnet-api and crashnet-ws.

---

## 🧩 API Summary

| Endpoint     | Service | Method | Description                    |
|--------------|---------|--------|--------------------------------|
| /health      | ML      | GET    | Check model loaded             |
| /infer       | ML      | POST   | Predict accident likelihood    |
| /train       | ML      | POST   | Retrain model                  |
| /telemetry   | API     | POST   | Receive sensor data            |
| /alert       | WS      | POST   | Broadcast alerts to clients    |
| /telemetry   | WS      | POST   | Broadcast telemetry to clients |
| /ws          | WS      | WS     | Realtime client updates        |

Example WebSocket payload:

```json
{
  "id": "veh-7",
  "coords": [26.85, 80.95],
  "accident": false,
  "score": -10.0,
  "ts": 1730858400
}
```

---

## 🧠 Future Vision

- Edge deployment on IoT microcontrollers  
- Real-time traffic policy feedback to authorities  
- Citizen mobile app integration for crash reporting  
- Secure V2X communication layer  
- Federated ML training with regional models

---

## 🏆 Credits

Developed by: Faizal (@faizdevx)  
Inspiration: Safer Roads • Smarter Cities • Connected Future

---

## 🧭 Quick Start TL;DR

```bash
# build + start everything
docker compose up -d --build

# run simulator
python simulator/full_simulator.py

# open dashboard
http://localhost:3000
```

---

Would you like a second version that adds:
- Shields.io badges (build, docker pulls, license, tech stack)  
- Preview screenshots for the dashboard  
- A dark "Government Dashboard" hero banner on top?