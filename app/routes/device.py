import os
from secrets import compare_digest, token_urlsafe
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status

from app.db import get_connection
from app.models import (
    AllowDeviceRequest,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    RevokeDeviceRequest,
)
from app.services.audit import record_audit
from app.services.permissions import allow_device, revoke_device


router = APIRouter(prefix="/device", tags=["device"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=DeviceRegisterResponse)
def register_device(payload: DeviceRegisterRequest, request: Request) -> dict[str, str]:
    register_token = os.getenv("REGISTER_TOKEN")
    if register_token and not compare_digest(payload.register_token or "", register_token):
        record_audit(
            device_id=None,
            action="login",
            ip=client_ip(request),
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid register token",
        )

    token = token_urlsafe(32)
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO devices (id, name, token, status)
            VALUES (%s, %s, %s, 'active')
            ON CONFLICT (name)
            DO UPDATE SET token = EXCLUDED.token, status = 'active'
            RETURNING id, token
            """,
            (str(uuid4()), payload.name, token),
        ).fetchone()

    record_audit(
        device_id=str(row["id"]),
        action="login",
        ip=client_ip(request),
        success=True,
    )
    return {"device_id": str(row["id"]), "token": row["token"]}


@router.get("")
def list_devices() -> list[dict[str, str | None]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, status, created_at, last_seen_at
            FROM devices
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "status": row["status"],
                "created_at": row["created_at"].isoformat(),
                "last_seen_at": row["last_seen_at"].isoformat()
                if row["last_seen_at"]
                else None,
            }
            for row in rows
        ]


@router.post("/allow")
def allow(payload: AllowDeviceRequest, request: Request) -> dict[str, str]:
    allow_device(payload.device, payload.secret, payload.permission)
    record_audit(
        device_id=None,
        action="allow_device",
        secret_name=payload.secret,
        ip=client_ip(request),
        success=True,
    )
    return {"status": "ok"}


@router.post("/revoke")
def revoke(payload: RevokeDeviceRequest, request: Request) -> dict[str, str]:
    revoke_device(payload.device)
    record_audit(
        device_id=None,
        action="revoke_device",
        ip=client_ip(request),
        success=True,
    )
    return {"status": "ok"}

