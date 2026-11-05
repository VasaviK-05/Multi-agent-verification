"""Recorded Development loss regression; no model construction or inference."""
import math

from scripts.verify_compound_reference_fits import ROOT, compound_clean_metrics, read


def test_frozen_compound_clean_loss_counts_and_penalty():
    folder = ROOT / 'compound-85/candidate'
    metrics = compound_clean_metrics(read(folder / 'policy.json'), read(folder / 'development-outcomes.json'))
    assert metrics['examples'] == 48
    assert (metrics['correct_accept'], metrics['correct_reject']) == (12, 31)
    assert (metrics['false_accept'], metrics['false_reject'], metrics['uncertain']) == (0, 0, 5)
    assert metrics['uncertainty_penalty'] == .2
    assert math.isclose(metrics['decision_coverage'], 43 / 48, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(metrics['clean_validation_loss'], (5 / 48) * .2, rel_tol=0, abs_tol=1e-12)
