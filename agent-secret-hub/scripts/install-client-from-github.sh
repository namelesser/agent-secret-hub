#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/namelesser/agent-secret-hub.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-${HOME}/.agent-secret-hub/app}"

echo "==> 安装 git"
if ! command -v git >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git
  elif command -v brew >/dev/null 2>&1; then
    brew install git
  else
    echo "未找到 git，请先安装 git。"
    exit 1
  fi
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

echo "==> 执行客户端安装"
bash "${INSTALL_DIR}/scripts/install-client.sh"

