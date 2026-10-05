from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from database import get_connection


def create_session(title: str):
    session_id = uuid4()

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO sessions (
                session_id,
                title,
                created_at,
                updated_at
            )
            VALUES (%s, %s, NOW(), NOW())
            RETURNING session_id, title, created_at, updated_at
            """,
            (str(session_id), title),
        )

        row = cursor.fetchone()
        connection.commit()

        return {
            "session_id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
        }

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_sessions():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT session_id, title, created_at, updated_at
            FROM sessions
            ORDER BY updated_at DESC
            """
        )

        rows = cursor.fetchall()

        return [
            {
                "session_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
            for row in rows
        ]

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()