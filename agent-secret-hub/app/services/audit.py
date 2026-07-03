from uuid import uuid4

from app.db import get_connection


def record_audit(
    *,
    device_id: str | None,
    action: str,
    secret_name: str | None = None,
    ip: str | None = None,
    success: bool = True,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (id, device_id, action, secret_name, ip, success)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (str(uuid4()), device_id, action, secret_name, ip, success),
        )

