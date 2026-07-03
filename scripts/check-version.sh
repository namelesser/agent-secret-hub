#!/usr/bin/env bash
# 检查 skill 版本与项目版本是否一致，不一致则更新 skill
set -euo pipefail

SKILL_DIR="$HOME/.hermes/skills/devops"
PROJECT_DIR="$HOME/workspace/agent-secret-hub"

# 读取项目版本
PROJECT_VER=$(grep '^version' "$PROJECT_DIR/pyproject.toml" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')

# 读取 skill 版本
SKILL_VER=$(grep -o 'v[0-9]*\.[0-9]*\.[0-9]*' "$SKILL_DIR/agent-secret-hub/SKILL.md" | head -1 | sed 's/^v//')

if [ "$PROJECT_VER" = "$SKILL_VER" ]; then
    echo "✓ 版本一致: v$PROJECT_VER"
    exit 0
fi

echo "⚠ 版本不一致: 项目=v$PROJECT_VER, skill=v$SKILL_VER"
echo "==> 更新 skill..."

# 从项目复制 skill 文件
cp "$PROJECT_DIR/skills/agent-secret-hub.md" "$SKILL_DIR/agent-secret-hub/SKILL.md"
cp "$PROJECT_DIR/skills/agent-secret-auto.md" "$SKILL_DIR/agent-secret-auto/SKILL.md"

NEW_VER=$(grep -o 'v[0-9]*\.[0-9]*\.[0-9]*' "$SKILL_DIR/agent-secret-hub/SKILL.md" | head -1)
echo "✓ skill 已更新到 $NEW_VER"
