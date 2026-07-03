from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from app.db import get_connection


def upsert_secret(name: str, secret_type: str, data: dict[str, Any], device_name: str | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO secrets (id, name, device_name, type, data)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name, device_name)
            DO UPDATE SET type = EXCLUDED.type, data = EXCLUDED.data, updated_at = NOW()
            RETURNING name, type, data
            """,
            (str(uuid4()), name, device_name, secret_type, Jsonb(data)),
        ).fetchone()
        return dict(row)


def update_secret(
    name: str,
    secret_type: str | None,
    data: dict[str, Any] | None,
) -> dict[str, Any]:
    with get_connection() as conn:
        existing = get_secret(name)
        row = conn.execute(
            """
            UPDATE secrets
            SET type = %s, data = %s, updated_at = NOW()
            WHERE name = %s
            RETURNING name, type, data
            """,
            (
                secret_type or existing["type"],
                Jsonb(data if data is not None else existing["data"]),
                name,
            ),
        ).fetchone()
        return dict(row)


def get_secret(name: str, device_name: str | None = None) -> dict[str, Any]:
    with get_connection() as conn:
        # 优先查本设备专用
        if device_name:
            row = conn.execute(
                "SELECT name, type, data FROM secrets WHERE name = %s AND device_name = %s",
                (name, device_name),
            ).fetchone()
            if row:
                return dict(row)
        # 回退到通用
        row = conn.execute(
            "SELECT name, type, data FROM secrets WHERE name = %s AND device_name IS NULL",
            (name,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Secret not found")
        return dict(row)


def list_secrets(device_name: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if device_name:
            # 本设备专用 + 通用，同名取专用
            rows = conn.execute("""
                SELECT name, type, data FROM secrets
                WHERE device_name = %s
                UNION
                SELECT name, type, data FROM secrets
                WHERE device_name IS NULL AND name NOT IN (
                    SELECT name FROM secrets WHERE device_name = %s
                )
                ORDER BY name
            """, (device_name, device_name)).fetchall()
        else:
            rows = conn.execute(
                "SELECT name, type, data FROM secrets WHERE device_name IS NULL ORDER BY name"
            ).fetchall()
        return [dict(row) for row in rows]


def delete_secret(name: str, device_name: str | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM device_permissions WHERE secret_name = %s",
            (name,),
        )
        if device_name:
            result = conn.execute(
                "DELETE FROM secrets WHERE name = %s AND device_name = %s",
                (name, device_name),
            )
        else:
            result = conn.execute(
                "DELETE FROM secrets WHERE name = %s AND device_name IS NULL",
                (name,),
            )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Secret not found")


def list_shared_secrets(device_id: str, device_name: str | None = None) -> dict[str, dict[str, Any]]:
    with get_connection() as conn:
        if device_name:
            rows = conn.execute("""
                SELECT name, data FROM secrets WHERE device_name = %s
                UNION
                SELECT name, data FROM secrets WHERE device_name IS NULL AND name NOT IN (
                    SELECT name FROM secrets WHERE device_name = %s
                )
                ORDER BY name
            """, (device_name, device_name)).fetchall()
        else:
            rows = conn.execute(
                "SELECT name, data FROM secrets WHERE device_name IS NULL ORDER BY name",
            ).fetchall()
        return {row["name"]: row["data"] for row in rows}


def list_allowed_secrets(device_id: str) -> dict[str, dict[str, Any]]:
    return list_shared_secrets(device_id)

