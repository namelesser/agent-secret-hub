from fastapi import HTTPException, status

from app.db import get_connection


VALID_PERMISSIONS = {"read", "write", "admin"}


def allow_device(device_name: str, secret_name: str, permission: str = "read") -> None:
    if permission not in VALID_PERMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"permission must be one of: {', '.join(sorted(VALID_PERMISSIONS))}",
        )

    with get_connection() as conn:
        device = conn.execute(
            "SELECT id FROM devices WHERE name = %s",
            (device_name,),
        ).fetchone()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        secret = conn.execute(
            "SELECT name FROM secrets WHERE name = %s",
            (secret_name,),
        ).fetchone()
        if not secret:
            raise HTTPException(status_code=404, detail="Secret not found")

        conn.execute(
            """
            INSERT INTO device_permissions (device_id, secret_name, permission)
            VALUES (%s, %s, %s)
            ON CONFLICT (device_id, secret_name)
            DO UPDATE SET permission = EXCLUDED.permission
            """,
            (device["id"], secret_name, permission),
        )


def revoke_device(device_name: str) -> None:
    with get_connection() as conn:
        result = conn.execute(
            "UPDATE devices SET status = 'revoked' WHERE name = %s",
            (device_name,),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Device not found")


def device_can_read(device_id: str, secret_name: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM device_permissions
            WHERE device_id = %s AND secret_name = %s
            """,
            (device_id, secret_name),
        ).fetchone()
        return row is not None

