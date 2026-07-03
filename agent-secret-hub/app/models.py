from typing import Any

from pydantic import BaseModel, Field


class DeviceRegisterRequest(BaseModel):
    name: str = Field(min_length=1)


class DeviceRegisterResponse(BaseModel):
    device_id: str
    token: str


class DeviceResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    last_seen_at: str | None = None


class SecretUpsertRequest(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(default="generic", min_length=1)
    data: dict[str, Any]


class SecretUpdateRequest(BaseModel):
    type: str | None = None
    data: dict[str, Any] | None = None


class SecretResponse(BaseModel):
    name: str
    type: str
    data: dict[str, Any]


class AllowDeviceRequest(BaseModel):
    device: str = Field(min_length=1)
    secret: str = Field(min_length=1)
    permission: str = "read"


class RevokeDeviceRequest(BaseModel):
    device: str = Field(min_length=1)


class AuditLogResponse(BaseModel):
    id: str
    device_id: str | None
    action: str | None
    secret_name: str | None
    ip: str | None
    success: bool
    created_at: str

