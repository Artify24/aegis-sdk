from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter(prefix="/api/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        # Maps project_id -> list of connected WebSocket objects
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast_to_project(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            for connection in list(self.active_connections[project_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(project_id, connection)

manager = ConnectionManager()

@router.websocket("/project/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data) if data else {}
            if payload.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
    except Exception:
        manager.disconnect(project_id, websocket)
