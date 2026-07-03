from fastapi import APIRouter, Request

from app.db import get_connection
from app.services.audit import record_audit
from app.services.auth import CurrentDevice
from app.services.secrets import list_shared_secrets


router = APIRouter(tags=["sync"])


from app.utils.client_ip import client_ip


@router.get("/sync")
def sync_secrets(request: Request, device: CurrentDevice) -> dict:
    data = list_shared_secrets(str(device["id"]))
    record_audit(
        device_id=str(device["id"]),
        action="sync",
        ip=client_ip(request),
        success=True,
    )
    return data


@router.get("/audit")
def audit_logs(device: CurrentDevice, limit: int = 100) -> list[dict]:
    limit = max(1, min(limit, 500))
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, device_id, action, secret_name, ip, success, created_at
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "device_id": str(row["device_id"]) if row["device_id"] else None,
                "action": row["action"],
                "secret_name": row["secret_name"],
                "ip": row["ip"],
                "success": row["success"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]

