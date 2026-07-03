#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/namelesser/agent-secret-hub.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/agent-secret-hub}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "请用 root 运行：curl ... | sudo bash"
  exit 1
fi

echo "==> 安装 git"
if ! command -v git >/dev/null 2>&1; then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y git
fi

echo "==> 拉取项目：${REPO_URL}"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  git -C "${INSTALL_DIR}" fetch origin "${BRANCH}"
  git -C "${INSTALL_DIR}" checkout "${BRANCH}"
  git -C "${INSTALL_DIR}" reset --hard "origin/${BRANCH}"
else
  rm -rf "${INSTALL_DIR}"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"
fi

echo "==> 执行服务端安装"
INSTALL_DIR="${INSTALL_DIR}" bash "${INSTALL_DIR}/scripts/install-server.sh"

