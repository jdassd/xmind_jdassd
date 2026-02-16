from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.services import node_service, permission_service

router = APIRouter(prefix="/api/maps/{map_id}/nodes", tags=["nodes"])


class CreateNodeRequest(BaseModel):
    parent_id: str
    content: str = ""
    position: int = 0
    style: str = "{}"
    id: Optional[str] = None


class UpdateNodeRequest(BaseModel):
    content: Optional[str] = None
    position: Optional[int] = None
    style: Optional[str] = None
    collapsed: Optional[bool] = None
    parent_id: Optional[str] = None


@router.post("", status_code=201)
async def create_node(map_id: str, req: CreateNodeRequest, user: dict = Depends(get_current_user)):
    if not await permission_service.check_map_access(user["id"], map_id, "edit"):
        raise HTTPException(status_code=403, detail="No edit access")
    return await node_service.create_node(
        map_id=map_id,
        parent_id=req.parent_id,
        content=req.content,
        position=req.position,
        style=req.style,
        node_id=req.id,
        user_id=user["id"],
        username=user.get("username", ""),
    )


@router.put("/{node_id}")
async def update_node(map_id: str, node_id: str, req: UpdateNodeRequest, user: dict = Depends(get_current_user)):
    if not await permission_service.check_map_access(user["id"], map_id, "edit"):
        raise HTTPException(status_code=403, detail="No edit access")
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    result = await node_service.update_node(node_id, changes, user_id=user["id"], username=user.get("username", ""))
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.delete("/{node_id}")
async def delete_node(map_id: str, node_id: str, user: dict = Depends(get_current_user)):
    if not await permission_service.check_map_access(user["id"], map_id, "edit"):
        raise HTTPException(status_code=403, detail="No edit access")
    result = await node_service.delete_node(node_id, user_id=user["id"], username=user.get("username", ""))
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.get("/{node_id}/history")
async def get_node_history(map_id: str, node_id: str, user: dict = Depends(get_current_user)):
    if not await permission_service.check_map_access(user["id"], map_id, "view"):
        raise HTTPException(status_code=403, detail="Access denied")
    return await node_service.get_node_history(node_id)


@router.post("/{node_id}/history/{history_id}/rollback")
async def rollback_node_history(
    map_id: str, node_id: str, history_id: int, user: dict = Depends(get_current_user)
):
    if not await permission_service.check_map_access(user["id"], map_id, "edit"):
        raise HTTPException(status_code=403, detail="No edit access")
    result = await node_service.rollback_to_history(history_id, user["id"], user.get("username", ""))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{node_id}/lock")
async def lock_node(map_id: str, node_id: str, user: dict = Depends(get_current_user)):
    if not await permission_service.check_map_access(user["id"], map_id, "edit"):
        raise HTTPException(status_code=403, detail="No edit access")
    lock = await node_service.acquire_lock(node_id, map_id, user["id"], user.get("username", ""))
    if lock is None:
        raise HTTPException(status_code=409, detail="Node is locked by another user")
    return lock


@router.delete("/{node_id}/lock")
async def unlock_node(map_id: str, node_id: str, user: dict = Depends(get_current_user)):
    await node_service.release_lock(node_id, user["id"])
    return {"status": "ok"}
