import os
import sys
from pathlib import Path

import psycopg
try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None


def get_runtime_base_dir() -> Path:
    """Return the executable directory in build mode, project root in dev mode."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_app_data_dir() -> Path:
    """Compatibility helper retained for older path-based callers."""
    return get_runtime_base_dir()


_LOCAL_FALLBACK_CONNECTION_STRING = (
    "host=127.0.0.1 port=5432 dbname=zimon user=postgres password=postgres sslmode=disable"
)
_LEGACY_CLOUD_CONNECTION_STRING = (
    "Host=trolley.proxy.rlwy.net;Port=43066;Database=railway;Username=postgres;"
    "Password=ZvjFxEikmIXDgwwvJMpZJjUmvpDAVmkE;SSL Mode=Require;Trust Server Certificate=true"
)


def _load_env_files() -> None:
    if load_dotenv is None:
        return
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")
    load_dotenv(root / "backend" / ".env", override=True)


def _normalize_connection_string(raw_connection_string: str) -> str:
    raw = raw_connection_string.strip().strip("\"' ")

    # If a URL contains key/value payload by mistake (e.g. "postgresql://Host=...;Port=..."),
    # fall through to key/value parser instead of treating it as a URL.
    if "://" in raw and "host=" not in raw.lower():
        return raw

    if "://" in raw and "host=" in raw.lower():
        raw = raw.split("://", 1)[1]

    parts = {}
    for item in raw.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip().lower()] = value.strip()

    mapped = {
        "host": parts.get("host"),
        "port": parts.get("port"),
        "dbname": parts.get("database"),
        "user": parts.get("username") or parts.get("user id") or parts.get("user"),
        "password": parts.get("password"),
        "sslmode": (parts.get("ssl mode") or parts.get("sslmode") or "require").lower(),
    }
    return " ".join(f"{k}={v}" for k, v in mapped.items() if v)


def _conn_dict(conninfo: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in conninfo.split():
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        out[k.strip().lower()] = v.strip()
    return out


def _looks_like_ipv4(host: str) -> bool:
    parts = host.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def _with_overrides(conninfo: str, **overrides: str) -> str:
    data = _conn_dict(conninfo)
    for k, v in overrides.items():
        data[k.lower()] = v
    order = ("host", "port", "dbname", "user", "password", "sslmode")
    items = [f"{k}={data[k]}" for k in order if data.get(k)]
    for k in data.keys():
        if k not in order:
            items.append(f"{k}={data[k]}")
    return " ".join(items)


def get_connection():
    _load_env_files()
    explicit = (
        os.environ.get("ZIMON_DATABASE_CONNECTION_STRING")
        or os.environ.get("ZIMON_DATABASE_URL")
        or ""
    ).strip()

    attempts: list[tuple[str, str]] = []
    if explicit:
        normalized = _normalize_connection_string(explicit)
        attempts.append(("configured", normalized))
        cfg = _conn_dict(normalized)
        host = cfg.get("host", "")
        # Rescue for Railway-style configs using raw IP (breaks TLS/SNI on some networks).
        if host and _looks_like_ipv4(host):
            attempts.append(
                (
                    "configured-hostname-fallback",
                    _with_overrides(normalized, host="trolley.proxy.rlwy.net", sslmode="require"),
                )
            )
        # Retry with explicit sslmode=require unless already set to require.
        if cfg.get("sslmode", "").lower() != "require":
            attempts.append(("configured-ssl-require", _with_overrides(normalized, sslmode="require")))
    attempts.append(("local-fallback", _LOCAL_FALLBACK_CONNECTION_STRING))
    attempts.append(("legacy-cloud-fallback", _normalize_connection_string(_LEGACY_CLOUD_CONNECTION_STRING)))

    last_error: Exception | None = None
    for label, conninfo in attempts:
        try:
            return psycopg.connect(conninfo, connect_timeout=8)
        except Exception as exc:
            last_error = exc
            # Try next candidate.
            continue

    raise RuntimeError(
        "Database connection failed. Checked configured DB connection and local fallback "
        "(host=127.0.0.1 port=5432 dbname=zimon). Set ZIMON_DATABASE_CONNECTION_STRING "
        "or ZIMON_DATABASE_URL to a reachable PostgreSQL instance."
    ) from last_error


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_locked BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT users_role_check CHECK (role IN ('admin', 'student'))
        )
        """
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
            id SMALLINT PRIMARY KEY CHECK (id = 1),
            user_id BIGINT,
            is_logged_in BOOLEAN NOT NULL DEFAULT FALSE,
            last_login TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO app_session (id, user_id, is_logged_in)
        VALUES (1, NULL, FALSE)
        ON CONFLICT (id) DO NOTHING
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS presets (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            video_path TEXT,
            config_path TEXT,
            output_dir TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
            id BIGSERIAL PRIMARY KEY,
            action TEXT NOT NULL,
            performed_by_user_id BIGINT,
            target_user_id BIGINT,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
            id BIGSERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_id BIGINT,
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
            notification_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id BIGSERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            category TEXT,
            message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    conn.commit()
    conn.close()

