#!/usr/bin/env python3
"""Agent Secret Hub MCP Server — 通过 MCP 协议暴露凭证管理工具"""

import json
import os
import sys
from pathlib import Path

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

CONFIG_PATH = Path(os.getenv("AGENT_SECRET_CONFIG", "~/.agent-secret-hub/config.json")).expanduser()
DEFAULT_SERVER = os.getenv("AGENT_SECRET_SERVER", "http://127.0.0.1:8000")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"server": DEFAULT_SERVER}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def server_url() -> str:
    return load_config().get("server", DEFAULT_SERVER).rstrip("/")


def auth_headers() -> dict:
    token = load_config().get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api(method: str, path: str, **kwargs) -> dict:
    url = f"{server_url()}{path}"
    resp = httpx.request(method, url, timeout=20, headers=auth_headers(), **kwargs)
    resp.raise_for_status()
    return resp.json()


app = Server("agent-secret-hub")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list",
            description="列出所有凭证（名称和类型）",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get",
            description="获取单个凭证的详细数据",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "凭证名称"}},
                "required": ["name"],
            },
        ),
        Tool(
            name="set",
            description="创建或更新凭证",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "凭证名称"},
                    "type": {"type": "string", "description": "凭证类型：api_key / token / database / generic", "default": "generic"},
                    "data": {"type": "object", "description": "凭证数据 JSON"},
                    "device_only": {"type": "boolean", "description": "仅本设备专用，默认 false（通用）", "default": False},
                },
                "required": ["name", "data"],
            },
        ),
        Tool(
            name="delete",
            description="删除凭证",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "凭证名称"}},
                "required": ["name"],
            },
        ),
        Tool(
            name="devices",
            description="列出所有已注册设备",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="audit",
            description="查看审计日志",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "显示条数", "default": 20}},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "list":
            data = api("GET", "/secrets")
            lines = [f"  {s['name']:30s}  ({s['type']})" for s in data]
            result = "\n".join(lines) + f"\n\n共 {len(data)} 条凭证"

        elif name == "get":
            data = api("GET", f"/secrets/{arguments['name']}")
            result = json.dumps(data, indent=2, ensure_ascii=False)

        elif name == "set":
            payload = {
                "name": arguments["name"],
                "type": arguments.get("type", "generic"),
                "data": arguments["data"],
                "device_only": arguments.get("device_only", False),
            }
            data = api("POST", "/secrets", json=payload)
            result = f"已保存：{data['name']}"

        elif name == "delete":
            api("DELETE", f"/secrets/{arguments['name']}")
            result = f"已删除：{arguments['name']}"

        elif name == "devices":
            data = api("GET", "/device")
            lines = []
            for d in data:
                status = "✓" if d["status"] == "active" else "✗"
                lines.append(f"  {status} {d['name']:20s}  {d['status']}")
            result = "\n".join(lines) + f"\n\n共 {len(data)} 台设备"

        elif name == "audit":
            limit = arguments.get("limit", 20)
            data = api("GET", f"/audit?limit={limit}")
            lines = []
            for a in data:
                lines.append(f"  {a['created_at'][:16]}  {a['action']:15s}  {a.get('secret_name') or ''}")
            result = "\n".join(lines) + f"\n\n共 {len(data)} 条记录"

        else:
            result = f"未知工具：{name}"

    except httpx.HTTPStatusError as e:
        result = f"API 错误 ({e.response.status_code}): {e.response.text}"
    except Exception as e:
        result = f"错误：{e}"

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
