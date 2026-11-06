
"""Heartbeat management for leased validation executions."""

import threading
from uuid import UUID

from app.database.execution_journal_repository import renew_execution_lease


class ExecutionLeaseLostError(RuntimeError):
    """Raised when a worker no longer owns its execution lease."""


class ExecutionLeaseHeartbeat:
    def __init__(
        self,
        *,
        validation_id: str,
        lease_token: str,
        interval_seconds: int = 10,
        lease_seconds: int = 60,
    ):
        if (
            isinstance(interval_seconds, bool)
            or not isinstance(interval_seconds, int)
            or interval_seconds < 1
        ):
            raise ValueError("interval_seconds must be a positive integer")

        if (
            isinstance(lease_seconds, bool)
            or not isinstance(lease_seconds, int)
            or lease_seconds < 15
        ):
            raise ValueError("lease_seconds must be an integer >= 15")

        if interval_seconds * 3 >= lease_seconds:
            raise ValueError(
                "interval_seconds must be less than one-third of lease_seconds"
            )

        self.validation_id = str(UUID(str(validation_id)))
        self.lease_token = str(UUID(str(lease_token)))
        self.interval_seconds = interval_seconds
        self.lease_seconds = lease_seconds

        self._stop_event = threading.Event()
        self._lost_event = threading.Event()
        self._start_lock = threading.Lock()
        self._started = False

        self._thread = threading.Thread(
            target=self._run,
            name=f"lease-heartbeat-{self.validation_id}",
            daemon=True,
        )

    def start(self):
        """Start the heartbeat thread exactly once."""
        with self._start_lock:
            if self._started:
                raise RuntimeError("Lease heartbeat has already been started")

            self._started = True
            self._thread.start()

        return self

    def _run(self):
        """Periodically renew the execution lease."""
        while not self._stop_event.wait(self.interval_seconds):
            try:
                renewed = renew_execution_lease(
                    validation_id=self.validation_id,
                    lease_token=self.lease_token,
                    lease_seconds=self.lease_seconds,
                )

                if not renewed:
                    self._lost_event.set()
                    return

            except Exception:
                # Fail closed: never assume ownership after a failed renewal.
                self._lost_event.set()
                return

    def assert_owned(self):
        """Raise if the heartbeat has detected lease loss."""
        if self._lost_event.is_set():
            raise ExecutionLeaseLostError(
                f"Lease lost for execution {self.validation_id}"
            )

    def stop(self):
        """Stop and join the heartbeat thread."""
        self._stop_event.set()

        if self._started and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 2)
