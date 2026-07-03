import os
from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://agent_secret:***@localhost:5432/agent_secret_hub",
)

pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global pool
    if pool is None:
        pool = ConnectionPool(DATABASE_URL, min_size=2, max_size=10, kwargs={"row_factory": dict_row})
    return pool


def get_connection():
    """返回连接上下文管理器，自动归还到连接池"""
    return get_pool().connection()


def db_cursor() -> Iterator[psycopg.Cursor]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            yield cur


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
              id UUID PRIMARY KEY,
              name TEXT UNIQUE NOT NULL,
              token TEXT NOT NULL,
              status TEXT DEFAULT 'active',
              created_at TIMESTAMP DEFAULT NOW(),
              last_seen_at TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secrets (
              id UUID PRIMARY KEY,
              name TEXT UNIQUE NOT NULL,
              type TEXT NOT NULL,
              data JSONB NOT NULL,
              created_at TIMESTAMP DEFAULT NOW(),
              updated_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS device_permissions (
              device_id UUID NOT NULL,
              secret_name TEXT NOT NULL,
              permission TEXT DEFAULT 'read',
              PRIMARY KEY (device_id, secret_name)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
              id UUID PRIMARY KEY,
              device_id UUID,
              action TEXT,
              secret_name TEXT,
              ip TEXT,
              success BOOLEAN DEFAULT TRUE,
              created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_device_permissions_secret_name ON device_permissions (secret_name);"
        )

