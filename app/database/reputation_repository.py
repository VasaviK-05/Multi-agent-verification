from database import get_connection


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