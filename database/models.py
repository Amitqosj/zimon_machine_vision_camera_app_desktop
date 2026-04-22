"""Simple model docs/placeholders for PostgreSQL entities used by the app."""

USER_TABLE_SCHEMA = {
    "id": "BIGSERIAL PRIMARY KEY",
    "full_name": "TEXT NOT NULL",
    "username": "TEXT NOT NULL UNIQUE",
    "email": "TEXT NOT NULL UNIQUE",
    "password_hash": "TEXT NOT NULL",
    "role": "TEXT NOT NULL DEFAULT 'student'",
    "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
    "is_locked": "BOOLEAN NOT NULL DEFAULT FALSE",
    "created_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    "updated_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
}

