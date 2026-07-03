from fastapi import Request


def client_ip(request: Request) -> str | None:
    """获取客户端 IP"""
    return request.client.host if request.client else None
