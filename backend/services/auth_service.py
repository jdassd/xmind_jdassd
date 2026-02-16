from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from backend.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from backend.db import get_db, release_db
import aiomysql


async def register_user(username: str, email: str, password: str, display_name: str = "") -> dict:
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    password_hash = hash_password(password)
    if not display_name:
        display_name = username

    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            # Check uniqueness
            await cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            existing = await cursor.fetchone()
            if existing:
                return {"error": "Username or email already exists"}

            await cursor.execute(
                "INSERT INTO users (id, username, email, password_hash, display_name, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, username, email, password_hash, display_name, now, now),
            )
        await db.commit()
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "display_name": display_name,
        }
    finally:
        release_db(db)


async def authenticate_user(username: str, password: str) -> dict | None:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT id, username, email, password_hash, display_name FROM users WHERE username = %s",
                (username,),
            )
            user = await cursor.fetchone()
            if not user:
                return None
            if not verify_password(password, user["password_hash"]):
                return None
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "display_name": user["display_name"],
            }
    finally:
        release_db(db)


async def store_refresh_token(user_id: str, token: str, expires_at: datetime) -> None:
    token_id = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at) VALUES (%s, %s, %s, %s)",
                (token_id, user_id, token_hash, expires_at.isoformat()),
            )
        await db.commit()
    finally:
        release_db(db)


async def validate_refresh_token(token: str) -> dict | None:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return None

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT rt.id, rt.user_id, u.username, u.email, u.display_name FROM refresh_tokens rt JOIN users u ON rt.user_id = u.id WHERE rt.token_hash = %s AND rt.expires_at > %s",
                (token_hash, datetime.now(timezone.utc).isoformat()),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return {
                "token_id": row["id"],
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "display_name": row["display_name"],
            }
    finally:
        release_db(db)


async def revoke_refresh_token(token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute("DELETE FROM refresh_tokens WHERE token_hash = %s", (token_hash,))
        await db.commit()
    finally:
        release_db(db)


async def revoke_all_refresh_tokens(user_id: str) -> None:
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
        await db.commit()
    finally:
        release_db(db)
