"""Synthetic Experiment 3 runner.

The original source file is not in the tree. A preserved bytecode copy is at
``_experiment3_preserved.pyc``. That bytecode imports
``controlled_two_group_registry`` and ``shared_unknown_registry`` from
``app.game.dependencies``, and those names are not in the current module.
The bytecode is therefore not executed. This file does not invent the missing
registry or any Development recording.
"""

from __future__ import annotations

from pathlib import Path

PRESERVED_BYTECODE = Path(__file__).with_name("_experiment3_preserved.pyc")


class Experiment3ImplementationUnavailable(RuntimeError):
    """The synthetic runner cannot be loaded from the preserved bytecode."""


def assert_claim_allowed(*, claim: str, complete_development_attempts: int) -> None:
    """Refuse an empirical claim when no complete Development attempt exists."""
    if claim not in {"synthetic", "empirical"}:
        raise ValueError("claim must be synthetic or empirical")
    if not isinstance(complete_development_attempts, int) or complete_development_attempts < 0:
        raise ValueError("complete Development attempt count must be a nonnegative integer")
    if claim == "empirical" and complete_development_attempts == 0:
        raise ValueError("empirical Experiment 3 claim blocked: complete Development attempts are zero")


def _unavailable(*_args, **_kwargs):
    raise Experiment3ImplementationUnavailable(
        "Experiment 3 synthetic runner source is missing, and the preserved bytecode cannot load because the dependency helpers it imports are absent."
    )


write_synthetic_outputs = _unavailable
render_synthetic_results = _unavailable
synthetic_specification = _unavailable
scenario_observations = _unavailable
scenario_attempts = _unavailable
