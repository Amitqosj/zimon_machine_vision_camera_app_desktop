import bcrypt
import sqlite3

from database.db import get_connection


ROLE_ADMIN = "admin"
ROLE_STUDENT = "student"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def write_audit_log(
    action: str,
    performed_by_user_id: int | None = None,
    target_user_id: int | None = None,
    ip_address: str | None = None,
    description: str = "",
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO audit_logs (action, performed_by_user_id, target_user_id, ip_address, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (action, performed_by_user_id, target_user_id, ip_address, description),
        )
        conn.commit()
    finally:
        conn.close()


def create_user(full_name, username, email, password, role=ROLE_STUDENT):
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    try:
        cursor.execute(
            """
            INSERT INTO users (full_name, username, email, password_hash, role, is_active, is_locked)
            VALUES (?, ?, ?, ?, ?, 1, 0)
            """,
            (full_name.strip(), username.strip(), email.strip().lower(), password_hash, role),
        )
        conn.commit()
        return True, cursor.lastrowid
    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "users.username" in msg or "username" in msg:
            return False, "Username already exists"
        if "users.email" in msg or "email" in msg:
            return False, "Email already exists"
        return False, "User already exists"
    except Exception:
        return False, "Database error while creating user"
    finally:
        conn.close()


def verify_login_credentials(username_or_email, password):
    """
    Validate credentials and return user payload without updating app_session.
    Use for stateless API auth (e.g. JWT) so web clients do not fight the desktop session row.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, full_name, username, email, password_hash, role, is_active, is_locked, created_at
            FROM users
            WHERE lower(username) = lower(?) OR lower(email) = lower(?)
            """,
            (username_or_email.strip(), username_or_email.strip()),
        )
        user = cursor.fetchone()
    finally:
        conn.close()

    if not user:
        return False, "Invalid credentials"
    if int(user[6]) != 1 or int(user[7]) == 1:
        return False, "Invalid credentials"
    if verify_password(password, user[4]):
        payload = {
            "id": user[0],
            "full_name": user[1],
            "username": user[2],
            "email": user[3],
            "role": user[5],
            "is_active": bool(user[6]),
            "is_locked": bool(user[7]),
            "created_at": user[8],
        }
        return True, payload
    return False, "Invalid credentials"


def set_active_session(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE app_session
            SET user_id = ?, is_logged_in = 1, last_login = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()


def clear_active_session():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE app_session
            SET user_id = NULL, is_logged_in = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_active_session_user():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT u.id, u.full_name, u.username, u.email, u.role, u.created_at
            FROM app_session s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = 1 AND s.is_logged_in = 1
            """
        )
        user = cursor.fetchone()
        if not user:
            return None
        return {
            "id": user[0],
            "full_name": user[1],
            "username": user[2],
            "email": user[3],
            "role": user[4],
            "created_at": user[5],
        }
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, full_name, username, email, role, is_active, is_locked, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "full_name": row[1],
        "username": row[2],
        "email": row[3],
        "role": row[4],
        "is_active": bool(row[5]),
        "is_locked": bool(row[6]),
        "created_at": row[7],
        "updated_at": row[8],
    }


def list_users():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, full_name, username, email, role, is_active, is_locked, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return [
        {
            "id": row[0],
            "full_name": row[1],
            "username": row[2],
            "email": row[3],
            "role": row[4],
            "is_active": bool(row[5]),
            "is_locked": bool(row[6]),
            "created_at": row[7],
            "updated_at": row[8],
        }
        for row in rows
    ]


def update_user(user_id: int, full_name: str, email: str, is_active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, is_active = ?, role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (full_name.strip(), email.strip().lower(), 1 if is_active else 0, ROLE_STUDENT, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_user_active_state(user_id: int, is_active: bool):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if is_active else 0, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_user_password(user_id: int, new_password: str, unlock: bool = False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?, is_locked = CASE WHEN ? THEN 0 ELSE is_locked END, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (hash_password(new_password), 1 if unlock else 0, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_user_lock_state(user_id: int, locked: bool):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET is_locked = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if locked else 0, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_user_by_username_or_email(username_or_email: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, full_name, username, email, role, is_active, is_locked, created_at, updated_at
            FROM users
            WHERE lower(username) = lower(?) OR lower(email) = lower(?)
            """,
            (username_or_email.strip(), username_or_email.strip()),
        )
        row = cursor.fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "full_name": row[1],
        "username": row[2],
        "email": row[3],
        "role": row[4],
        "is_active": bool(row[5]),
        "is_locked": bool(row[6]),
        "created_at": row[7],
        "updated_at": row[8],
    }

