from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.auth import get_current_user
from backend.services import map_service, permission_service, export_service

router = APIRouter(prefix="/api/maps", tags=["export"])

EXPORT_FORMATS = {
    "docx": {
        "fn": export_service.export_docx,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "ext": ".docx",
    },
    "xlsx": {
        "fn": export_service.export_xlsx,
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ext": ".xlsx",
    },
    "xmind": {
        "fn": export_service.export_xmind,
        "content_type": "application/zip",
        "ext": ".xmind",
    },
}


@router.get("/{map_id}/export/{format}")
async def export_map(map_id: str, format: str, user: dict = Depends(get_current_user)):
    if format not in EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}. Use: {', '.join(EXPORT_FORMATS)}")

    if not await permission_service.check_map_access(user["id"], map_id, "view"):
        raise HTTPException(status_code=403, detail="Access denied")

    map_data = await map_service.get_map_with_nodes(map_id)
    if not map_data:
        raise HTTPException(status_code=404, detail="Map not found")

    fmt = EXPORT_FORMATS[format]
    buf = fmt["fn"](map_data["name"], map_data["nodes"])
    filename = f"{map_data['name']}{fmt['ext']}"

    return StreamingResponse(
        buf,
        media_type=fmt["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
