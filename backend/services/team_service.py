from __future__ import annotations

import uuid
from datetime import datetime, timezone

from backend.db import get_db, release_db
import aiomysql


async def create_team(name: str, owner_id: str) -> dict:
    team_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO teams (id, name, owner_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                (team_id, name, owner_id, now, now),
            )
            # Add owner as team member with 'owner' role
            await cursor.execute(
                "INSERT INTO team_members (team_id, user_id, role, created_at) VALUES (%s, %s, 'owner', %s)",
                (team_id, owner_id, now),
            )
        await db.commit()
        return {"id": team_id, "name": name, "owner_id": owner_id, "created_at": now, "updated_at": now}
    finally:
        release_db(db)


async def list_user_teams(user_id: str) -> list[dict]:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """SELECT t.id, t.name, t.owner_id, t.created_at, t.updated_at, tm.role
                   FROM teams t
                   JOIN team_members tm ON t.id = tm.team_id
                   WHERE tm.user_id = %s
                   ORDER BY t.updated_at DESC""",
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        release_db(db)


async def get_team(team_id: str) -> dict | None:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    finally:
        release_db(db)


async def update_team(team_id: str, name: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE teams SET name = %s, updated_at = %s WHERE id = %s",
                (name, now, team_id),
            )
            await db.commit()
            await cursor.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    finally:
        release_db(db)


async def delete_team(team_id: str) -> bool:
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute("DELETE FROM teams WHERE id = %s", (team_id,))
            rowcount = cursor.rowcount
        await db.commit()
        return rowcount > 0
    finally:
        release_db(db)


async def list_team_members(team_id: str) -> list[dict]:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """SELECT u.id, u.username, u.email, u.display_name, tm.role, tm.created_at
                   FROM team_members tm
                   JOIN users u ON tm.user_id = u.id
                   WHERE tm.team_id = %s
                   ORDER BY tm.created_at""",
                (team_id,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        release_db(db)


async def add_team_member(team_id: str, user_id: str, role: str = "viewer") -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            # Check if already a member
            await cursor.execute(
                "SELECT team_id FROM team_members WHERE team_id = %s AND user_id = %s",
                (team_id, user_id),
            )
            if await cursor.fetchone():
                return None  # Already a member

            await cursor.execute(
                "INSERT INTO team_members (team_id, user_id, role, created_at) VALUES (%s, %s, %s, %s)",
                (team_id, user_id, role, now),
            )
        await db.commit()
        return {"team_id": team_id, "user_id": user_id, "role": role}
    finally:
        release_db(db)


async def update_member_role(team_id: str, user_id: str, role: str) -> bool:
    db = await get_db()
    try:
        async with db.cursor() as cursor:
            await cursor.execute(
                "UPDATE team_members SET role = %s WHERE team_id = %s AND user_id = %s",
                (role, team_id, user_id),
            )
            rowcount = cursor.rowcount
        await db.commit()
        return rowcount > 0
    finally:
        release_db(db)


async def remove_team_member(team_id: str, user_id: str) -> bool:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            # Cannot remove the owner
            await cursor.execute(
                "SELECT role FROM team_members WHERE team_id = %s AND user_id = %s",
                (team_id, user_id),
            )
            row = await cursor.fetchone()
            if not row or row["role"] == "owner":
                return False

            await cursor.execute(
                "DELETE FROM team_members WHERE team_id = %s AND user_id = %s",
                (team_id, user_id),
            )
            rowcount = cursor.rowcount
        await db.commit()
        return rowcount > 0
    finally:
        release_db(db)


# --- Invitations ---

async def create_invitation(team_id: str, inviter_id: str, invitee_email: str, role: str = "viewer") -> dict:
    inv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            # Check if invitation already pending
            await cursor.execute(
                "SELECT id FROM team_invitations WHERE team_id = %s AND invitee_email = %s AND status = 'pending'",
                (team_id, invitee_email),
            )
            existing = await cursor.fetchone()
            if existing:
                return {"error": "Invitation already pending for this email"}

            await cursor.execute(
                "INSERT INTO team_invitations (id, team_id, inviter_id, invitee_email, role, status, created_at) VALUES (%s, %s, %s, %s, %s, 'pending', %s)",
                (inv_id, team_id, inviter_id, invitee_email, role, now),
            )
        await db.commit()
        return {"id": inv_id, "team_id": team_id, "invitee_email": invitee_email, "role": role, "status": "pending"}
    finally:
        release_db(db)


async def list_user_invitations(email: str) -> list[dict]:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """SELECT i.id, i.team_id, i.invitee_email, i.role, i.status, i.created_at,
                          t.name as team_name, u.display_name as inviter_name
                   FROM team_invitations i
                   JOIN teams t ON i.team_id = t.id
                   JOIN users u ON i.inviter_id = u.id
                   WHERE i.invitee_email = %s AND i.status = 'pending'
                   ORDER BY i.created_at DESC""",
                (email,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        release_db(db)


async def accept_invitation(invitation_id: str, user_id: str) -> dict | None:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM team_invitations WHERE id = %s AND status = 'pending'",
                (invitation_id,),
            )
            inv = await cursor.fetchone()
            if not inv:
                return None

            # Verify user email matches invitation
            await cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            user = await cursor.fetchone()
            if not user or user["email"] != inv["invitee_email"]:
                return None

            # Add to team
            now = datetime.now(timezone.utc).isoformat()
            try:
                await cursor.execute(
                    "INSERT INTO team_members (team_id, user_id, role, created_at) VALUES (%s, %s, %s, %s)",
                    (inv["team_id"], user_id, inv["role"], now),
                )
            except Exception:
                # Already a member, update role
                await cursor.execute(
                    "UPDATE team_members SET role = %s WHERE team_id = %s AND user_id = %s",
                    (inv["role"], inv["team_id"], user_id),
                )

            await cursor.execute(
                "UPDATE team_invitations SET status = 'accepted' WHERE id = %s",
                (invitation_id,),
            )
        await db.commit()
        return {"id": invitation_id, "status": "accepted", "team_id": inv["team_id"]}
    finally:
        release_db(db)


async def decline_invitation(invitation_id: str, user_id: str) -> dict | None:
    db = await get_db()
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM team_invitations WHERE id = %s AND status = 'pending'",
                (invitation_id,),
            )
            inv = await cursor.fetchone()
            if not inv:
                return None

            # Verify user email matches
            await cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            user = await cursor.fetchone()
            if not user or user["email"] != inv["invitee_email"]:
                return None

            await cursor.execute(
                "UPDATE team_invitations SET status = 'declined' WHERE id = %s",
                (invitation_id,),
            )
        await db.commit()
        return {"id": invitation_id, "status": "declined"}
    finally:
        release_db(db)
