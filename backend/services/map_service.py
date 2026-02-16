from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db, release_db
from backend.services.node_service import get_locks_for_map
import aiomysql


async def list_maps(user_id: str) -> list[dict]:
    """List maps accessible to the user: owned, team-accessible, and legacy (owner_id=NULL)."""
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """SELECT DISTINCT m.* FROM maps m
                   LEFT JOIN team_members tm ON m.team_id = tm.team_id AND tm.user_id = %s
                   WHERE m.owner_id IS NULL
                      OR m.owner_id = %s
                      OR tm.user_id IS NOT NULL
                   ORDER BY m.updated_at DESC""",
                (user_id, user_id),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        release_db(db)


async def create_map(name: str, owner_id: str | None = None, team_id: str | None = None) -> dict:
    map_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO maps (id, name, version, owner_id, team_id, created_at, updated_at) VALUES (%s, %s, 0, %s, %s, %s, %s)",
                (map_id, name, owner_id, team_id, now, now),
            )
            root_id = str(uuid.uuid4())
            await cursor.execute(
                "INSERT INTO nodes (id, map_id, parent_id, content, position, version, created_at, updated_at) VALUES (%s, %s, NULL, %s, 0, 0, %s, %s)",
                (root_id, map_id, name, now, now),
            )
        await db.commit()
        return {
            "id": map_id,
            "name": name,
            "version": 0,
            "owner_id": owner_id,
            "team_id": team_id,
            "created_at": now,
            "updated_at": now,
            "root_id": root_id,
        }
    finally:
        release_db(db)


async def get_map_with_nodes(map_id: str) -> dict | None:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM maps WHERE id = %s", (map_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            map_data = dict(row)

            await cursor.execute(
                "SELECT * FROM nodes WHERE map_id = %s ORDER BY position",
                (map_id,),
            )
            nodes = [dict(r) for r in await cursor.fetchall()]
            for n in nodes:
                n["collapsed"] = bool(n["collapsed"])
            map_data["nodes"] = nodes
            return map_data
    finally:
        release_db(db)


async def get_sync(map_id: str, since_version: int) -> dict | None:
    """Return changes since a given version, or full data if since_version is 0."""
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT id, version FROM maps WHERE id = %s", (map_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            current_version = row["version"]

            # No changes
            if since_version >= current_version:
                locks = await get_locks_for_map(map_id)
                return {"version": current_version, "changed": [], "deleted": [], "locks": locks}

            # Get change log entries since the requested version
            await cursor.execute(
                "SELECT action, node_id FROM change_log WHERE map_id = %s AND version > %s ORDER BY version",
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
                placeholders = ",".join("%s" for _ in changed_ids)
                await cursor.execute(
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
                "locks": await get_locks_for_map(map_id),
            }
    finally:
        release_db(db)


async def delete_map(map_id: str) -> bool:
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute("DELETE FROM change_log WHERE map_id = %s", (map_id,))
            await cursor.execute("DELETE FROM maps WHERE id = %s", (map_id,))
            rowcount = cursor.rowcount
        await db.commit()
        return rowcount > 0
    finally:
        release_db(db)


async def claim_map(map_id: str, user_id: str) -> dict | None | bool:
    """Claim a legacy map. Returns map dict on success, None if not found, False if already owned."""
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM maps WHERE id = %s", (map_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            if row["owner_id"] is not None:
                return False
            now = datetime.now(timezone.utc).isoformat()
            await cursor.execute(
                "UPDATE maps SET owner_id = %s, updated_at = %s WHERE id = %s",
                (user_id, now, map_id),
            )
        await db.commit()
        result = dict(row)
        result["owner_id"] = user_id
        result["updated_at"] = now
        return result
    finally:
        release_db(db)
