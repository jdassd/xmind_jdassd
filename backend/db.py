from __future__ import annotations

import aiomysql

_pool: aiomysql.Pool | None = None


async def create_pool(host: str, port: int, user: str, password: str, db: str) -> None:
    global _pool
    _pool = await aiomysql.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        db=db,
        autocommit=False,
        charset="utf8mb4",
        minsize=2,
        maxsize=10,
    )


async def close_pool() -> None:
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def get_db() -> aiomysql.Connection:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call create_pool() first.")
    conn = await _pool.acquire()
    return conn


def release_db(conn: aiomysql.Connection) -> None:
    if _pool is not None:
        _pool.release(conn)


async def init_db() -> None:
    conn = await get_db()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS maps (
                    id          VARCHAR(36) PRIMARY KEY,
                    name        TEXT NOT NULL,
                    version     INTEGER NOT NULL DEFAULT 0,
                    owner_id    VARCHAR(36),
                    team_id     VARCHAR(36),
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id          VARCHAR(36) PRIMARY KEY,
                    map_id      VARCHAR(36) NOT NULL,
                    parent_id   VARCHAR(36),
                    content     TEXT NOT NULL,
                    position    INTEGER NOT NULL DEFAULT 0,
                    style       TEXT DEFAULT '{}',
                    collapsed   TINYINT(1) DEFAULT 0,
                    version     INTEGER NOT NULL DEFAULT 0,
                    last_edited_by VARCHAR(36),
                    last_edited_by_name VARCHAR(255) DEFAULT '',
                    last_edited_at DATETIME,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_nodes_map (map_id),
                    INDEX idx_nodes_parent (parent_id)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
                    map_id      VARCHAR(36) NOT NULL,
                    version     INTEGER NOT NULL,
                    action      VARCHAR(50) NOT NULL,
                    node_id     VARCHAR(36) NOT NULL,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_changelog_map_ver (map_id, version)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            VARCHAR(36) PRIMARY KEY,
                    username      VARCHAR(255) NOT NULL UNIQUE,
                    email         VARCHAR(255) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name  VARCHAR(255) NOT NULL DEFAULT '',
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id          VARCHAR(36) PRIMARY KEY,
                    user_id     VARCHAR(36) NOT NULL,
                    token_hash  VARCHAR(64) NOT NULL,
                    expires_at  DATETIME NOT NULL,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_refresh_tokens_user (user_id)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id          VARCHAR(36) PRIMARY KEY,
                    name        VARCHAR(255) NOT NULL,
                    owner_id    VARCHAR(36) NOT NULL,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    team_id     VARCHAR(36) NOT NULL,
                    user_id     VARCHAR(36) NOT NULL,
                    role        VARCHAR(20) NOT NULL DEFAULT 'viewer',
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (team_id, user_id)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS team_invitations (
                    id            VARCHAR(36) PRIMARY KEY,
                    team_id       VARCHAR(36) NOT NULL,
                    inviter_id    VARCHAR(36) NOT NULL,
                    invitee_email VARCHAR(255) NOT NULL,
                    role          VARCHAR(20) NOT NULL DEFAULT 'viewer',
                    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_invitations_email (invitee_email)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS node_history (
                    id          INTEGER PRIMARY KEY AUTO_INCREMENT,
                    node_id     VARCHAR(36) NOT NULL,
                    map_id      VARCHAR(36) NOT NULL,
                    user_id     VARCHAR(36),
                    username    VARCHAR(255) DEFAULT '',
                    action      VARCHAR(20) NOT NULL,
                    old_content TEXT,
                    new_content TEXT,
                    old_parent_id VARCHAR(36),
                    new_parent_id VARCHAR(36),
                    old_position INTEGER,
                    new_position INTEGER,
                    snapshot    LONGTEXT,
                    map_version INTEGER,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_node_history_node (node_id),
                    INDEX idx_node_history_map (map_id, created_at DESC)
                )
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS node_locks (
                    node_id     VARCHAR(36) PRIMARY KEY,
                    map_id      VARCHAR(36) NOT NULL,
                    user_id     VARCHAR(36) NOT NULL,
                    username    VARCHAR(255) DEFAULT '',
                    locked_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add indexes on maps table (ignore if they already exist)
            for idx_sql in [
                "CREATE INDEX idx_maps_owner ON maps(owner_id)",
                "CREATE INDEX idx_maps_team ON maps(team_id)",
            ]:
                try:
                    await cur.execute(idx_sql)
                except Exception:
                    pass

        await conn.commit()
    finally:
        release_db(conn)
