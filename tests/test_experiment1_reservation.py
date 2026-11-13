"""Synthetic checks for reservation-based Experiment 1 comparison. No empirical claims."""

import pytest

from app.game.offline.evaluation import bind_evaluation, export_artifact, fit_policy
from app.game.offline.records import FinalTestReservation, Partition, ReservedExample, TrainingManifest
from app.game.research.comparison import (prepare_comparison, role_examples, score_development_pilot,
                                          score_frozen_final)
from app.game.research.readiness import check_readiness
from app.game.research.specification import ExperimentSpecification
from app.game.research.uncertainty import bootstrap_development_pilot, bootstrap_frozen_final
from tests.test_game_offline import unbind
from tests.test_game_research import REVISION, frozen_study, study


def reserved_study(names=("a", "b")):
    legacy = study(names=names)
    final = legacy.manifest.partition("final_test")
    reservation = FinalTestReservation(version="final_test_reservation_v1", role="final_test",
        dataset_id=final.dataset_id, custody_record="SYNTHETIC external witness only",
        examples=tuple(ReservedExample.from_example(e) for e in final.examples))
    training = TrainingManifest(version="game_training_manifest_v1", evidence_kind=legacy.manifest.evidence_kind,
        partitions=tuple(p for p in legacy.manifest.partitions if p.role != "final_test"),
        final_test_reservation=reservation)
    context = bind_evaluation(unbind(legacy.context), training, legacy.contract, legacy.attacks)
    spec = ExperimentSpecification(**{**legacy.model_dump(), "context": context, "manifest": training})
    return spec, final, legacy


def freeze(spec):
    policy, dev = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)
    artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks,
                               applicable_domain=spec.context.plan.domain)
    return prepare_comparison(spec, dev, artifact, freeze_record="SYNTHETIC freeze only",
                              actual_code_revision=REVISION)


def test_specification_holds_reservation_without_final_outcomes():
    spec, _, _ = reserved_study()
    assert isinstance(spec.manifest, TrainingManifest)
    assert not hasattr(spec.manifest.partition("final_test").examples[0], "answer_is_correct")
    assert check_readiness(spec, actual_code_revision=REVISION).ready


def test_development_pipeline_runs_without_any_final_payload():
    spec, _, _ = reserved_study()
    frozen = freeze(spec)
    result = score_development_pilot(spec, frozen, actual_code_revision=REVISION)
    assert result.run_kind == "development_pilot" and result.reservation_id is None
    assert [m.method for m in result.methods] == [p.method for p in frozen.policies]
    assert bootstrap_development_pilot(spec, frozen, actual_code_revision=REVISION).run_kind == "development_pilot"
    with pytest.raises(ValueError, match="never accepts"):
        role_examples(spec, "development", spec.manifest.partition("development"))


def test_reserved_final_requires_matching_released_payload():
    spec, final, _ = reserved_study()
    frozen = freeze(spec)
    with pytest.raises(ValueError, match="separately released payload"):
        score_frozen_final(spec, frozen, actual_code_revision=REVISION)
    with pytest.raises(ValueError, match="separately released payload"):
        bootstrap_frozen_final(spec, frozen, actual_code_revision=REVISION)
    data = final.model_dump()
    data["examples"][0]["question"] = "tampered question"
    with pytest.raises(ValueError, match="frozen reservation"):
        score_frozen_final(spec, frozen, actual_code_revision=REVISION, final_partition=Partition(**data))
    result = score_frozen_final(spec, frozen, actual_code_revision=REVISION, final_partition=final)
    assert result.run_kind == "frozen_final"
    assert result.reservation_id == spec.manifest.final_test_reservation.reservation_id
    assert result.final_payload_id


def test_reserved_and_legacy_final_metrics_agree():
    spec, final, legacy = reserved_study()
    reserved = score_frozen_final(spec, freeze(spec), actual_code_revision=REVISION, final_partition=final)
    frozen, _, _ = frozen_study(legacy)
    bound = score_frozen_final(legacy, frozen, actual_code_revision=REVISION)
    assert [(m.method, m.attack_metrics) for m in reserved.methods] == [(m.method, m.attack_metrics) for m in bound.methods]
    with pytest.raises(ValueError, match="already binds"):
        score_frozen_final(legacy, frozen, actual_code_revision=REVISION, final_partition=final)


def test_empirical_study_with_embedded_final_labels_is_blocked():
    legacy = study()
    data = legacy.model_dump()
    data["manifest"]["evidence_kind"] = "empirical"
    report = check_readiness(ExperimentSpecification(**data), actual_code_revision=REVISION)
    assert "empirical_study_requires_final_test_reservation" in report.blockers
    spec, _, _ = reserved_study()
    data = spec.model_dump()
    data["manifest"]["evidence_kind"] = "empirical"
    report = check_readiness(ExperimentSpecification(**data), actual_code_revision=REVISION)
    assert "empirical_study_requires_final_test_reservation" not in report.blockers
    assert not report.ready
