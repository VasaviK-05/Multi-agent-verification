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
            SELECT validation_id, question_id, question, generated_answer,
                   final_status, final_score, domain, created_at, history_state
            FROM (
                SELECT v.validation_id, v.question_id, v.question, v.generated_answer,
                       v.final_status, v.final_score, v.domain, v.created_at,
                       'validation_record'::text AS history_state
                FROM validation_records v WHERE v.session_id = %s
                UNION ALL
                SELECT NULL::uuid, q.id, q.question, q.answer,
                       NULL::text, NULL::double precision, NULL::text, q.created_at,
                       'generated_only'::text
                FROM questions_answers q
                WHERE q.session_id = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM validation_records v
                      WHERE v.question_id = q.id AND v.session_id = q.session_id
                  )
            ) history
            ORDER BY created_at ASC, question_id ASC, validation_id ASC
            """,
            (session_id, session_id),
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
                "history_state": row[8],
            }
            for row in rows
        ]

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()