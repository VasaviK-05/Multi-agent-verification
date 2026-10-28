from database import get_connection
import json

def load_reputation():
    """
    Load persisted verifier reputation from PostgreSQL.

    Returns a list of dictionaries containing verifier_name, domain,
    alpha and beta.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT verifier_name, domain, alpha, beta
                FROM verifier_reputation
                ORDER BY verifier_name, domain
                """
            )

            rows = cursor.fetchall()

            return [
                {
                    "verifier_name": row[0],
                    "domain": row[1],
                    "alpha": float(row[2]),
                    "beta": float(row[3]),
                }
                for row in rows
            ]

    finally:
        conn.close()


def save_reputation(
    verifier_name: str,
    domain: str,
    alpha: float,
    beta: float,
):
    """
    Persist one verifier/domain reputation using an atomic upsert.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO verifier_reputation (
                    verifier_name,
                    domain,
                    alpha,
                    beta,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (verifier_name, domain)
                DO UPDATE SET
                    alpha = EXCLUDED.alpha,
                    beta = EXCLUDED.beta,
                    updated_at = NOW()
                """,
                (
                    verifier_name,
                    domain,
                    alpha,
                    beta,
                ),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def load_feedback_events():
    """
    Reconstruct persisted feedback events from PostgreSQL.

    The feedback table stores the external label.
    validation_records stores the domain.
    verifier_outputs stores the verifier votes and metadata.
    """
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    f.validation_id,
                    f.is_correct,
                    vr.domain,
                    vo.verifier_name,
                    vo.score,
                    vo.passed,
                    vo.reasoning,
                    vo.metadata,
                    vo.execution_order
                FROM feedback f
                JOIN validation_records vr
                    ON vr.validation_id = f.validation_id
                JOIN verifier_outputs vo
                    ON vo.validation_id = f.validation_id
                ORDER BY
                    f.validation_id,
                    vo.execution_order
                """
            )

            rows = cursor.fetchall()

            events = {}

            for row in rows:
                (
                    validation_id,
                    is_correct,
                    domain,
                    verifier_name,
                    score,
                    passed,
                    reasoning,
                    metadata,
                    execution_order,
                ) = row

                validation_id = str(validation_id)

                event = events.setdefault(
                    validation_id,
                    {
                        "validation_id": validation_id,
                        "domain": domain,
                        "answer_is_correct": bool(is_correct),
                        "source": "ground_truth",
                        "results": [],
                    },
                )

                event["results"].append(
                    {
                        "verifier_name": verifier_name,
                        "score": float(score),
                        "passed": bool(passed),
                        "reasoning": reasoning,
                        "metadata": metadata or {},
                    }
                )

            return list(events.values())

    finally:
        conn.close()

def load_reputation_state():
    """
    Load the persisted reputation snapshot and feedback events.

    Returns the data needed to restore ReputationManager.
    """
    return {
        "reputation": load_reputation(),
        "feedback": load_feedback_events(),
    }

def build_reputation_state():
    """
    Build a ReputationManager-compatible state from persisted feedback.

    The ReputationManager itself calculates successes/failures from the
    persisted verifier results, so abstentions and vote semantics remain
    consistent with the normal learning path.
    """
    from app.models.schemas import VerificationResult
    from app.reputation.reputation_manager import ReputationManager, FeedbackEvent

    state = load_reputation_state()

    manager = ReputationManager()

    events = [
        FeedbackEvent(
            validation_id=event["validation_id"],
            domain=event["domain"],
            answer_is_correct=event["answer_is_correct"],
            results=tuple(
                VerificationResult(**result)
                for result in event["results"]
            ),
            source=event.get("source", "ground_truth"),
        )
        for event in state["feedback"]
    ]

    if events:
        manager.record_feedback_batch(events)

    return manager.export_state()

def save_reputation_manager_state(state: dict) -> None:
    """Persist the complete exported ReputationManager state."""
    if not isinstance(state, dict):
        raise TypeError("state must be a dictionary")

    schema_version = state.get("schema_version")
    if not isinstance(schema_version, int) or schema_version <= 0:
        raise ValueError("state must have a positive schema_version")

    serialized_state = json.dumps(state, allow_nan=False)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO reputation_manager_state (
                    state_id, schema_version, state, updated_at
                )
                VALUES (1, %s, %s::jsonb, NOW())
                ON CONFLICT (state_id)
                DO UPDATE SET
                    schema_version = EXCLUDED.schema_version,
                    state = EXCLUDED.state,
                    updated_at = NOW()
                """,
                (schema_version, serialized_state),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def load_reputation_manager_state() -> dict | None:
    """Load the complete exported state, or None if no snapshot exists."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_version, state
                FROM reputation_manager_state
                WHERE state_id = 1
                """
            )
            row = cursor.fetchone()

        if row is None:
            return None

        schema_version, state = row
        if isinstance(state, str):
            state = json.loads(state)

        if not isinstance(state, dict):
            raise ValueError("Persisted reputation state must be a JSON object")

        if state.get("schema_version") != schema_version:
            raise ValueError("Persisted reputation state version does not match")

        return state
    finally:
        conn.close()


def save_reputation_state_and_rows(state: dict) -> None:
    """Persist the manager snapshot and all reputation rows atomically."""
    if not isinstance(state, dict):
        raise TypeError("state must be a dictionary")

    schema_version = state.get("schema_version")
    if not isinstance(schema_version, int) or schema_version <= 0:
        raise ValueError("state must have a positive schema_version")

    pairs = state.get("pairs")
    if not isinstance(pairs, list):
        raise ValueError("state must contain a pairs list")

    serialized_state = json.dumps(state, allow_nan=False)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Save the complete manager state.
            cursor.execute(
                """
                INSERT INTO reputation_manager_state (
                    state_id, schema_version, state, updated_at
                )
                VALUES (1, %s, %s::jsonb, NOW())
                ON CONFLICT (state_id)
                DO UPDATE SET
                    schema_version = EXCLUDED.schema_version,
                    state = EXCLUDED.state,
                    updated_at = NOW()
                """,
                (schema_version, serialized_state),
            )

            # Save every verifier/domain aggregate in the same transaction.
            for pair in pairs:
                cursor.execute(
                    """
                    INSERT INTO verifier_reputation (
                        verifier_name, domain, alpha, beta, updated_at
                    )
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (verifier_name, domain)
                    DO UPDATE SET
                        alpha = EXCLUDED.alpha,
                        beta = EXCLUDED.beta,
                        updated_at = NOW()
                    """,
                    (
                        pair["verifier_name"],
                        pair["domain"],
                        pair["successes"] + state["prior_alpha"],
                        pair["failures"] + state["prior_beta"],
                    ),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
