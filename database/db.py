import os
import sqlite3
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return writable app data directory for desktop/runtime builds."""
    if os.name == "nt":
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
    else:
        base = Path.home() / ".local" / "share"
    app_dir = base / "ZIMON"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


_default_db = get_app_data_dir() / "zimon_app.db"
DB_PATH = os.environ.get("ZIMON_DATABASE_PATH", str(_default_db))


def get_connection():
    return sqlite3.connect(DB_PATH)


def _column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    return any(c[1] == column for c in cols)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_active INTEGER NOT NULL DEFAULT 1,
            is_locked INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    if not _column_exists(cursor, "users", "is_active"):
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
    if not _column_exists(cursor, "users", "is_locked"):
        cursor.execute("ALTER TABLE users ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0")
    if not _column_exists(cursor, "users", "updated_at"):
        # SQLite does not allow non-constant defaults in ALTER TABLE ADD COLUMN.
        cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
        cursor.execute(
            "UPDATE users SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)"
        )

    cursor.execute(
        """
        UPDATE users
        SET role = CASE
            WHEN lower(role) = 'admin' THEN 'admin'
            ELSE 'student'
        END
        """
    )
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]
    if admin_count == 0:
        cursor.execute(
            """
            UPDATE users
            SET role = 'admin'
            WHERE id = (SELECT id FROM users ORDER BY created_at ASC, id ASC LIMIT 1)
            """
        )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_session (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_id INTEGER,
            is_logged_in INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO app_session (id, user_id, is_logged_in)
        VALUES (1, NULL, 0)
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            video_path TEXT,
            config_path TEXT,
            output_dir TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_presets_user_id ON presets(user_id)
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            performed_by_user_id INTEGER,
            target_user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            description TEXT,
            FOREIGN KEY(performed_by_user_id) REFERENCES users(id),
            FOREIGN KEY(target_user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_reads (
            notification_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (notification_id, user_id),
            FOREIGN KEY(notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_reads_user_id ON notification_reads(user_id)
        """
    )

    conn.commit()
    conn.close()

