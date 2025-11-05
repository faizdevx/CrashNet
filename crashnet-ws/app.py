from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

clients: set[WebSocket] = set()
clients_lock = asyncio.Lock()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    async with clients_lock:
        clients.add(ws)
    try:
        while True:
            # keep connection open
            await ws.receive_text()
    except Exception:
        pass
    finally:
        async with clients_lock:
            if ws in clients:
                clients.remove(ws)

async def broadcast_json(payload: dict):
    async with clients_lock:
        remove = []
        for ws in list(clients):
            try:
                await ws.send_json(payload)
            except Exception:
                remove.append(ws)
        for r in remove:
            clients.discard(r)

# HTTP endpoint used by API to post realtime events
@app.post("/alert")
async def alert(req: Request):
    payload = await req.json()
    # payload must be JSON containing at least { id, coords:[lat,lon], accident, score, ts }
    asyncio.create_task(broadcast_json(payload))
    return {"status": "ok"}

# optional: endpoint to accept telemetry events (not just accidents)
@app.post("/telemetry")
async def telemetry(req: Request):
    payload = await req.json()
    asyncio.create_task(broadcast_json(payload))
    return {"status": "ok"}
