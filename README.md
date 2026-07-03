# Agent Secret Hub

个人多电脑 Agent 凭证中心。用于统一管理 API Key、Token、账号密码、API URL、数据库连接信息，并同步生成 Hermes / OpenClaw / Codex 的 `.env` 文件。

当前 MVP：

- FastAPI 服务端
- PostgreSQL JSONB 存储
- 多设备 device token
- Secret CRUD API
- 设备授权与吊销
- Typer CLI 管理工具
- 一键同步到 Agent `.env`

明确不包含：加密、企业 SSO、复杂 RBAC、动态密钥系统、Kubernetes。

## 仓库

```text
https://github.com/namelesser/agent-secret-hub
```

如果仓库是 private，先在目标机器上配置 GitHub 访问权限，再 `git clone`。

```bash
git clone https://github.com/namelesser/agent-secret-hub.git
cd agent-secret-hub
```

## 一键安装服务端 Ubuntu

在服务器上执行：

```bash
sudo bash scripts/install-server.sh
```

脚本会自动完成：

- 安装 Python、PostgreSQL、git、rsync
- 创建 PostgreSQL 数据库 `agent_secret_hub`
- 创建数据库用户 `agent_secret`
- 生成随机数据库密码
- 写入 `/etc/agent-secret-hub.env`
- 安装 Python 依赖
- 创建并启动 systemd 服务 `agent-secret-hub`

默认服务地址：

```text
http://服务器IP:8000
```

检查服务：

```bash
curl http://127.0.0.1:8000/health
systemctl status agent-secret-hub
journalctl -u agent-secret-hub -f
```

自定义端口：

```bash
PORT=9000 sudo -E bash scripts/install-server.sh
```

自定义安装目录：

```bash
INSTALL_DIR=/opt/my-secret-hub sudo -E bash scripts/install-server.sh
```

## 一键安装客户端 Windows

在 Windows PowerShell 里进入项目目录：

```powershell
cd "C:\path\to\agent-secret-hub"
powershell -ExecutionPolicy Bypass -File .\scripts\install-client.ps1
```

安装后重新打开终端，即可使用：

```powershell
agent-secret --help
```

也可以安装后直接登录设备：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-client.ps1 `
  -ServerUrl "http://服务器IP:8000" `
  -DeviceName "desktop-home"
```

## 一键安装客户端 Linux / macOS

```bash
bash scripts/install-client.sh
```

安装后确认 `~/.local/bin` 在 PATH 里：

```bash
agent-secret --help
```

也可以安装后直接登录设备：

```bash
SERVER_URL="http://服务器IP:8000" DEVICE_NAME="laptop" bash scripts/install-client.sh
```

## 基本使用流程

### 1. 每台电脑登录一次

```bash
agent-secret login --name codex-pc --server http://服务器IP:8000
```

登录后 device token 会保存在：

```text
~/.agent-secret-hub/config.json
```

### 2. 创建或更新 secret

OpenAI：

```bash
agent-secret set OPENAI --type api_key --data "{\"api_key\":\"sk-xxx\",\"base_url\":\"https://api.openai.com/v1\"}"
```

GitHub：

```bash
agent-secret set GITHUB --type token --data "{\"token\":\"ghp_xxx\"}"
```

数据库：

```bash
agent-secret set POSTGRES_MAIN --type database --data "{\"host\":\"1.2.3.4\",\"port\":5432,\"username\":\"postgres\",\"password\":\"123456\",\"database\":\"main\"}"
```

### 3. 授权设备读取 secret

```bash
agent-secret allow codex-pc OPENAI
agent-secret allow codex-pc GITHUB
```

未授权的设备不能读取对应 secret。

### 4. 获取单个 secret

```bash
agent-secret get OPENAI
```

### 5. 同步到 Agent `.env`

同步全部 Agent：

```bash
agent-secret sync all
```

只同步某一个：

```bash
agent-secret sync hermes
agent-secret sync openclaw
agent-secret sync codex
```

输出文件：

```text
~/.hermes/.env
~/.openclaw/.env
~/.codex/.env
```

示例输出：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
GITHUB_TOKEN=ghp_xxx
```

### 6. 查看设备和审计日志

```bash
agent-secret devices
agent-secret audit
```

### 7. 吊销设备

```bash
agent-secret revoke laptop
```

吊销后，该设备 token 不能再读取 secret，也不能再执行 sync。

## 常用服务端命令

```bash
systemctl restart agent-secret-hub
systemctl stop agent-secret-hub
systemctl status agent-secret-hub
journalctl -u agent-secret-hub -f
```

服务端环境变量文件：

```text
/etc/agent-secret-hub.env
```

## API

### 注册设备

```http
POST /device/register
Content-Type: application/json

{"name": "desktop-home"}
```

### 创建或更新 secret

```http
POST /secrets
Content-Type: application/json

{
  "name": "OPENAI",
  "type": "api_key",
  "data": {
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1"
  }
}
```

### 授权设备

```http
POST /device/allow
Content-Type: application/json

{"device": "desktop-home", "secret": "OPENAI"}
```

### 获取 secret

```http
GET /secrets/OPENAI
Authorization: Bearer DEVICE_TOKEN
```

### 同步全部

```http
GET /sync
Authorization: Bearer DEVICE_TOKEN
```

## 数据库表

```sql
CREATE TABLE devices (
  id UUID PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  token TEXT NOT NULL,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP
);

CREATE TABLE secrets (
  id UUID PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL,
  data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE device_permissions (
  device_id UUID NOT NULL,
  secret_name TEXT NOT NULL,
  permission TEXT DEFAULT 'read',
  PRIMARY KEY (device_id, secret_name)
);

CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  device_id UUID,
  action TEXT,
  secret_name TEXT,
  ip TEXT,
  success BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```
