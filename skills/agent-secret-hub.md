---
name: agent-secret-hub
description: 使用 agent-secret CLI 管理多设备 Agent 凭证（API Key/Token/密码），同步到 Hermes/OpenClaw/Codex 的 .env。
trigger:
  - agent-secret
  - secret hub
  - 凭证同步
  - 凭证管理
  - secret sync
  - 凭证查询
---

# Agent Secret Hub

个人多电脑 Agent 凭证中心。统一管理 API Key、Token、账号密码、数据库连接，一键同步到 `.env`。

## MCP Server（推荐）

已注册为 Hermes MCP server，工具前缀 `mcp_agent_secret_hub_*`：

| 工具 | 说明 |
|------|------|
| `mcp_agent_secret_hub_list` | 列出所有凭证 |
| `mcp_agent_secret_hub_get` | 获取凭证详情 |
| `mcp_agent_secret_hub_set` | 创建/更新凭证 |
| `mcp_agent_secret_hub_delete` | 删除凭证 |
| `mcp_agent_secret_hub_devices` | 列出设备 |
| `mcp_agent_secret_hub_audit` | 审计日志 |

优先使用 MCP 工具，不需要调用 CLI。

## CLI 命令速查

```bash
agent-secret --help          # 主帮助（中文）
agent-secret login --help    # 登录
agent-secret list            # 列出凭证
agent-secret get <NAME>      # 获取凭证
agent-secret set <NAME>      # 设置凭证
agent-secret export          # 导出 JSON
agent-secret import <file>   # 导入 JSON
agent-secret sync all        # 同步到 .env（merge 模式）
agent-secret devices         # 设备列表
agent-secret audit           # 审计日志
agent-secret update          # 更新客户端
```

## 环境信息

- CLI 路径：`~/.local/bin/agent-secret`
- 项目目录：`~/workspace/agent-secret-hub`
- 服务端：京东云 `http://REDACTED_IP:8000`（git clone，重启自动更新）
- 当前设备：`mac-mini`
- 配置文件：`~/.agent-secret-hub/config.json`

## 认证规则

- 所有 API 端点都需要设备 token（登录后自动保存）
- 登录设备可读写所有 secret（无权限隔离，active 设备共享全部）
- 未登录设备完全无法访问（401）

## Pitfalls

- **push before restart** — 本地 commit 不 push，服务端 git pull 会拉到旧代码
- **f-string 不能跨行** — Python 3.11 不支持 f-string 内换行，用 `\n`
- **patch 残留 diff 标记** — 检查 `+`/`-` 前缀残留
- **验证脚本用 bash** — Python 嵌套 curl JSON 引号极易出错

## HTTPS（可选）

服务端支持通过环境变量启用 HTTPS：
```bash
# /etc/agent-secret-hub.env
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
```

## 服务端管理

```bash
# SSH 到京东云
sshpass -p 'REDACTED_PASSWORD' ssh root@REDACTED_IP

# 服务管理
systemctl status agent-secret-hub
systemctl restart agent-secret-hub
journalctl -u agent-secret-hub -f
```

## 常见问题

1. **ConnectError** — 用公网 IP，不要用局域网 IP
2. **Not authenticated** — 先 `agent-secret login`
3. **PYTHONPATH 冲突** — 包装脚本已处理 `unset PYTHONPATH`
4. **Python 版本** — 项目要求 >=3.10，已用 python3.11
