"""Simple model docs/placeholders for SQLite entities used by the app."""

USER_TABLE_SCHEMA = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "full_name": "TEXT NOT NULL",
    "username": "TEXT NOT NULL UNIQUE",
    "email": "TEXT NOT NULL UNIQUE",
    "password_hash": "TEXT NOT NULL",
    "role": "TEXT DEFAULT 'student'",
    "is_active": "INTEGER NOT NULL DEFAULT 1",
    "is_locked": "INTEGER NOT NULL DEFAULT 0",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
}

