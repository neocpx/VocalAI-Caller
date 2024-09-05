from fastapi import FastAPI, Response, WebSocket
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    room: str | None = None
    price: float



app = FastAPI()

@app.get("/status")
async def get(response: Response):
    response.status_code = 200
    return {"status":  "ok"}

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"msg": "Hello WebSocket"})
    await websocket.close()
