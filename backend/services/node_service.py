from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db


async def _bump_version(db, map_id: str) -> int:
    """Increment map version and return the new value."""
    await db.execute(
        "UPDATE maps SET version = version + 1, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), map_id),
    )
    cursor = await db.execute("SELECT version FROM maps WHERE id = ?", (map_id,))
    row = await cursor.fetchone()
    return row["version"]


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
        ver = await _bump_version(db, map_id)
        await db.execute(
            """INSERT INTO nodes (id, map_id, parent_id, content, position, style, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, map_id, parent_id, content, position, style, ver, now, now),
        )
        await db.execute(
            "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'create', ?)",
            (map_id, ver, node_id),
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
            "version": ver,
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
    db = await get_db()
    try:
        # Get map_id first
        cursor = await db.execute("SELECT map_id FROM nodes WHERE id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        map_id = row["map_id"]

        ver = await _bump_version(db, map_id)
        updates["updated_at"] = now
        updates["version"] = ver

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [node_id]
        await db.execute(f"UPDATE nodes SET {set_clause} WHERE id = ?", values)
        await db.execute(
            "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'update', ?)",
            (map_id, ver, node_id),
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


async def delete_node(node_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT map_id FROM nodes WHERE id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        map_id = row["map_id"]

        # Collect all descendant ids before deleting (CASCADE will remove them)
        deleted_ids = [node_id]
        queue = [node_id]
        while queue:
            pid = queue.pop()
            cursor = await db.execute("SELECT id FROM nodes WHERE parent_id = ?", (pid,))
            children = await cursor.fetchall()
            for c in children:
                deleted_ids.append(c["id"])
                queue.append(c["id"])

        ver = await _bump_version(db, map_id)

        # Log all deletions
        for did in deleted_ids:
            await db.execute(
                "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'delete', ?)",
                (map_id, ver, did),
            )

        await db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        await db.commit()
        return {"deleted_ids": deleted_ids, "version": ver, "map_id": map_id}
    finally:
        await db.close()


async def move_node(node_id: str, new_parent_id: str, position: int) -> dict | None:
    return await update_node(node_id, {"parent_id": new_parent_id, "position": position})
