from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/nodes", tags=["nodes"])

# Node CRUD is handled via WebSocket for real-time sync.
# This router is reserved for potential future REST endpoints.
