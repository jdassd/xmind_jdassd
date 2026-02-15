from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db


async def create_node(
    map_id: str,
    parent_id: str,
    content: str = "",
    position: int = 0,
    style: str = "{}",
    node_id: str | None = None,
) -> dict:
    node_id = node_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO nodes (id, map_id, parent_id, content, position, style, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, map_id, parent_id, content, position, style, now, now),
        )
        await db.execute(
            "UPDATE maps SET updated_at = ? WHERE id = ?", (now, map_id)
        )
        await db.commit()
        return {
            "id": node_id,
            "map_id": map_id,
            "parent_id": parent_id,
            "content": content,
            "position": position,
            "style": style,
            "collapsed": False,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        await db.close()


async def update_node(node_id: str, changes: dict) -> dict | None:
    allowed = {"content", "position", "style", "collapsed", "parent_id"}
    updates = {k: v for k, v in changes.items() if k in allowed}
    if not updates:
        return None

    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [node_id]

    db = await get_db()
    try:
        await db.execute(f"UPDATE nodes SET {set_clause} WHERE id = ?", values)
        # Update map timestamp
        await db.execute(
            """UPDATE maps SET updated_at = ?
               WHERE id = (SELECT map_id FROM nodes WHERE id = ?)""",
            (now, node_id),
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["collapsed"] = bool(d["collapsed"])
        return d
    finally:
        await db.close()


async def delete_node(node_id: str) -> bool:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """UPDATE maps SET updated_at = ?
               WHERE id = (SELECT map_id FROM nodes WHERE id = ?)""",
            (now, node_id),
        )
        cursor = await db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def move_node(node_id: str, new_parent_id: str, position: int) -> dict | None:
    return await update_node(node_id, {"parent_id": new_parent_id, "position": position})
