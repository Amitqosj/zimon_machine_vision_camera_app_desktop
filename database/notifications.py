from database.db import get_connection


def create_notification(title: str, message: str, user_id: int | None = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO notifications (title, message, user_id, is_read)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
            """,
            (title, message, user_id),
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return int(new_id)
    finally:
        conn.close()


def list_for_user(user_id: int) -> list[dict]:
    """Notifications visible to this user: broadcast (user_id NULL) or targeted to them."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                n.id,
                n.title,
                n.message,
                n.created_at,
                n.user_id,
                CASE
                    WHEN n.user_id IS NULL THEN
                        CASE WHEN EXISTS (
                            SELECT 1 FROM notification_reads r
                            WHERE r.notification_id = n.id AND r.user_id = %s
                        ) THEN TRUE ELSE FALSE END
                    ELSE n.is_read
                END AS is_read_effective
            FROM notifications n
            WHERE n.user_id IS NULL OR n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT 100
            """,
            (user_id, user_id),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()
    return [
        {
            "id": row[0],
            "title": row[1],
            "message": row[2],
            "created_at": row[3],
            "user_id": row[4],
            "is_read": bool(row[5]),
        }
        for row in rows
    ]


def mark_read(notification_id: int, reader_user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT user_id FROM notifications WHERE id = %s
            """,
            (notification_id,),
        )
        row = cursor.fetchone()
        if not row:
            return False
        owner_id = row[0]
        if owner_id is not None and int(owner_id) != reader_user_id:
            return False
        if owner_id is None:
            cursor.execute(
                """
                INSERT INTO notification_reads (notification_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT (notification_id, user_id) DO NOTHING
                """,
                (notification_id, reader_user_id),
            )
        else:
            cursor.execute(
                """
                UPDATE notifications SET is_read = TRUE WHERE id = %s
                """,
                (notification_id,),
            )
        conn.commit()
        return True
    finally:
        conn.close()
