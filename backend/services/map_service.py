from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db
from backend.models import Map


async def list_maps() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM maps ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def create_map(name: str) -> dict:
    map_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO maps (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (map_id, name, now, now),
        )
        # Create root node
        root_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO nodes (id, map_id, parent_id, content, position, created_at, updated_at) VALUES (?, ?, NULL, ?, 0, ?, ?)",
            (root_id, map_id, name, now, now),
        )
        await db.commit()
        return {"id": map_id, "name": name, "created_at": now, "updated_at": now, "root_id": root_id}
    finally:
        await db.close()


async def get_map_with_nodes(map_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM maps WHERE id = ?", (map_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        map_data = dict(row)

        cursor = await db.execute(
            "SELECT * FROM nodes WHERE map_id = ? ORDER BY position",
            (map_id,),
        )
        nodes = [dict(r) for r in await cursor.fetchall()]
        for n in nodes:
            n["collapsed"] = bool(n["collapsed"])
        map_data["nodes"] = nodes
        return map_data
    finally:
        await db.close()


async def delete_map(map_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM maps WHERE id = ?", (map_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
