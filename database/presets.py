"""CRUD for analysis presets (per user)."""

from typing import Any, Dict, List, Optional

from database.db import get_connection


def list_presets(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, user_id, name, description, video_path, config_path, output_dir, created_at
            FROM presets
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    keys = (
        "id",
        "user_id",
        "name",
        "description",
        "video_path",
        "config_path",
        "output_dir",
        "created_at",
    )
    return [dict(zip(keys, row)) for row in rows]


def create_preset(
    user_id: int,
    name: str,
    description: Optional[str] = None,
    video_path: Optional[str] = None,
    config_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO presets (user_id, name, description, video_path, config_path, output_dir)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, name, description or "", video_path or "", config_path or "", output_dir or ""),
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return int(new_id)
    finally:
        conn.close()


def update_preset(
    user_id: int,
    preset_id: int,
    name: str,
    description: Optional[str] = None,
    video_path: Optional[str] = None,
    config_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE presets
            SET name = %s, description = %s, video_path = %s, config_path = %s, output_dir = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                name,
                description or "",
                video_path or "",
                config_path or "",
                output_dir or "",
                preset_id,
                user_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_preset(user_id: int, preset_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM presets WHERE id = %s AND user_id = %s",
            (preset_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_preset(user_id: int, preset_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, user_id, name, description, video_path, config_path, output_dir, created_at
            FROM presets
            WHERE id = %s AND user_id = %s
            """,
            (preset_id, user_id),
        )
        row = cursor.fetchone()
    finally:
        conn.close()
    if not row:
        return None
    keys = (
        "id",
        "user_id",
        "name",
        "description",
        "video_path",
        "config_path",
        "output_dir",
        "created_at",
    )
    return dict(zip(keys, row))
