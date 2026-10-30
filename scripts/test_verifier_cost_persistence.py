
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import verifier_cost_repository as repository
from database import get_connection


def main():
    suffix = uuid4().hex
    verifier_name = f"integration-test-verifier-{suffix}"
    setup_fingerprint = f"integration-test-{suffix}"
    run_id = str(uuid4())
    calibration_id = str(uuid4())

    setup_id = None
    attempt_ids = []
    estimate_id = None

    try:
        # 1. Save a unique measurement setup.
        setup_id = repository.save_measurement_setup(
            verifier_name=verifier_name,
            setup_fingerprint=setup_fingerprint,
            verifier_implementation="integration-test",
            implementation_fingerprint=f"impl-{suffix}",
            config_fingerprint=f"config-{suffix}",
            verifier_config={"test": True},
            code_revision="integration-test",
        )
        print("Setup saved:", setup_id)

        # 2. Save three attempts: two successes and one failure.
        attempt_specs = [
            ("returned", 10.0),
            ("returned", 20.0),
            ("failure", 30.0),
        ]

        for outcome, duration_ms in attempt_specs:
            attempt_id = repository.save_verifier_attempt(
                run_id=run_id,
                verifier_name=verifier_name,
                setup_id=setup_id,
                outcome=outcome,
                duration_ms=duration_ms,
                measurement_purpose="calibration",
                data_role="development",
                metadata={"integration_test": True, "suffix": suffix},
            )
            attempt_ids.append(attempt_id)
            print(f"Attempt saved: {attempt_id} ({outcome}, {duration_ms} ms)")

        # 3. Calculate the estimate from persisted attempts.
        estimate_id = repository.calculate_and_save_cost_estimate(
            calibration_id=calibration_id,
            verifier_name=verifier_name,
            setup_id=setup_id,
            estimator_version="integration-test-v1",
            measurement_purpose="calibration",
            data_role="development",
        )
        print("Calculated estimate saved:", estimate_id)

        # 4. Read the calculated estimate back from PostgreSQL.
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT mean_attempt_cost_ms,
                           median_duration_ms,
                           p95_duration_ms,
                           attempt_count,
                           failure_count,
                           input_digest,
                           source_attempt_ids
                    FROM verifier_cost_estimates
                    WHERE estimate_id = %s
                    """,
                    (estimate_id,),
                )
                row = cur.fetchone()
                assert row is not None, "Estimate was not persisted"

                mean_ms, median_ms, p95_ms, count, failures, digest, raw_ids = row

                assert float(mean_ms) == 20.0, mean_ms
                assert float(median_ms) == 20.0, median_ms
                assert float(p95_ms) == 30.0, p95_ms
                assert count == 3, count
                assert failures == 1, failures
                assert digest and len(digest) == 64, digest

                if isinstance(raw_ids, str):
                    stored_ids = (
                        raw_ids.strip("{}").split(",")
                        if raw_ids.strip("{}")
                        else []
                    )
                else:
                    stored_ids = [str(value) for value in raw_ids]

                stored_ids = [value.strip() for value in stored_ids]

                assert set(stored_ids) == set(attempt_ids), stored_ids

                print("Mean:", mean_ms)
                print("Median:", median_ms)
                print("P95:", p95_ms)
                print("Attempt count:", count)
                print("Failure count:", failures)
                print("Input digest:", digest)
                print("Source attempts verified:", len(stored_ids))

        finally:
            conn.close()

        print(
            "PASS: cost statistics were calculated from persisted attempts "
            "and the estimate was read back from PostgreSQL."
        )

    finally:
        # Delete only records created by this test.
        conn = get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    if estimate_id:
                        cur.execute(
                            """
                            DELETE FROM verifier_cost_estimates
                            WHERE estimate_id = %s
                            """,
                            (estimate_id,),
                        )

                    if attempt_ids:
                        cur.execute(
                            """
                            DELETE FROM verifier_cost_attempts
                            WHERE attempt_id = ANY(%s::uuid[])
                            """,
                            (attempt_ids,),
                        )

                    if setup_id:
                        cur.execute(
                            """
                            DELETE FROM verifier_measurement_setups
                            WHERE setup_id = %s
                              AND setup_fingerprint = %s
                            """,
                            (setup_id, setup_fingerprint),
                        )
        finally:
            conn.close()


if __name__ == "__main__":
    main()
