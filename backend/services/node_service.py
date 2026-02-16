from __future__ import annotations

import json
import uuid
import asyncio
from datetime import datetime, timedelta, timezone

from backend.db import get_db


async def node_belongs_to_map(node_id: str, map_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT 1 FROM nodes WHERE id = ? AND map_id = ?",
            (node_id, map_id),
        )
        return await cursor.fetchone() is not None
    finally:
        await db.close()


async def _bump_version(db, map_id: str) -> int:
    """Increment map version and return the new value."""
    await db.execute(
        "UPDATE maps SET version = version + 1, updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), map_id),
    )
    cursor = await db.execute("SELECT version FROM maps WHERE id = ?", (map_id,))
    row = await cursor.fetchone()
    return row["version"]


async def _record_history(
    db,
    node_id: str,
    map_id: str,
    action: str,
    map_version: int,
    user_id: str | None = None,
    username: str | None = None,
    old_content: str | None = None,
    new_content: str | None = None,
    old_parent_id: str | None = None,
    new_parent_id: str | None = None,
    old_position: int | None = None,
    new_position: int | None = None,
    snapshot: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO node_history
           (node_id, map_id, user_id, username, action,
            old_content, new_content, old_parent_id, new_parent_id,
            old_position, new_position, snapshot, map_version, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (node_id, map_id, user_id, username or '', action,
         old_content, new_content, old_parent_id, new_parent_id,
         old_position, new_position, snapshot, map_version, now),
    )


async def create_node(
    map_id: str,
    parent_id: str,
    content: str = "",
    position: int = 0,
    style: str = "{}",
    node_id: str | None = None,
    user_id: str | None = None,
    username: str | None = None,
) -> dict | None:
    node_id = node_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        # Parent node must belong to this map, otherwise reject cross-map writes.
        cursor = await db.execute(
            "SELECT 1 FROM nodes WHERE id = ? AND map_id = ?",
            (parent_id, map_id),
        )
        if await cursor.fetchone() is None:
            return None

        ver = await _bump_version(db, map_id)
        await db.execute(
            """INSERT INTO nodes (id, map_id, parent_id, content, position, style, version,
               last_edited_by, last_edited_by_name, last_edited_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, map_id, parent_id, content, position, style, ver,
             user_id, username or '', now, now, now),
        )
        await db.execute(
            "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'create', ?)",
            (map_id, ver, node_id),
        )
        await _record_history(
            db, node_id, map_id, 'create', ver,
            user_id=user_id, username=username,
            new_content=content, new_parent_id=parent_id, new_position=position,
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
            "last_edited_by": user_id,
            "last_edited_by_name": username or '',
            "last_edited_at": now,
            "created_at": now,
            "updated_at": now,
        }
    finally:
        await db.close()


async def update_node(
    map_id: str,
    node_id: str,
    changes: dict,
    user_id: str | None = None,
    username: str | None = None,
) -> dict | None:
    allowed = {"content", "position", "style", "collapsed", "parent_id"}
    updates = {k: v for k, v in changes.items() if k in allowed}
    if not updates:
        return None

    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        # Get current state before update
        cursor = await db.execute("SELECT * FROM nodes WHERE id = ? AND map_id = ?", (node_id, map_id))
        row = await cursor.fetchone()
        if not row:
            return None
        old_node = dict(row)

        # New parent (if provided) must remain in the same map.
        if "parent_id" in updates and updates["parent_id"] is not None:
            cursor = await db.execute(
                "SELECT 1 FROM nodes WHERE id = ? AND map_id = ?",
                (updates["parent_id"], map_id),
            )
            if await cursor.fetchone() is None:
                return None

        ver = await _bump_version(db, map_id)
        updates["updated_at"] = now
        updates["version"] = ver
        if user_id:
            updates["last_edited_by"] = user_id
            updates["last_edited_by_name"] = username or ''
            updates["last_edited_at"] = now

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [node_id, map_id]
        await db.execute(f"UPDATE nodes SET {set_clause} WHERE id = ? AND map_id = ?", values)
        await db.execute(
            "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'update', ?)",
            (map_id, ver, node_id),
        )

        # Record history
        await _record_history(
            db, node_id, map_id, 'update', ver,
            user_id=user_id, username=username,
            old_content=old_node.get("content"),
            new_content=changes.get("content", old_node.get("content")),
            old_parent_id=old_node.get("parent_id"),
            new_parent_id=changes.get("parent_id", old_node.get("parent_id")),
            old_position=old_node.get("position"),
            new_position=changes.get("position", old_node.get("position")),
        )

        await db.commit()

        cursor = await db.execute("SELECT * FROM nodes WHERE id = ? AND map_id = ?", (node_id, map_id))
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["collapsed"] = bool(d["collapsed"])
        return d
    finally:
        await db.close()


async def delete_node(map_id: str, node_id: str, user_id: str | None = None, username: str | None = None) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM nodes WHERE id = ? AND map_id = ?", (node_id, map_id))
        row = await cursor.fetchone()
        if not row:
            return None

        # Collect full subtree data before deleting
        subtree_nodes = []
        deleted_ids = [node_id]
        queue = [node_id]

        # First collect all IDs
        while queue:
            pid = queue.pop()
            cursor = await db.execute("SELECT id FROM nodes WHERE parent_id = ? AND map_id = ?", (pid, map_id))
            children = await cursor.fetchall()
            for c in children:
                deleted_ids.append(c["id"])
                queue.append(c["id"])

        # Collect full data for snapshot
        for did in deleted_ids:
            cursor = await db.execute("SELECT * FROM nodes WHERE id = ? AND map_id = ?", (did, map_id))
            r = await cursor.fetchone()
            if r:
                d = dict(r)
                d["collapsed"] = bool(d["collapsed"])
                subtree_nodes.append(d)

        ver = await _bump_version(db, map_id)

        # Log all deletions
        for did in deleted_ids:
            await db.execute(
                "INSERT INTO change_log (map_id, version, action, node_id) VALUES (?, ?, 'delete', ?)",
                (map_id, ver, did),
            )

        # Record history with snapshot
        await _record_history(
            db, node_id, map_id, 'delete', ver,
            user_id=user_id, username=username,
            old_content=row["content"],
            old_parent_id=row["parent_id"],
            old_position=row["position"],
            snapshot=json.dumps(subtree_nodes, default=str),
        )

        await db.execute("DELETE FROM nodes WHERE id = ? AND map_id = ?", (node_id, map_id))
        await db.commit()
        return {"deleted_ids": deleted_ids, "version": ver, "map_id": map_id}
    finally:
        await db.close()


async def get_node_history(node_id: str, limit: int = 50) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM node_history WHERE node_id = ? ORDER BY created_at DESC LIMIT ?",
            (node_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_map_history(map_id: str, limit: int = 100) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM node_history WHERE map_id = ? ORDER BY created_at DESC LIMIT ?",
            (map_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def rollback_to_history(
    history_id: int,
    map_id: str,
    user_id: str,
    username: str,
    expected_node_id: str | None = None,
) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM node_history WHERE id = ?", (history_id,))
        row = await cursor.fetchone()
        if not row:
            return {"error": "History entry not found"}
        entry = dict(row)

        if entry["map_id"] != map_id:
            return {"error": "History entry does not belong to this map"}
        if expected_node_id and entry["node_id"] != expected_node_id:
            return {"error": "History entry does not belong to this node"}

        action = entry["action"]

        if action == "update":
            # Reverse: apply old values
            changes = {}
            if entry["old_content"] is not None:
                changes["content"] = entry["old_content"]
            if entry["old_parent_id"] is not None:
                changes["parent_id"] = entry["old_parent_id"]
            if entry["old_position"] is not None:
                changes["position"] = entry["old_position"]
            if changes:
                result = await update_node(map_id, entry["node_id"], changes, user_id=user_id, username=username)
                if not result:
                    return {"error": "Rollback failed"}
                return {"status": "ok", "action": "update_reversed", "node": result}

        elif action == "create":
            # Reverse: delete the node
            result = await delete_node(map_id, entry["node_id"], user_id=user_id, username=username)
            if result is None:
                return {"error": "Rollback failed"}
            return {"status": "ok", "action": "create_reversed", "result": result}

        elif action == "delete":
            # Reverse: restore from snapshot
            if not entry["snapshot"]:
                return {"error": "No snapshot available"}
            snapshot_nodes = json.loads(entry["snapshot"])
            restored = []
            for n in snapshot_nodes:
                result = await create_node(
                    map_id=map_id,
                    parent_id=n["parent_id"],
                    content=n.get("content", ""),
                    position=n.get("position", 0),
                    style=n.get("style", "{}"),
                    node_id=n["id"],
                    user_id=user_id,
                    username=username,
                )
                if not result:
                    return {"error": "Rollback failed"}
                restored.append(result)
            return {"status": "ok", "action": "delete_reversed", "restored": restored}

        return {"error": "Unknown action type"}
    except Exception:
        # db may already be closed above, that's fine
        return {"error": "Rollback failed"}


async def move_node(map_id: str, node_id: str, new_parent_id: str, position: int) -> dict | None:
    return await update_node(map_id, node_id, {"parent_id": new_parent_id, "position": position})


_node_locks = {}
_lock_mutex = asyncio.Lock()
_locks_initialized = False

async def _ensure_locks_initialized():
    global _locks_initialized
    if _locks_initialized:
        return
    
    async with _lock_mutex:
        if _locks_initialized:
            return
            
        db = await get_db()
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(minutes=5)).isoformat()
        
        # Cleanup stale locks in DB first
        await db.execute("DELETE FROM node_locks WHERE locked_at < ?", (cutoff,))
        await db.commit()
        
        # Load from DB
        cursor = await db.execute("SELECT * FROM node_locks")
        rows = await cursor.fetchall()
        for row in rows:
            _node_locks[row["node_id"]] = {
                "map_id": row["map_id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "locked_at": datetime.fromisoformat(row["locked_at"])
            }
        _locks_initialized = True

async def acquire_lock(node_id: str, map_id: str, user_id: str, username: str) -> dict | None:
    """Try to acquire a lock. Returns lock info on success, None if locked by another user."""
    await _ensure_locks_initialized()
    async with _lock_mutex:
        now = datetime.now(timezone.utc)
        
        # Clean up this specific lock if it's stale
        if node_id in _node_locks:
            lock = _node_locks[node_id]
            if (now - lock["locked_at"]).total_seconds() > 300: # 5 minutes
                del _node_locks[node_id]

        # Check existing lock
        if node_id in _node_locks:
            lock = _node_locks[node_id]
            if lock["user_id"] == user_id:
                # Already locked by this user, refresh
                lock["locked_at"] = now
                return {
                    "node_id": node_id, 
                    "user_id": user_id, 
                    "username": username, 
                    "locked_at": now.isoformat()
                }
            else:
                # Locked by another user
                return None

        # Optional: verify node exists in DB (can be skipped for even more speed if frontend is trusted)
        # But for safety we keep it, but use the shared connection
        db = await get_db()
        cursor = await db.execute(
            "SELECT 1 FROM nodes WHERE id = ? AND map_id = ?",
            (node_id, map_id),
        )
        if await cursor.fetchone() is None:
            return None

        # Acquire lock in memory
        _node_locks[node_id] = {
            "map_id": map_id,
            "user_id": user_id,
            "username": username,
            "locked_at": now
        }
        
        # Asyncly sync to DB if needed, but for now just memory is enough for speed
        # To keep it compatible with other parts of the system that might read the DB, 
        # we can do a quick background write.
        async def sync_lock_to_db():
            db = await get_db()
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO node_locks (node_id, map_id, user_id, username, locked_at) VALUES (?, ?, ?, ?, ?)",
                    (node_id, map_id, user_id, username, now.isoformat()),
                )
                await db.commit()
            except:
                pass
        
        asyncio.create_task(sync_lock_to_db())
        
        return {
            "node_id": node_id, 
            "user_id": user_id, 
            "username": username, 
            "locked_at": now.isoformat()
        }


async def release_lock(node_id: str, map_id: str, user_id: str) -> bool:
    await _ensure_locks_initialized()
    async with _lock_mutex:
        if node_id in _node_locks:
            lock = _node_locks[node_id]
            if lock["user_id"] == user_id and lock["map_id"] == map_id:
                del _node_locks[node_id]
                
                # Sync to DB
                async def sync_release_to_db():
                    db = await get_db()
                    try:
                        await db.execute(
                            "DELETE FROM node_locks WHERE node_id = ? AND map_id = ? AND user_id = ?",
                            (node_id, map_id, user_id),
                        )
                        await db.commit()
                    except:
                        pass
                asyncio.create_task(sync_release_to_db())
                return True
        return False


async def get_locks_for_map(map_id: str) -> list[dict]:
    await _ensure_locks_initialized()
    async with _lock_mutex:
        now = datetime.now(timezone.utc)
        locks = []
        to_delete = []
        
        for nid, lock in _node_locks.items():
            if (now - lock["locked_at"]).total_seconds() > 300:
                to_delete.append(nid)
                continue
            
            if lock["map_id"] == map_id:
                locks.append({
                    "node_id": nid,
                    "user_id": lock["user_id"],
                    "username": lock["username"],
                    "locked_at": lock["locked_at"].isoformat()
                })
        
        for nid in to_delete:
            del _node_locks[nid]
            
        return locks
