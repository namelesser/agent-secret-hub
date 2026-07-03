#!/usr/bin/env bash
# Agent Secret Hub 启动脚本
# 支持可选 HTTPS：设置 SSL_CERTFILE 和 SSL_KEYFILE 环境变量即启用
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
SSL_CERTFILE="${SSL_CERTFILE:-}"
SSL_KEYFILE="${SSL_KEYFILE:-}"

UVICORN_ARGS=(
    "app.main:app"
    --host "$HOST"
    --port "$PORT"
)

# 有证书就用 HTTPS，没有就 HTTP
if [[ -n "$SSL_CERTFILE" && -n "$SSL_KEYFILE" ]]; then
    if [[ -f "$SSL_CERTFILE" && -f "$SSL_KEYFILE" ]]; then
        echo "==> HTTPS 模式 (cert: $SSL_CERTFILE)"
        UVICORN_ARGS+=(--ssl-certfile "$SSL_CERTFILE")
        UVICORN_ARGS+=(--ssl-keyfile "$SSL_KEYFILE")
    else
        echo "警告: SSL 文件不存在，回退到 HTTP 模式" >&2
    fi
else
    echo "==> HTTP 模式 (设置 SSL_CERTFILE 和 SSL_KEYFILE 可启用 HTTPS)"
fi

exec "$(dirname "$0")/../.venv/bin/python" -m uvicorn "${UVICORN_ARGS[@]}"
