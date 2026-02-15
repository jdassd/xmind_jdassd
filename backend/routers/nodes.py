from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import node_service

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
async def create_node(map_id: str, req: CreateNodeRequest):
    return await node_service.create_node(
        map_id=map_id,
        parent_id=req.parent_id,
        content=req.content,
        position=req.position,
        style=req.style,
        node_id=req.id,
    )


@router.put("/{node_id}")
async def update_node(map_id: str, node_id: str, req: UpdateNodeRequest):
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    result = await node_service.update_node(node_id, changes)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result


@router.delete("/{node_id}")
async def delete_node(map_id: str, node_id: str):
    result = await node_service.delete_node(node_id)
    if not result:
        raise HTTPException(status_code=404, detail="Node not found")
    return result
