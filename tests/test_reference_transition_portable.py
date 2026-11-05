"""Run the unchanged historical transfer assertions with portable path lookup."""
from pathlib import Path

from tests import test_reference_transition as historical


def test_reference_transfer_with_portable_journal_paths(monkeypatch):
    # The publication pins the original test's source bytes. Adapt only its
    # repository-relative Windows path resolution; every original assertion and
    # expected journal/report/timing digest still runs unchanged.
    monkeypatch.setattr(historical, 'Path', lambda value: Path(str(value).replace('\\', '/')))
    historical.test_nonconfidence_transfer_preserves_authentic_report_timing_and_observation()
