from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import get_connection


security = HTTPBearer()


def get_current_device(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
) -> dict[str, Any]:
    token = credentials.credentials
    with get_connection() as conn:
        device = conn.execute(
            """
            SELECT id, name, token, status, created_at, last_seen_at
            FROM devices
            WHERE token = %s
            """,
            (token,),
        ).fetchone()
        if not device or device["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked device token",
            )
        conn.execute(
            "UPDATE devices SET last_seen_at = NOW() WHERE id = %s",
            (device["id"],),
        )
        return device


CurrentDevice = Annotated[dict[str, Any], Depends(get_current_device)]

