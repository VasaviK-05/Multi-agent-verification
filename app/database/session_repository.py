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

def get_session_questions(session_id: str):
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                validation_id,
                question_id,
                question,
                generated_answer,
                final_status,
                final_score,
                domain,
                created_at
            FROM validation_records
            WHERE session_id = %s
            ORDER BY created_at ASC
            """,
            (session_id,),
        )

        rows = cursor.fetchall()

        return [
            {
                "validation_id": row[0],
                "question_id": row[1],
                "question": row[2],
                "generated_answer": row[3],
                "final_status": row[4],
                "final_score": row[5],
                "domain": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()