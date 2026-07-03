from fastapi import APIRouter, HTTPException, Request

from app.db import get_connection
from app.models import SecretResponse, SecretUpdateRequest, SecretUpsertRequest
from app.services.audit import record_audit
from app.services.auth import CurrentDevice
from app.services.secrets import (
    delete_secret,
    get_secret,
    list_secrets,
    update_secret,
    upsert_secret,
)
from app.services.permissions import device_can_read


router = APIRouter(prefix="/secrets", tags=["secrets"])


from app.utils.client_ip import client_ip


@router.post("", response_model=SecretResponse)
def create_secret(payload: SecretUpsertRequest, request: Request, device: CurrentDevice) -> dict:
    secret = upsert_secret(payload.name, payload.type, payload.data)
    record_audit(
        device_id=str(device["id"]),
        action="set_secret",
        secret_name=payload.name,
        ip=client_ip(request),
        success=True,
    )
    return secret


@router.get("")
+def all_secrets(device: CurrentDevice) -> list[SecretResponse]:
+    return list_secrets(str(device["id"]))


@router.get("/{name}", response_model=SecretResponse)
def read_secret(name: str, request: Request, device: CurrentDevice) -> dict:
    try:
        if not device_can_read(str(device["id"]), name):
            record_audit(
                device_id=str(device["id"]),
                action="get_secret",
                secret_name=name,
                ip=client_ip(request),
                success=False,
            )
            raise HTTPException(status_code=403, detail="Forbidden: device not authorized to read this secret")
        secret = get_secret(name)
        record_audit(
            device_id=str(device["id"]),
            action="get_secret",
            secret_name=name,
            ip=client_ip(request),
            success=True,
        )
        return secret
    except HTTPException as exc:
        if exc.status_code == 404:
            record_audit(
                device_id=str(device["id"]),
                action="get_secret",
                secret_name=name,
                ip=client_ip(request),
                success=False,
            )
        raise


@router.put("/{name}", response_model=SecretResponse)
def edit_secret(name: str, payload: SecretUpdateRequest, request: Request) -> dict:
    secret = update_secret(name, payload.type, payload.data)
    record_audit(
        device_id=None,
        action="set_secret",
        secret_name=name,
        ip=client_ip(request),
        success=True,
    )
    return secret


@router.delete("/{name}")
def remove_secret(name: str, request: Request, device: CurrentDevice) -> dict[str, str]:
    delete_secret(name)
    record_audit(
        device_id=str(device["id"]),
        action="delete_secret",
        secret_name=name,
        ip=client_ip(request),
        success=True,
    )
    return {"status": "ok"}

