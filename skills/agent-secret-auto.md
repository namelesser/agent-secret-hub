---
name: agent-secret-auto
description: 遇到凭证自动保存到 agent-secret-hub，需要时优先从 agent-secret-hub 查询。配合 MCP Server 使用。
trigger:
  - 自动保存凭证
  - 凭证自动存储
  - 账号密码保存
  - token 保存
  - key 保存
  - 凭证查询
  - 查密码
  - 查 token
  - 查 key
---

# Agent Secret 自动凭证管理

与 agent-secret-hub MCP Server 配合，实现凭证自动保存和查询。

## 核心规则

### 遇到凭证 → 自动保存

当对话中出现以下信息时，**主动调用 MCP 工具保存**，不需要用户提示：

- 账号/密码
- API Key / Secret Key
- Token / Access Token / Refresh Token
- 授权码
- 数据库连接信息
- SSH 密码/密钥
- 任何敏感凭证

**保存格式：**

```
name: 大写下划线，如 GITHUB_TOKEN、JD_SSH_PASSWORD
type: api_key / token / database / generic
data: JSON 对象，包含所有相关字段
```

**示例：**

```json
// API Key
name: "OPENAI_API_KEY"
type: "api_key"
data: {"api_key": "***", "base_url": "https://api.openai.com/v1"}

// 账号密码
name: "ROUTER_ADMIN"
type: "generic"
data: {"username": "admin", "password": "***", "host": "192.168.1.1"}

// 数据库
name: "PG_MAIN"
type: "database"
data: {"host": "1.2.3.4", "port": 5432, "username": "postgres", "password": "***", "database": "main"}

// Token
name: "GITHUB_TOKEN"
type: "token"
data: {"token": "ghp_***"}
```

### 需要凭证 → 先查询

当需要使用某个凭证时（调 API、连数据库、登录等），**先从 agent-secret-hub 查询**，不要问用户要。

```
1. 调用 mcp_agent_secret_hub_get 查询
2. 有 → 使用
3. 没有 → 问用户要，拿到后自动保存
```

### 工作流

```
用户提供凭证 → 自动保存 → 告知已保存
需要凭证 → 查询 → 有就用 / 没有就问 → 拿到后保存
```

## MCP 工具

| 工具 | 说明 |
|------|------|
| `mcp_agent_secret_hub_list` | 列出所有凭证 |
| `mcp_agent_secret_hub_get` | 获取凭证详情 |
| `mcp_agent_secret_hub_set` | 创建/更新凭证 |
| `mcp_agent_secret_hub_delete` | 删除凭证 |

## CLI 兼容

如果 MCP 不可用，退化为 CLI：

```bash
agent-secret list
agent-secret get <NAME>
agent-secret set <NAME> --type <TYPE> --data '<JSON>'
```

## 注意事项

- name 命名要有意义，方便后续查询（如 `JD_SSH` 而不是 `MYPASSWORD`）
- 同名凭证会自动更新（不会重复保存）
- 保存后简短告知用户即可，不需要长篇解释
- 敏感信息不要写入记忆/日志，只存 agent-secret-hub
