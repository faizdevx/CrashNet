from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
import asyncio
import json

app = FastAPI(title="CrashNet-WS")
clients = set()

@app.get("/")
def index():
    return HTMLResponse("""
    <html><body>
    <h3>CrashNet WS server</h3>
    <p>Open console or use ws client at ws://localhost:8002/ws</p>
    </body></html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive; ignore messages
    except WebSocketDisconnect:
        clients.remove(websocket)

async def _broadcast(message: str):
    to_remove = []
    for ws in list(clients):
        try:
            await ws.send_text(message)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        clients.discard(ws)

@app.post("/alert")
async def alert(req: Request, background: BackgroundTasks):
    payload = await req.json()
    message = json.dumps(payload)
    background.add_task(_broadcast, message)
    return {"status":"broadcasted", "clients": len(clients)}
