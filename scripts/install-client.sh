#!/usr/bin/env bash
set -euo pipefail

INSTALL_BIN="${INSTALL_BIN:-${HOME}/.local/bin}"
SERVER_URL="${SERVER_URL:-}"
DEVICE_NAME="${DEVICE_NAME:-}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> 安装客户端依赖"
python3 -m venv "${SOURCE_DIR}/.venv"
"${SOURCE_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${SOURCE_DIR}/.venv/bin/python" -m pip install -e "${SOURCE_DIR}"

mkdir -p "${INSTALL_BIN}"
cat > "${INSTALL_BIN}/agent-secret" <<EOF
#!/usr/bin/env bash
exec "${SOURCE_DIR}/.venv/bin/agent-secret" "\$@"
EOF
chmod +x "${INSTALL_BIN}/agent-secret"

echo "==> 客户端安装完成"
echo "命令位置：${INSTALL_BIN}/agent-secret"

case ":${PATH}:" in
  *":${INSTALL_BIN}:"*) ;;
  *)
    echo "提示：${INSTALL_BIN} 不在 PATH 里，可执行："
    echo "export PATH=\"${INSTALL_BIN}:\$PATH\""
    ;;
esac

if [[ -n "${SERVER_URL}" && -n "${DEVICE_NAME}" ]]; then
  "${INSTALL_BIN}/agent-secret" login --name "${DEVICE_NAME}" --server "${SERVER_URL}"
else
  echo "登录示例：agent-secret login --name my-laptop --server http://服务器IP:8000"
fi

