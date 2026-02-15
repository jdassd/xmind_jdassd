from __future__ import annotations

import aiosqlite

_db_path: str = ""


def set_db_path(path: str) -> None:
    global _db_path
    _db_path = path


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS maps (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                version     INTEGER NOT NULL DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS nodes (
                id          TEXT PRIMARY KEY,
                map_id      TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
                parent_id   TEXT REFERENCES nodes(id) ON DELETE CASCADE,
                content     TEXT NOT NULL DEFAULT '',
                position    INTEGER NOT NULL DEFAULT 0,
                style       TEXT DEFAULT '{}',
                collapsed   BOOLEAN DEFAULT 0,
                version     INTEGER NOT NULL DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_nodes_map ON nodes(map_id);
            CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);

            CREATE TABLE IF NOT EXISTS change_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                map_id      TEXT NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
                version     INTEGER NOT NULL,
                action      TEXT NOT NULL,
                node_id     TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_changelog_map_ver ON change_log(map_id, version);
            """
        )
        # Migrate: add version column to existing tables if missing
        try:
            await db.execute("ALTER TABLE maps ADD COLUMN version INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE nodes ADD COLUMN version INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        await db.commit()
    finally:
        await db.close()
