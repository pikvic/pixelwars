from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

pixels = [{"id": f'x{x}y{y}', "color": "#fa0afc"} for y in range(10) for x in range(10)]

templates = Jinja2Templates(directory='templates')

@app.get("/")
async def get(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse('index.html', context={"request": request, "pixels": pixels})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            id, color = data.split()
            for pixel in pixels:
                if pixel["id"] == id:
                    pixel["color"] = color
            await manager.broadcast(data)

    except WebSocketDisconnect:

        manager.disconnect(websocket)

        await manager.broadcast(f"Client #{client_id} left the chat")
