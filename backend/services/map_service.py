from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db


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
            "INSERT INTO maps (id, name, version, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
            (map_id, name, now, now),
        )
        root_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO nodes (id, map_id, parent_id, content, position, version, created_at, updated_at) VALUES (?, ?, NULL, ?, 0, 0, ?, ?)",
            (root_id, map_id, name, now, now),
        )
        await db.commit()
        return {"id": map_id, "name": name, "version": 0, "created_at": now, "updated_at": now, "root_id": root_id}
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


async def get_sync(map_id: str, since_version: int) -> dict | None:
    """Return changes since a given version, or full data if since_version is 0."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, version FROM maps WHERE id = ?", (map_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        current_version = row["version"]

        # No changes
        if since_version >= current_version:
            return {"version": current_version, "changed": [], "deleted": []}

        # Get change log entries since the requested version
        cursor = await db.execute(
            "SELECT action, node_id FROM change_log WHERE map_id = ? AND version > ? ORDER BY version",
            (map_id, since_version),
        )
        log_entries = await cursor.fetchall()

        deleted_ids = set()
        changed_ids = set()
        for entry in log_entries:
            if entry["action"] == "delete":
                deleted_ids.add(entry["node_id"])
                changed_ids.discard(entry["node_id"])
            else:
                changed_ids.add(entry["node_id"])
                deleted_ids.discard(entry["node_id"])

        changed_nodes = []
        if changed_ids:
            placeholders = ",".join("?" for _ in changed_ids)
            cursor = await db.execute(
                f"SELECT * FROM nodes WHERE id IN ({placeholders})",
                list(changed_ids),
            )
            rows = await cursor.fetchall()
            for r in rows:
                d = dict(r)
                d["collapsed"] = bool(d["collapsed"])
                changed_nodes.append(d)

        return {
            "version": current_version,
            "changed": changed_nodes,
            "deleted": list(deleted_ids),
        }
    finally:
        await db.close()


async def delete_map(map_id: str) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM change_log WHERE map_id = ?", (map_id,))
        cursor = await db.execute("DELETE FROM maps WHERE id = ?", (map_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
