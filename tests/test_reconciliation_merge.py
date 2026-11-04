"""Synthetic audit regression only; no native verifiers, services or persistence."""
import pytest
from app.game.models import PlanningContext
from app.models.schemas import ValidationRequest
from tests.test_game_runtime import runtime_fixture, persistence_boundaries


@pytest.mark.usefixtures('persistence_boundaries')
def test_runtime_keeps_selected_and_informative_minimum_audits_distinct(monkeypatch):
    # Isolate the audit roles using the existing synthetic complete-team fixture.
    # An opt-in contract can require more informative reports than the selected
    # floor; the existing synthetic fixture has a selected floor of one.
    monkeypatch.setattr(PlanningContext, 'minimum_informative_count', property(lambda self: 2))
    orchestrator, checkers, _, _ = runtime_fixture()
    response = orchestrator.validate(ValidationRequest(question='synthetic question', answer='synthetic answer'))
    audit = response.execution_audit
    assert audit['selection_status'] == 'selected'
    assert audit['minimum_selected_team_size'] == 1
    assert audit['minimum_contributors'] == 2
    assert sum(v.calls for v in checkers) == 2
    assert audit['termination'] == 'complete_selected_team'


def test_merge_overlay_preserves_pinned_resources_and_frozen_artifacts():
    from scripts.verify_reconciliation_merge import audit
    result = audit()
    assert result['unchanged_original_files'] == 484
    assert result['frozen_publication_artifacts_unchanged']
    assert result['resource_fingerprint_pins_unchanged']
    assert not result['canonical_whole_publication_unchanged']
