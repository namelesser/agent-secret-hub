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

# Agent Secret Hub (v0.2.0)

个人多电脑 Agent 凭证中心。统一管理 API Key、Token、账号密码、数据库连接，一键同步到 `.env`。

仓库：`https://github.com/namelesser/agent-secret-hub`

替代旧的 PostgreSQL `credentials` 表 + `creds.sh` 脚本方案，所有技能引用已迁移到 agent-secret-hub。

## 凭证存储规则

- **默认通用**：所有设备共享，同名互相覆盖（不重复）
- **设备专用**：加 `--device-only`，各设备各存各的
- **取的时候**：优先取本设备专用的，没有就取通用的

```bash
# 通用（默认）— 所有设备共享
agent-secret set QQ --type generic --data '{"account":"4216952","password": "***"}'

# 本机专用 — 各存各的
agent-secret set PG_LOCAL --device-only --type database --data '{"password": "***"}'
```

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

优先使用 MCP 工具，不需要调用 CLI。验证：`hermes mcp test agent-secret-hub`

MCP server 脚本：`scripts/mcp_server.py`（项目内）

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
- 配置文件：`~/.agent-secret-hub/config.json`
- Skills：`skills/agent-secret-hub.md` + `skills/agent-secret-auto.md`（项目内）

## 认证规则

- 所有 API 端点都需要设备 token（登录后自动保存）
- 登录设备可读写所有 secret（无权限隔离，active 设备共享全部）
- 未登录设备完全无法访问（401）

## HTTPS（可选）

服务端支持通过环境变量启用 HTTPS：
```bash
# /etc/agent-secret-hub.env
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
```
不设置则默认 HTTP。证书文件不存在时自动回退。

## 服务端管理

```bash
# SSH 到服务端（替换实际 IP）
ssh root@<SERVER_IP>

# 服务管理
systemctl status agent-secret-hub
systemctl restart agent-secret-hub
journalctl -u agent-secret-hub -f
```

服务端用 git clone 部署，`systemctl restart` 会自动 `git pull` 最新代码。

## Pitfalls

### 同名凭证跨设备覆盖
`set` 使用 upsert（`ON CONFLICT (name) DO UPDATE`），同名 secret 后存的覆盖先存的。如果两台设备密码不同，用不同 name（如 `PG_MAC`、`PG_WIN`）。

### install-client.sh 包装脚本
安装生成的 `~/.local/bin/agent-secret` 包装脚本默认**不自动更新**（`AGENT_SECRET_AUTO_UPDATE=0`）。手动更新用 `agent-secret update`。

### Python 包名冲突（Windows）
`cli/` 目录会和 Hermes 的 `cli.py` 冲突。项目已重命名为 `agent_secret_cli/`。**创建 Python CLI 工具时，避免用 `cli`、`utils` 等通用名作为顶层包名。**

### PYTHONPATH 冲突
Hermes 的 `PYTHONPATH` 会覆盖项目包。包装脚本必须 `unset PYTHONPATH`。

### f-string 不能跨行
Python 3.11 不支持 f-string 内换行，用 `\n`。如 `f"line1\nline2"` 而非：
```python
f"line1
line2"
```

### patch 残留 diff 标记
用 `patch()` 后检查 `+`/`-` 前缀残留，grep 确认。

### 验证脚本用 bash
Python 嵌套 curl JSON 引号极易出错，验证脚本优先用 bash。

### 公开文档不放敏感信息
Skills、README 等公开文件中用 `<占位符>`，不要写真实 IP、密码、token。不小心泄露后需 `git filter-repo` 重写历史。

### git auto-update 覆盖本地修改
包装脚本 `git reset --hard origin/main` 会覆盖未提交的修改。先 commit+push 再测试，或用 `AGENT_SECRET_AUTO_UPDATE=0` 禁用。

### GitHub tarball CDN 缓存
systemd 用 tarball 安装时，GitHub CDN 会缓存，更新不及时。改用 `git clone` 部署解决。

## References

- `references/server-deployment.md` — 服务端部署（git clone vs tarball、start.sh、HTTPS）
- `references/client-installation.md` — 客户端安装 pitfall（Windows 包名冲突、PYTHONPATH、自动更新控制、Python 版本、注册口令）
