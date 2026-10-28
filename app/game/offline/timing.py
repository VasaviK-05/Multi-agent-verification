"""Shared attempt timing, independent of orchestration and persistence imports."""
import time

from app.verifiers.base_verifier import BaseVerifier
from app.models.schemas import VerificationResult


class TimedVerifier(BaseVerifier):
    """Measure the existing verify call; preserve its result and exception."""
    def __init__(self, inner, durations_ms, *, measurement_metadata=None, measurements=None):
        if (measurement_metadata is None) != (measurements is None):
            raise ValueError('measurement metadata and output list must be supplied together')
        self._inner = inner
        self._durations_ms = durations_ms
        self._measurement_metadata = measurement_metadata
        self._measurements = measurements

    @property
    def name(self):
        return self._inner.name

    def verify(self, question, answer, context=None) -> VerificationResult:
        started = time.perf_counter()
        status = 'interrupted'
        try:
            result = self._inner.verify(question, answer, context)
            status = 'returned'
            return result
        except TimeoutError:
            status = 'timeout'
            raise
        except Exception:
            status = 'failure'
            raise
        finally:
            duration = (time.perf_counter() - started) * 1000.0
            self._durations_ms.append(duration)
            if self._measurements is not None:
                self._measurements.append({**self._measurement_metadata,
                    'verifier_name': self.name, 'duration_ms': duration, 'status': status})
