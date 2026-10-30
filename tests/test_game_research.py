"""Synthetic implementation checks only. No empirical scientific defaults/results."""

import json
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

import pytest

from app.game.models import PlanningContext, canonical_json
from app.game.offline.evaluation import bind_evaluation, fit_policy, export_artifact, summarize
from app.game.offline.records import DatasetManifest
from app.game.research.specification import ExperimentSpecification
from app.game.research.readiness import check_readiness, EVIDENCE_FAILURES
from app.game.research.comparison import (FrozenComparison, prepare_comparison, score_development_pilot,
                                          score_frozen_final, deterministic_id)
from app.game.research.uncertainty import bootstrap_frozen_final
from tests.test_game_offline import attempt, fixture, report, unbind

REVISION = subprocess.check_output(
    ["git", "rev-parse", "HEAD"],
    text=True,
).strip()


def study(*, labels=("arithmetic",), names=("a",), budget=None):
    context, manifest, contract, attacks = fixture(labels=labels, names=names)
    if budget is not None:
        from app.game.offline.evaluation import bind_evaluation
        from app.game.offline.replay import category_id
        context = PlanningContext(**{**unbind(context).model_dump(), "budget": budget})
        data = manifest.model_dump()
        for part in data["partitions"]:
            for example in part["examples"]:
                example["planning_category"] = category_id(context)
        manifest = DatasetManifest(**data)
        context = bind_evaluation(context, manifest, contract, attacks)
    return ExperimentSpecification(version="game_research_v1", study_id="SYNTHETIC_TEST_ONLY",
        configuration_version="synthetic-v1", code_revision=REVISION, setting_role="primary",
        primary_specification_id=None, scientific_scope="synthetic arithmetic correctness only",
        primary_outcomes=("mean_loss", "worst_case_expected_loss"),
        sensitivity_plan=("SYNTHETIC: declared threshold sensitivity, not executed",),
        matched_coverage_plan="SYNTHETIC: dev-only threshold grid then rebuild bindings",
        final_test_custody_and_freeze_protocol="SYNTHETIC: independent freeze witness",
        datasets=tuple(dict(role=p.role, dataset_id=p.dataset_id, version="synthetic-v1", source="synthetic fixture",
            independent_label_provenance="synthetic independent truth", declared_label_sources=("fixture-independent-label",),
            grouping_protocol="synthetic related questions share split_identity") for p in manifest.partitions),
        recording=dict(execution_configuration_id=contract.execution_configuration_id,
            model_fingerprints=(("not_applicable", "synthetic double"),), corpus_fingerprints=(("not_applicable", "no retrieval"),),
            prompt_and_adapter_fingerprints=(("synthetic", "generic_v1"),), collection_protocol="complete_team_independent_v1"),
        context=context, manifest=manifest, contract=contract, attacks=attacks, unknown_dependency_treatment="shared_unknown",
        greedy_aggregation="dependency_group",
        policy_sampling_seeds=(22, 11), policy_sampling_repetitions=2,
        uncertainty=dict(method="paired_split_identity_cluster_percentile_v1", resamples=12, confidence_level=.9, seed=23),
        optimizer_tolerance=1e-8)


def frozen_study(spec):
    policy, dev = fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)
    artifact = export_artifact(policy, spec.context, spec.manifest, spec.contract, spec.attacks,
                               applicable_domain=spec.context.plan.domain)
    return prepare_comparison(spec, dev, artifact, freeze_record="SYNTHETIC freeze only", actual_code_revision=REVISION), dev, artifact


def test_unresolved_template_and_numeric_rejection():
    data = json.loads(Path("docs/game_research_spec.template.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError):
        ExperimentSpecification(**data)
    for update in ({"optimizer_tolerance": float("nan")}, {"policy_sampling_repetitions": True},
                   {"policy_sampling_seeds": (-1,)}, {"setting_role": "sensitivity"}, {"datasets": ()}):
        with pytest.raises(ValueError):
            ExperimentSpecification(**{**study().model_dump(), **update})


def test_readiness_lists_actions_and_baseline_without_scoring(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry-run attempted evaluation/dispatch/fitting")
    import app.game.offline.evaluation as evaluation
    import app.game.offline.replay as replay_module
    import app.game.solver as solver
    monkeypatch.setattr(evaluation, "construct_payoffs", forbidden)
    monkeypatch.setattr(evaluation, "evaluate_final_test", forbidden)
    monkeypatch.setattr(replay_module, "replay", forbidden)
    monkeypatch.setattr(solver, "linprog", forbidden)
    spec = study()
    report = check_readiness(spec, actual_code_revision=REVISION)
    assert report.ready and len(report.strategies) == 2 and len(report.attacks) == 5
    assert report.greedy_strategy_id and report.evidence_kind == "synthetic_test_fixture"
    assert not check_readiness(spec, actual_code_revision="0" * 40).ready


def test_directional_rule_generic_adapter_reproduction_and_structured_blockers(monkeypatch):
    spec = study(names=("rule",))
    # The original discrepancy: the offline fitter rejects this declared mapping.
    with pytest.raises(ValueError, match="unsupported verifier-aware transformation adapter"):
        fit_policy(spec.context, spec.manifest, spec.contract, spec.attacks)

    def forbidden(*args, **kwargs):
        raise AssertionError("readiness attempted replay/scoring/optimization/dispatch")

    import app.game.offline.attacks as attacks_module
    import app.game.offline.evaluation as evaluation
    import app.game.offline.replay as replay_module
    import app.game.solver as solver
    monkeypatch.setattr(attacks_module, "transform", forbidden)
    monkeypatch.setattr(evaluation, "construct_payoffs", forbidden)
    monkeypatch.setattr(replay_module, "replay", forbidden)
    monkeypatch.setattr(solver, "linprog", forbidden)
    checked = check_readiness(spec, actual_code_revision=REVISION)
    assert not checked.ready
    assert [b.model_dump() for b in checked.adapter_blockers] == [dict(
        code="incompatible_attack_adapter", partition=role, example_id=role,
        verifier_name="rule", adapter="generic_v1", expected_adapter="rule_v1")
        for role in ("development", "final_test")]


@pytest.mark.parametrize("name,adapter", [
    ("rule", "rule_v1"), ("evidence", "evidence_v1"),
    ("confidence", "confidence_v1"), ("semantic", "semantic_v1"), ("custom", "generic_v1"),
])
def test_shared_adapter_validation_matches_existing_directional_transformations(name, adapter):
    from app.game.offline.attacks import adapter_incompatibility, enumerate_attacks, transform
    row = report(name)
    if name == "evidence":
        row = report(name, metadata={"decision": "SUPPORT", "nli_label": "entailment",
            "supporting": [{"nli_label": "entailment", "document": "synthetic"}], "contradicting": [],
            "claim_decisions": [{"decision": "SUPPORT"}]})
    elif name == "confidence":
        row = report(name, metadata={"judgments": ["support", "support"], "majority_label": "support"})
    context, _, contract, specification = fixture(names=(name,))
    recording = attempt(name, row=row, adapter=adapter)
    original = recording.model_dump_json()
    assert adapter_incompatibility(recording) is None
    for action in enumerate_attacks(context.dependencies, specification):
        transform(recording, action, specification)
    assert recording.model_dump_json() == original
    wrong = "generic_v1" if adapter != "generic_v1" else "rule_v1"
    invalid = recording.model_copy(update={"adapter": wrong})
    mismatch = adapter_incompatibility(invalid)
    assert mismatch.model_dump() == dict(verifier_name=name, adapter=wrong, expected_adapter=adapter)
    with pytest.raises(ValueError, match="unsupported verifier-aware transformation adapter"):
        transform(invalid, enumerate_attacks(context.dependencies, specification)[1], specification)


@pytest.mark.parametrize("name,adapter", [
    ("rule", "rule_v1"), ("evidence", "evidence_v1"),
    ("confidence", "confidence_v1"), ("semantic", "semantic_v1"),
])
def test_readiness_accepts_valid_builtin_mapping_without_bypassing_evidence_gate(name, adapter):
    spec = study(names=(name,))
    data = spec.model_dump()
    for part in data["manifest"]["partitions"]:
        for example in part["examples"]:
            for recording in example["attempts"]:
                recording["adapter"] = adapter
    manifest = DatasetManifest(**data["manifest"])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    updated = ExperimentSpecification(**{**data, "context": context, "manifest": manifest})
    checked = check_readiness(updated, actual_code_revision=REVISION)
    assert checked.adapter_blockers == ()
    assert checked.ready == (name != "evidence")


@pytest.mark.parametrize("state", ["abstention", "unavailable", "failed"])
@pytest.mark.parametrize("name", ["rule", "evidence", "confidence", "semantic"])
def test_nondirectional_reports_retain_adapter_mapping_exemption(name, state):
    from app.game.offline.attacks import adapter_incompatibility, enumerate_attacks, transform
    context, _, _, specification = fixture(names=(name,))
    recording = attempt(name, state=state, adapter="generic_v1")
    assert adapter_incompatibility(recording) is None
    actions = enumerate_attacks(context.dependencies, specification)
    for action in actions[1:4]:
        changed, audit = transform(recording, action, specification)
        assert changed == recording
        assert audit.reason == ("preserved_abstention" if state == "abstention" else "no_returned_report")
    # All-nondirectional study remains a valid input, not an invented decisive result.
    spec = study(names=(name,))
    data = spec.model_dump()
    for part in data["manifest"]["partitions"]:
        for example in part["examples"]:
            for item in example["attempts"]:
                item.update(state=recording.state, report_json=recording.report_json)
    manifest = DatasetManifest(**data["manifest"])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    checked = check_readiness(ExperimentSpecification(**{**data, "context": context, "manifest": manifest}),
                              actual_code_revision=REVISION)
    assert checked.ready and checked.adapter_blockers == ()


@pytest.mark.parametrize("labels,unsupported,evidence", [
    (("arithmetic",), (), False), (("direct_fact",), (), True),
    (("semantic",), ("semantic",), False), (("logical_rule",), ("logical_rule",), False),
    (("evidence_retrieval",), ("evidence_retrieval",), True),
])
def test_coverage_and_evidence_gates(labels, unsupported, evidence):
    result = check_readiness(study(labels=labels), actual_code_revision=REVISION)
    assert result.unsupported_achieved == unsupported
    assert any("evidence_contract_failures" in b for b in result.blockers) == evidence
    assert result.ready == (not unsupported and not evidence)
    assert result.evidence_failures == EVIDENCE_FAILURES and len(EVIDENCE_FAILURES) == 3


def test_split_leakage_independent_labels_and_missing_recording_rejection():
    spec = study()
    for field, value in (("split_identity", "history"), ("answer_is_correct", None), ("label_method", "consensus")):
        data = spec.model_dump()
        part = next(p for p in data["manifest"]["partitions"] if p["role"] == "development")
        part["examples"][0][field] = value
        with pytest.raises(ValueError):
            ExperimentSpecification(**data)
    data = spec.model_dump()
    attempt = next(p for p in data["manifest"]["partitions"] if p["role"] == "development")["examples"][0]["attempts"][0]
    attempt.update(state="missing", report_json=None)
    result = check_readiness(ExperimentSpecification(**data), actual_code_revision=REVISION)
    assert not result.ready and any("incomplete_candidate_recordings" in b for b in result.blockers)


def test_greedy_cannot_relax_budget_or_minimum():
    spec = study(names=("a", "b"), budget=1.)
    # Make the actual captured greedy team exceed budget without altering feasible subsets.
    data = spec.model_dump()
    selection = asdict(spec.context.plan)
    selection["initial_selected"] = ["a", "b"]
    data["context"]["selection_json"] = canonical_json(selection)
    # initial_selected is deliberately excluded from game semantic compatibility.
    spec = ExperimentSpecification(**data)
    report = check_readiness(spec, actual_code_revision=REVISION)
    assert report.strategies and not report.ready
    assert "captured_coverage_aware_greedy_team_is_not_feasible" in report.blockers


def test_stable_detached_specification_identity():
    spec = study()
    data = spec.model_dump()
    data["datasets"] = tuple(reversed(data["datasets"]))
    data["policy_sampling_seeds"] = [11, 22]
    same = ExperimentSpecification(**data)
    assert same.specification_id == spec.specification_id
    data["recording"]["model_fingerprints"] = (("other", "changed"),)
    assert ExperimentSpecification(**data).specification_id != spec.specification_id
    assert same.specification_id == spec.specification_id


def test_fingerprint_order_canonicalization_and_explicit_unknown_treatment():
    data = study().model_dump()
    data["recording"]["model_fingerprints"] = (("second", "synthetic-2"), ("first", "synthetic-1"))
    first = ExperimentSpecification(**data)
    data["recording"]["model_fingerprints"] = tuple(reversed(data["recording"]["model_fingerprints"]))
    assert ExperimentSpecification(**data).specification_id == first.specification_id
    data.pop("unknown_dependency_treatment")
    with pytest.raises(ValueError):
        ExperimentSpecification(**data)


def test_comparison_metadata_complete_denominators_and_exact_mixtures():
    spec = study(names=("a", "b"))
    frozen, _, _ = frozen_study(spec)
    assert FrozenComparison.model_validate_json(frozen.model_dump_json()) == frozen
    result = score_development_pilot(spec, frozen, actual_code_revision=REVISION)
    assert result.run_kind == "development_pilot"
    from app.game.offline.replay import replay
    from app.game.research.readiness import check_readiness
    actions = check_readiness(spec, actual_code_revision=REVISION).attacks
    for policy, method in zip(frozen.policies, result.methods):
        if policy.method.startswith("fixed_"):
            assert {s.aggregation for s in policy.development_matrix.strategy_definitions} == {policy.method.removeprefix("fixed_")}
            assert policy.optimality_claim == "declared_action_set_numerical_certificate"
        for action, (attack_id, metric) in zip(actions, method.attack_metrics):
            expected = summarize(tuple((replay(spec.context, strategy, action, spec.attacks, spec.contract, e),
                dict(policy.probabilities)[strategy.strategy_id])
                for strategy in policy.development_matrix.strategy_definitions
                for e in spec.manifest.partition("development").examples), spec.context.loss_configuration)
            assert metric == expected and attack_id == action.attack_id
            assert metric.examples == 1
            assert metric.correct_accept + metric.correct_reject + metric.false_accept + metric.false_reject + metric.uncertain == pytest.approx(1.)
        assert method.worst_case_expected_loss == max(m.mean_loss for _, m in method.attack_metrics)
        assert method.clean_attack_id == actions[0].attack_id
    uniform = next(m for m in result.methods if m.method == "uniform")
    clean = uniform.attack_metrics[0][1]
    assert clean.estimated_resource_cost == pytest.approx(4. / 3.)
    assert clean.mean_loss == pytest.approx(.1 * 4. / 3.)
    rejection = uniform.attack_metrics[2][1]
    assert rejection.false_reject == pytest.approx(1.) and rejection.decision_coverage == pytest.approx(1.)
    assert rejection.mean_loss == pytest.approx(1. + .1 * 4. / 3.)


def test_development_only_selection_and_final_no_optimizer(monkeypatch):
    spec = study()
    frozen, dev, artifact = frozen_study(spec)
    with pytest.raises(ValueError, match="development"):
        prepare_comparison(spec, dev.model_copy(update={"role": "final_test"}), artifact,
                           freeze_record="invalid", actual_code_revision=REVISION)
    def forbidden(*args, **kwargs):
        raise AssertionError("final-test attempted optimization/development selection")
    import app.game.research.comparison as comparison
    import app.game.solver as solver
    monkeypatch.setattr(comparison, "solve_minimax", forbidden)
    monkeypatch.setattr(comparison, "construct_payoffs", forbidden)
    monkeypatch.setattr(solver, "linprog", forbidden)
    result = score_frozen_final(spec, frozen, actual_code_revision=REVISION)
    assert result.run_kind == "frozen_final" and result.comparison_id == frozen.comparison_id
    changed = spec.model_dump()
    changed["contract"]["threshold"] = .6
    with pytest.raises(ValueError):
        score_frozen_final(ExperimentSpecification(**changed), frozen, actual_code_revision=REVISION)


def test_matrix_or_baseline_tampering_and_incompatible_artifact_reject():
    spec = study()
    frozen, dev, artifact = frozen_study(spec)
    for method, field, value in (("fixed_dependency_group", "optimality_claim", "full_game_numerical_certificate"),
                                 ("uniform", "probabilities", (("wrong", 1.),))):
        data = frozen.model_dump()
        next(p for p in data["policies"] if p["method"] == method)[field] = value
        with pytest.raises(ValueError):
            FrozenComparison(**data)
    with pytest.raises(ValueError, match="development evaluation"):
        prepare_comparison(spec, dev.model_copy(update={"outcomes": ()}), artifact,
                           freeze_record="bad", actual_code_revision=REVISION)


def test_best_deterministic_uses_worst_column_and_stable_ties():
    from app.game.models import PayoffMatrix
    matrix = PayoffMatrix(strategy_ids=("b", "a", "c"), attack_ids=("clean", "attack"),
        values=((0., 10.), (1., 2.), (1., 2.)), compatibility_id="synthetic")
    assert deterministic_id(matrix, clean=False) == 1
    assert deterministic_id(matrix, clean=True) == 0


def test_manual_partial_coverage_mixture_uses_all_examples_and_failure_costs():
    spec = study(names=("a", "b"))
    data = spec.model_dump()
    for part in data["manifest"]["partitions"]:
        if part["role"] == "history":
            continue
        first = part["examples"][0]
        next(a for a in first["attempts"] if a["verifier_name"] == "b").update(state="failed", report_json=None)
        second = json.loads(json.dumps(first))
        suffix = part["role"] + "-incorrect"
        second.update(example_id=suffix, question_id=suffix, question=suffix, validation_id=suffix,
                      split_identity=suffix, answer_is_correct=False)
        for a in second["attempts"]:
            a["execution_id"] = suffix
        part["examples"] = (first, second)
    manifest = DatasetManifest(**data["manifest"])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    spec = ExperimentSpecification(**{**data, "context": context, "manifest": manifest})
    frozen, _, _ = frozen_study(spec)
    result = score_frozen_final(spec, frozen, actual_code_revision=REVISION)
    uniform = next(m for m in result.methods if m.method == "uniform")
    clean = uniform.attack_metrics[0][1]
    assert clean.examples == 2
    assert clean.correct_accept == pytest.approx(1. / 3.)
    assert clean.false_accept == pytest.approx(1. / 3.)
    assert clean.uncertain == pytest.approx(4. / 3.)
    assert clean.decision_coverage == pytest.approx(1. / 3.)
    assert clean.selective_risk == pytest.approx(.5)
    assert clean.estimated_resource_cost == pytest.approx(4. / 3.)
    assert clean.mean_loss == pytest.approx(1. / 6. + .2 * 2. / 3. + .1 * 4. / 3.)
    assert uniform.worst_case_expected_loss == pytest.approx(clean.mean_loss)


def test_final_labels_never_influence_development_baseline_choice():
    spec = study(names=("a", "b"))
    frozen, _, _ = frozen_study(spec)
    data = spec.model_dump()
    final = next(p for p in data["manifest"]["partitions"] if p["role"] == "final_test")
    final["examples"][0]["answer_is_correct"] = False
    manifest = DatasetManifest(**data["manifest"])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    other = ExperimentSpecification(**{**data, "context": context, "manifest": manifest})
    refrozen, _, _ = frozen_study(other)
    assert frozen.specification_id != refrozen.specification_id
    assert [(p.method, p.probabilities) for p in frozen.policies] == [(p.method, p.probabilities) for p in refrozen.policies]


def test_same_question_cannot_be_counted_as_independent_clusters():
    spec = study()
    data = spec.model_dump()
    final = next(p for p in data["manifest"]["partitions"] if p["role"] == "final_test")
    row = json.loads(json.dumps(final["examples"][0]))
    row.update(example_id="related", validation_id="related", split_identity="wrong_independent_group", answer="other answer")
    for a in row["attempts"]:
        a["execution_id"] = "related"
    final["examples"] = (*final["examples"], row)
    with pytest.raises(ValueError, match="share one split identity"):
        ExperimentSpecification(**data)


def test_single_cluster_does_not_invent_uncertainty():
    spec = study()
    frozen, _, _ = frozen_study(spec)
    report = bootstrap_frozen_final(spec, frozen, actual_code_revision=REVISION)
    assert report.cluster_count == 1 and not report.intervals and report.reason


def test_cluster_bootstrap_is_paired_reproducible_and_keeps_related_examples():
    from app.game.offline.evaluation import bind_evaluation
    from app.game.offline.replay import category_id
    spec = study()
    data = spec.model_dump()
    final = next(p for p in data["manifest"]["partitions"] if p["role"] == "final_test")
    original = final["examples"][0]
    rows = [original]
    for suffix, group in (("related", "final_test"), ("independent", "other_group")):
        row = json.loads(json.dumps(original))
        row.update(example_id=suffix, question_id=suffix, question=suffix, validation_id=suffix, split_identity=group)
        for a in row["attempts"]:
            a["execution_id"] = suffix
        rows.append(row)
    final["examples"] = rows
    manifest = DatasetManifest(**data["manifest"])
    context = bind_evaluation(unbind(spec.context), manifest, spec.contract, spec.attacks)
    data.update(context=context, manifest=manifest)
    spec = ExperimentSpecification(**data)
    frozen, _, _ = frozen_study(spec)
    report = bootstrap_frozen_final(spec, frozen, actual_code_revision=REVISION)
    assert report.cluster_count == 2 and report == bootstrap_frozen_final(spec, frozen, actual_code_revision=REVISION)
    assert any(i.method.startswith("full_minimax-minus-") for i in report.intervals)
    assert all(i.lower is None and i.defined_resamples == 0 for i in report.intervals
               if i.metric == "selective_risk" and i.attack_id == frozen.full_artifact.policy.matrix.attack_ids[-1])


def test_cli_unresolved_template_is_read_only_and_reports_digests():
    before = subprocess.check_output(["git", "status", "--porcelain=v1"])
    result = subprocess.run([sys.executable, "-m", "app.game.research", "readiness",
                             "docs/game_research_spec.template.json"], capture_output=True, text=True)
    assert result.returncode == 2, result.stderr
    report = json.loads(result.stdout)
    assert report["ready"] is False and report["command"] == "readiness_only"
    assert report["input_digest"] and report["research_source_digest"] and report["code_revision"] == REVISION
    assert subprocess.check_output(["git", "status", "--porcelain=v1"]) == before


def test_fresh_readiness_import_does_not_import_runtime_or_construct_models(tmp_path):
    # Existing selector package imports verifier modules eagerly. Guard constructors
    # and methods instead of pretending those existing imports are lazy.
    code = r'''
import sys
import json
from unittest.mock import patch
from pathlib import Path
from app.verifiers.semantic_verifier import SemanticVerifier
from app.verifiers.evidence_verifier import EvidenceVerifier
from app.verifiers.confidence_verifier import ConfidenceVerifier
from app.verifiers.rule_verifier import RuleVerifier
from contextlib import ExitStack

with ExitStack() as stack:
    for verifier in (SemanticVerifier, EvidenceVerifier, ConfidenceVerifier, RuleVerifier):
        stack.enter_context(patch.object(verifier, '__init__', side_effect=AssertionError('model construction')))
        stack.enter_context(patch.object(verifier, 'verify', side_effect=AssertionError('dispatch')))
    from app.game.research.specification import ExperimentSpecification
    from app.game.research.readiness import check_readiness
    spec = ExperimentSpecification.model_validate_json(Path(sys.argv[1]).read_text(encoding='utf-8'))
    before = spec.model_dump_json()
    assert check_readiness(spec, actual_code_revision=spec.code_revision).ready
assert spec.model_dump_json() == before
assert 'app.game.research.comparison' not in sys.modules
assert 'app.game.execution' not in sys.modules
assert 'app.orchestration.validation_orchestrator' not in sys.modules
assert not any(name.startswith(('app.db', 'app.database')) for name in sys.modules)
'''
    path = tmp_path / "synthetic-study.json"
    path.write_text(study().model_dump_json(), encoding="utf-8")
    result = subprocess.run([sys.executable, "-c", code, str(path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
