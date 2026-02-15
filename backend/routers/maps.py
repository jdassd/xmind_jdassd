from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import map_service

router = APIRouter(prefix="/api/maps", tags=["maps"])


class CreateMapRequest(BaseModel):
    name: str


@router.get("")
async def list_maps():
    return await map_service.list_maps()


@router.post("", status_code=201)
async def create_map(req: CreateMapRequest):
    return await map_service.create_map(req.name)


@router.get("/{map_id}")
async def get_map(map_id: str):
    result = await map_service.get_map_with_nodes(map_id)
    if not result:
        raise HTTPException(status_code=404, detail="Map not found")
    return result


@router.get("/{map_id}/sync")
async def sync_map(map_id: str, since: int = 0):
    result = await map_service.get_sync(map_id, since)
    if result is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return result


@router.delete("/{map_id}", status_code=204)
async def delete_map(map_id: str):
    deleted = await map_service.delete_map(map_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Map not found")
