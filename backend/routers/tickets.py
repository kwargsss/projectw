import json
import asyncio

from typing import List
from fastapi import APIRouter, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, redis_client
from dependencies import verify_support_access, get_user_from_token_ws

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

class TicketConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ticket_id: str):
        await websocket.accept()
        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = []
        self.active_connections[ticket_id].append(websocket)

    def disconnect(self, websocket: WebSocket, ticket_id: str):
        if ticket_id in self.active_connections and websocket in self.active_connections[ticket_id]:
            self.active_connections[ticket_id].remove(websocket)

ticket_manager = TicketConnectionManager()

@router.get("")
async def get_all_tickets(request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)

    ticket_keys = []
    async for key in redis_client.scan_iter("ticket:*"):
        ticket_keys.append(key)
        
    tickets = []
    for key in ticket_keys:
        try:
            if await redis_client.type(key) in [b'hash', 'hash']:
                data = await redis_client.hgetall(key)
                if data: tickets.append(data)
        except Exception: 
            continue

    tickets.sort(key=lambda x: int(x.get("created_at", 0)) if str(x.get("created_at", "")).isdigit() else 0, reverse=True)
    return {"status": "ok", "data": tickets}

@router.get("/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)
    try:
        messages = await redis_client.lrange(f"ticket_messages:{ticket_id}", 0, -1)
        parsed_messages = [json.loads(m) for m in messages]
        return {"status": "ok", "data": parsed_messages}
    except Exception:
        return {"status": "error", "data": []}

@router.post("/{ticket_id}/action")
async def manage_ticket_action(ticket_id: str, action: str, request: Request, db: AsyncSession = Depends(get_db)):
    user_info = await verify_support_access(request, db)

    if action == "force_delete":
        await redis_client.delete(f"ticket:{ticket_id}")
        await redis_client.delete(f"transcript:{ticket_id}")
        await redis_client.delete(f"ticket_messages:{ticket_id}")
        return {"status": "ok", "message": "Архив безвозвратно удален"}
    
    payload = { "action": action, "ticket_id": ticket_id, "admin_id": user_info["sub"], "admin_name": user_info["username"] }
    await redis_client.publish("web_ticket_controls", json.dumps(payload))
    return {"status": "ok", "message": f"Команда {action} отправлена"}

@router.get("/{ticket_id}/transcript")
async def get_ticket_transcript(ticket_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    await verify_support_access(request, db)
    transcript = await redis_client.get(f"transcript:{ticket_id}")
    if transcript:
        html_content = transcript.decode('utf-8') if isinstance(transcript, bytes) else transcript
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<div style='color: white; text-align: center; padding-top: 50px;'><h2>Транскрипт не найден</h2></div>", status_code=404)

@router.post("/{ticket_id}/message")
async def send_ticket_message(ticket_id: str, request: Request, payload: dict, db: AsyncSession = Depends(get_db)):
    user_info = await verify_support_access(request, db)
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_info['sub']}/{user_info['avatar']}.png" if user_info.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
    
    msg_data = { "action": "send_message", "ticket_id": ticket_id, "content": payload.get("content"), "author_name": user_info["username"], "author_avatar": avatar_url }
    await redis_client.publish("web_ticket_controls", json.dumps(msg_data))
    return {"status": "ok"}

@router.websocket("/ws/{ticket_id}")
async def websocket_ticket_chat(websocket: WebSocket, ticket_id: str):
    user_info = await get_user_from_token_ws(websocket)
    if not user_info:
        return 

    await ticket_manager.connect(websocket, ticket_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"ticket_chat:{ticket_id}")

    async def redis_reader():
        try:
            async for message in pubsub.listen():
                if message and message["type"] == "message":
                    await websocket.send_json(json.loads(message["data"]))
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def ws_reader():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    task_redis = asyncio.create_task(redis_reader())
    task_ws = asyncio.create_task(ws_reader())

    try:
        done, pending = await asyncio.wait(
            [task_redis, task_ws], 
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        ticket_manager.disconnect(websocket, ticket_id)
        await pubsub.unsubscribe(f"ticket_chat:{ticket_id}")
        await pubsub.close()