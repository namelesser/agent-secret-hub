from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from app.db import get_connection


def upsert_secret(name: str, secret_type: str, data: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO secrets (id, name, type, data)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name)
            DO UPDATE SET type = EXCLUDED.type, data = EXCLUDED.data, updated_at = NOW()
            RETURNING name, type, data
            """,
            (str(uuid4()), name, secret_type, Jsonb(data)),
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


def get_secret(name: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT name, type, data FROM secrets WHERE name = %s",
            (name,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Secret not found")
        return dict(row)


def list_secrets(device_id: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name, type, data FROM secrets ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_secret(name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM device_permissions WHERE secret_name = %s",
            (name,),
        )
        result = conn.execute(
            "DELETE FROM secrets WHERE name = %s",
            (name,),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Secret not found")


def list_shared_secrets(device_id: str) -> dict[str, dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name, data FROM secrets ORDER BY name",
        ).fetchall()
        return {row["name"]: row["data"] for row in rows}


def list_allowed_secrets(device_id: str) -> dict[str, dict[str, Any]]:
    return list_shared_secrets(device_id)

