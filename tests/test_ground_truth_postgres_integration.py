import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from database import get_connection
from app.ground_truth.storage import save_ground_truth

load_dotenv()


def test_ground_truth_persists_and_handles_retries():
    assert os.getenv("DB_NAME") == "multi_agent_controlled_fixture_test", (
        "Refusing to run outside multi_agent_controlled_fixture_test"
    )

    validation_id = uuid4()
    question = "What is the capital of France?"
    answer = "Paris"
    label = "Paris"
    source = "integration_test"
    question_id = None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO questions_answers (question, answer)
                VALUES (%s, %s)
                RETURNING id
                """,
                (question, answer),
            )
            question_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO validation_records (
                    validation_id, question_id, question, generated_answer
                )
                VALUES (%s, %s, %s, %s)
                """,
                (str(validation_id), question_id, question, answer),
            )

        connection.commit()

        first = save_ground_truth(
            validation_id=validation_id,
            question_id=question_id,
            label=label,
            source=source,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ground_truth_id, validation_id, question_id,
                       label, source
                FROM ground_truth_labels
                WHERE validation_id = %s
                """,
                (str(validation_id),),
            )
            stored = cursor.fetchone()

        assert stored is not None
        assert str(stored[0]) == str(first.ground_truth_id)
        assert str(stored[1]) == str(validation_id)
        assert stored[2] == question_id
        assert stored[3] == label
        assert stored[4] == source

        retry = save_ground_truth(
            validation_id=validation_id,
            question_id=question_id,
            label=label,
            source=source,
        )
        assert retry.ground_truth_id == first.ground_truth_id

        with pytest.raises(ValueError, match="Conflicting ground-truth data"):
            save_ground_truth(
                validation_id=validation_id,
                question_id=question_id,
                label="London",
                source=source,
            )

    finally:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM ground_truth_labels WHERE validation_id = %s",
                    (str(validation_id),),
                )
                cursor.execute(
                    "DELETE FROM validation_records WHERE validation_id = %s",
                    (str(validation_id),),
                )
                if question_id is not None:
                    cursor.execute(
                        "DELETE FROM questions_answers WHERE id = %s",
                        (question_id,),
                    )
            connection.commit()
        finally:
            connection.close()
