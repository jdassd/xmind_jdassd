from __future__ import annotations

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services import node_service
from backend.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/{map_id}")
async def websocket_endpoint(ws: WebSocket, map_id: str):
    client_id = str(uuid.uuid4())
    room = await manager.connect(map_id, client_id, ws)

    # Send client its own id and current version
    await ws.send_json({
        "type": "connected",
        "client_id": client_id,
        "version": room.version,
    })

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")
            payload = data.get("data", {})

            result = None

            if msg_type == "node:create":
                result = await node_service.create_node(
                    map_id=map_id,
                    parent_id=payload["parent_id"],
                    content=payload.get("content", ""),
                    position=payload.get("position", 0),
                    style=payload.get("style", "{}"),
                    node_id=payload.get("id"),
                )
            elif msg_type == "node:update":
                result = await node_service.update_node(
                    node_id=payload["id"],
                    changes=payload.get("changes", {}),
                )
            elif msg_type == "node:delete":
                await node_service.delete_node(payload["id"])
                result = {"id": payload["id"]}
            elif msg_type == "node:move":
                result = await node_service.move_node(
                    node_id=payload["id"],
                    new_parent_id=payload["parent_id"],
                    position=payload.get("position", 0),
                )
            else:
                await ws.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})
                continue

            version = manager.next_version(room)

            # Acknowledge to sender
            await ws.send_json({
                "type": "ack",
                "original_type": msg_type,
                "data": result,
                "version": version,
            })

            # Broadcast to others
            await manager.broadcast(
                room,
                {
                    "type": msg_type,
                    "data": result,
                    "version": version,
                    "client_id": client_id,
                },
                exclude_client=client_id,
            )

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(map_id, client_id)
        # Notify others
        room = manager.get_room(map_id)
        if room:
            await manager.broadcast(room, {
                "type": "peer:disconnect",
                "client_id": client_id,
            })
