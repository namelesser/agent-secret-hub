#!/usr/bin/env bash
set -euo pipefail

APP_NAME="agent-secret-hub"
INSTALL_DIR="${INSTALL_DIR:-/opt/agent-secret-hub}"
ENV_FILE="${ENV_FILE:-/etc/agent-secret-hub.env}"
SERVICE_FILE="/etc/systemd/system/agent-secret-hub.service"
DB_NAME="${DB_NAME:-agent_secret_hub}"
DB_USER="${DB_USER:-agent_secret}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
BRANCH="${BRANCH:-main}"
TARBALL_URL="${TARBALL_URL:-https://github.com/namelesser/agent-secret-hub/archive/refs/heads/${BRANCH}.tar.gz}"
AUTO_UPDATE_TIMEOUT_SECONDS="${AUTO_UPDATE_TIMEOUT_SECONDS:-60}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "请用 root 运行：sudo bash scripts/install-server.sh"
  exit 1
fi

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> 安装系统依赖"
missing_packages=()
command -v git >/dev/null 2>&1 || missing_packages+=(git)
command -v psql >/dev/null 2>&1 || missing_packages+=(postgresql)
command -v python3 >/dev/null 2>&1 || missing_packages+=(python3)
python3 -m pip --version >/dev/null 2>&1 || missing_packages+=(python3-pip)
python3 -m venv --help >/dev/null 2>&1 || missing_packages+=(python3-venv)
command -v rsync >/dev/null 2>&1 || missing_packages+=(rsync)

if (( ${#missing_packages[@]} > 0 )); then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing_packages[@]}"
fi

DB_PASSWORD="${DB_PASSWORD:-$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)}"

echo "==> 准备应用目录：${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
SOURCE_REAL="$(cd "${SOURCE_DIR}" && pwd -P)"
INSTALL_REAL="$(cd "${INSTALL_DIR}" && pwd -P)"
if [[ "${SOURCE_REAL}" != "${INSTALL_REAL}" ]]; then
  rm -rf "${INSTALL_DIR}"
  mkdir -p "${INSTALL_DIR}"
  tar \
    --exclude ".git" \
    --exclude ".venv" \
    --exclude "__pycache__" \
    -C "${SOURCE_DIR}" \
    -cf - . | tar -C "${INSTALL_DIR}" -xf -
else
  echo "当前源码目录就是安装目录，跳过复制。"
fi

echo "==> 初始化 PostgreSQL"
systemctl enable --now postgresql

runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;
SQL

if ! runuser -u postgres -- psql -Atc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -qx 1; then
  runuser -u postgres -- createdb -O "${DB_USER}" "${DB_NAME}"
fi

runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
ALTER DATABASE ${DB_NAME} OWNER TO ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
SQL

cat > "${ENV_FILE}" <<EOF
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}
EOF
chmod 600 "${ENV_FILE}"

echo "==> 安装 Python 应用"
python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${INSTALL_DIR}/.venv/bin/python" -m pip install -e "${INSTALL_DIR}"

echo "==> 注册 systemd 服务"
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Agent Secret Hub
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
ExecStartPre=/bin/bash -lc 'if [ -d .git ]; then timeout ${AUTO_UPDATE_TIMEOUT_SECONDS} git fetch origin ${BRANCH} && git checkout ${BRANCH} && git reset --hard origin/${BRANCH}; fi || true'
ExecStartPre=/bin/bash -lc 'set -o pipefail; if [ ! -d .git ]; then tmp=\$(mktemp -d) && timeout ${AUTO_UPDATE_TIMEOUT_SECONDS} curl -fsSL "${TARBALL_URL}" | tar -xz --strip-components=1 -C "\$tmp" && rsync -a --delete --exclude .venv "\$tmp"/ ${INSTALL_DIR}/ && rm -rf "\$tmp"; fi || true'
ExecStartPre=/bin/bash -lc '${INSTALL_DIR}/.venv/bin/python -m pip install -e ${INSTALL_DIR} >/tmp/agent-secret-hub-pip.log 2>&1 || true'
ExecStart=${INSTALL_DIR}/.venv/bin/python -m uvicorn app.main:app --host ${HOST} --port ${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "${APP_NAME}"
if command -v ufw >/dev/null 2>&1; then
  ufw allow "${PORT}/tcp" || true
fi

echo
echo "安装完成。"
echo "服务地址：http://<服务器IP>:${PORT}"
echo "健康检查：curl http://127.0.0.1:${PORT}/health"
echo "查看日志：journalctl -u ${APP_NAME} -f"
echo "数据库连接串已写入：${ENV_FILE}"
