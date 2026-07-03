#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/namelesser/agent-secret-hub.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/agent-secret-hub}"
GIT_TIMEOUT_SECONDS="${GIT_TIMEOUT_SECONDS:-60}"
TARBALL_URL="${TARBALL_URL:-https://github.com/namelesser/agent-secret-hub/archive/refs/heads/${BRANCH}.tar.gz}"

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
  if ! timeout "${GIT_TIMEOUT_SECONDS}" git -C "${INSTALL_DIR}" fetch origin "${BRANCH}" ||
     ! git -C "${INSTALL_DIR}" checkout "${BRANCH}" ||
     ! git -C "${INSTALL_DIR}" reset --hard "origin/${BRANCH}"; then
    echo "git 更新失败，改用 tarball 下载：${TARBALL_URL}"
    tmp_dir="$(mktemp -d)"
    curl -fsSL "${TARBALL_URL}" | tar -xz --strip-components=1 -C "${tmp_dir}"
    rm -rf "${INSTALL_DIR}"
    mkdir -p "${INSTALL_DIR}"
    cp -a "${tmp_dir}/." "${INSTALL_DIR}/"
    rm -rf "${tmp_dir}"
  fi
else
  rm -rf "${INSTALL_DIR}"
  if ! timeout "${GIT_TIMEOUT_SECONDS}" git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"; then
    echo "git clone 失败，改用 tarball 下载：${TARBALL_URL}"
    mkdir -p "${INSTALL_DIR}"
    curl -fsSL "${TARBALL_URL}" | tar -xz --strip-components=1 -C "${INSTALL_DIR}"
  fi
fi

echo "==> 执行服务端安装"
INSTALL_DIR="${INSTALL_DIR}" TARBALL_URL="${TARBALL_URL}" bash "${INSTALL_DIR}/scripts/install-server.sh"

