"""PostgreSQL-backed user store and audit persistence."""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


class Database:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL")
        if not self.dsn:
            raise RuntimeError("DATABASE_URL must be configured")

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            yield conn

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

                CREATE TABLE IF NOT EXISTS audit_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type VARCHAR(80) NOT NULL,
                    username VARCHAR(100),
                    role VARCHAR(50),
                    request_id VARCHAR(100),
                    details JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_events(created_at);
                CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_events(username);
                """
            )

    def get_user(self, username: str) -> dict | None:
        with self.connection() as conn:
            return conn.execute(
                "SELECT username, password_hash, role, active FROM users WHERE username=%s",
                (username,),
            ).fetchone()

    def upsert_user(self, username: str, password_hash: str, role: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    password_hash=EXCLUDED.password_hash,
                    role=EXCLUDED.role,
                    active=TRUE,
                    updated_at=NOW()
                """,
                (username, password_hash, role),
            )

    def audit(
        self,
        event_type: str,
        username: str | None = None,
        role: str | None = None,
        request_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_events
                    (event_type, username, role, request_id, details, created_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    event_type,
                    username,
                    role,
                    request_id,
                    __import__("json").dumps(details or {}),
                    datetime.now(timezone.utc),
                ),
            )
