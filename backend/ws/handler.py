from __future__ import annotations

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.auth import decode_token
from backend.services import node_service, permission_service
from backend.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/{map_id}")
async def websocket_endpoint(ws: WebSocket, map_id: str, token: str = Query(default="")):
    # Authenticate via query param token
    user = None
    if token:
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user = {"id": payload["sub"], "username": payload.get("username", "")}

    if not user:
        await ws.close(code=4001, reason="Authentication required")
        return

    if not await permission_service.check_map_access(user["id"], map_id, "view"):
        await ws.close(code=4003, reason="Access denied")
        return

    client_id = str(uuid.uuid4())
    room = await manager.connect(map_id, client_id, ws)

    # Send client its own id, current version and current locks
    locks = await node_service.get_locks_for_map(map_id)
    await ws.send_json({
        "type": "connected",
        "client_id": client_id,
        "version": room.version,
        "user_id": user["id"],
        "locks": locks,
    })

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")
            payload = data.get("data", {})

            result = None

            if msg_type.startswith("node:"):
                if not await permission_service.check_map_access(user["id"], map_id, "edit"):
                    await ws.send_json({"type": "error", "message": "No edit access"})
                    continue

            if msg_type == "node:create":
                parent_id = payload.get("parent_id")
                if not parent_id:
                    await ws.send_json({"type": "error", "message": "Missing parent_id"})
                    continue
                result = await node_service.create_node(
                    map_id=map_id,
                    parent_id=parent_id,
                    content=payload.get("content", ""),
                    position=payload.get("position", 0),
                    style=payload.get("style", "{}"),
                    node_id=payload.get("id"),
                    user_id=user["id"],
                    username=user["username"],
                )
                if result is None:
                    await ws.send_json({"type": "error", "message": "Parent node not found in this map"})
                    continue
            elif msg_type == "node:update":
                node_id = payload.get("id")
                if not node_id:
                    await ws.send_json({"type": "error", "message": "Missing node id"})
                    continue
                result = await node_service.update_node(
                    map_id=map_id,
                    node_id=node_id,
                    changes=payload.get("changes", {}),
                    user_id=user["id"],
                    username=user["username"],
                )
                if result is None:
                    await ws.send_json({"type": "error", "message": "Node not found"})
                    continue
            elif msg_type == "node:delete":
                node_id = payload.get("id")
                if not node_id:
                    await ws.send_json({"type": "error", "message": "Missing node id"})
                    continue
                deleted = await node_service.delete_node(map_id, node_id, user_id=user["id"], username=user["username"])
                if deleted is None:
                    await ws.send_json({"type": "error", "message": "Node not found"})
                    continue
                result = {"id": node_id}
            elif msg_type == "node:lock":
                node_id = payload.get("id")
                if not node_id:
                    await ws.send_json({"type": "error", "message": "Missing node id"})
                    continue
                lock = await node_service.acquire_lock(node_id, map_id, user["id"], user["username"])
                if lock is None:
                    await ws.send_json({"type": "error", "message": "Node is locked by another user"})
                    continue
                # Broadcast lock status to everyone including sender
                await manager.broadcast(
                    room,
                    {
                        "type": "node:lock",
                        "data": lock,
                        "client_id": client_id,
                    },
                )
                continue # Skip standard ack/broadcast
            elif msg_type == "node:unlock":
                node_id = payload.get("id")
                if not node_id:
                    await ws.send_json({"type": "error", "message": "Missing node id"})
                    continue
                await node_service.release_lock(node_id, map_id, user["id"])
                # Broadcast unlock status
                await manager.broadcast(
                    room,
                    {
                        "type": "node:unlock",
                        "data": {"node_id": node_id, "user_id": user["id"]},
                        "client_id": client_id,
                    },
                )
                continue # Skip standard ack/broadcast
            elif msg_type == "node:move":
                node_id = payload.get("id")
                parent_id = payload.get("parent_id")
                if not node_id or not parent_id:
                    await ws.send_json({"type": "error", "message": "Missing node id or parent_id"})
                    continue
                result = await node_service.move_node(
                    map_id=map_id,
                    node_id=node_id,
                    new_parent_id=parent_id,
                    position=payload.get("position", 0),
                )
                if result is None:
                    await ws.send_json({"type": "error", "message": "Node not found"})
                    continue
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
