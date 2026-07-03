# Agent Secret Hub

Python FastAPI + PostgreSQL JSONB secret hub for personal multi-computer agents:
Hermes, OpenClaw, and Codex.

This MVP intentionally does not implement encryption, enterprise SSO, complex RBAC,
dynamic key systems, or Kubernetes.

## Features

- Device registration with bearer device tokens
- PostgreSQL storage for devices, JSONB secrets, permissions, and audit logs
- Secret CRUD API
- Device permission checks for `GET /secrets/{name}` and `GET /sync`
- Typer CLI for login, set, get, allow, revoke, sync, devices, and audit
- `.env` sync targets:
  - `~/.hermes/.env`
  - `~/.openclaw/.env`
  - `~/.codex/.env`

## Start

```bash
cd agent-secret-hub
docker compose up -d
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

The default database URL is:

```text
postgresql://agent_secret:agent_secret@localhost:5432/agent_secret_hub
```

Override it with `DATABASE_URL` if needed.

## CLI

```bash
agent-secret login --name desktop-home --server http://127.0.0.1:8000
agent-secret set OPENAI --type api_key --data "{\"api_key\":\"sk-xxx\",\"base_url\":\"https://api.openai.com/v1\"}"
agent-secret allow desktop-home OPENAI
agent-secret get OPENAI
agent-secret sync all
agent-secret sync hermes
agent-secret sync openclaw
agent-secret sync codex
agent-secret revoke laptop
```

The CLI stores its current server and device token in:

```text
~/.agent-secret-hub/config.json
```

## API

### Register Device

```http
POST /device/register
Content-Type: application/json

{"name": "desktop-home"}
```

### Create or Update Secret

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

### Allow Device

```http
POST /device/allow
Content-Type: application/json

{"device": "desktop-home", "secret": "OPENAI"}
```

### Get Secret

```http
GET /secrets/OPENAI
Authorization: Bearer DEVICE_TOKEN
```

### Sync

```http
GET /sync
Authorization: Bearer DEVICE_TOKEN
```

## Database Tables

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
