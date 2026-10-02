"""Import-order checks in a fresh interpreter.

Pytest has already imported this repository, so these tests start a new
process and do not reuse that module table.
"""

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(statement: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", statement],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_reputation_imports_before_decision():
    completed = _fresh_import(
        "from app.reputation.reputation_manager import ReputationManager"
    )
    assert completed.returncode == 0, completed.stderr


def test_decision_imports_before_reputation():
    completed = _fresh_import("from app.decision.decision_engine import DecisionEngine")
    assert completed.returncode == 0, completed.stderr


def test_orchestrator_imports_first():
    completed = _fresh_import(
        "from app.orchestration.validation_orchestrator import ValidationOrchestrator"
    )
    assert completed.returncode == 0, completed.stderr
