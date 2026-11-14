"""Synthetic Experiment 4 prerequisite coverage; never initializes live resources."""
from copy import deepcopy
import pytest
from app.game.offline.calibration import MeasurementSetup
from app.game.offline.collection import (
    DiagnosticRecordingRequest,
    LazyVerifierPool,
    RecordingBundle,
    collect,
    collection_plan,
    completeness,
    require_collection_authorization,
    validate_recording_request,
)
from app.models.schemas import VerificationResult
from app.game.resource_provenance import ResourceManifest, VerifierResources
from tests.test_diagnostic_collection import experiment4_request_data


class NeverDispatchSemantic:
    name = "semantic"

    def __init__(self):
        self.calls = 0

    def verify(self, question, answer, context=None):
        self.calls += 1
        raise AssertionError("Semantic must not be dispatched without reference text")


class SyntheticObserver:
    def __init__(self, resources):
        self.resources = resources
        self.snapshot_calls = 0

    def snapshot(self):
        self.snapshot_calls += 1
        return self.resources


class SyntheticVerifier:
    def __init__(self, name):
        self.name = name
        self.calls = 0

    def verify(self, question, answer, context=None):
        self.calls += 1
        return VerificationResult(
            verifier_name=self.name,
            passed=True,
            score=1.0,
            metadata={"decision": "SUPPORT", "rule_kind": "factual", "rule": "synthetic"},
        )


def _four_example_request_data():
    data = experiment4_request_data()
    first, second = data["examples"]
    third, fourth = deepcopy(first), deepcopy(second)
    for example, candidate_number in ((third, 3), (fourth, 4)):
        example.update(
            example_id=f"candidate-{candidate_number}",
            source_candidate_id=f"source-candidate-{candidate_number}",
            run_id=f"run-{candidate_number}",
            split_identity="pair-2",
            question_id="question-2",
            question="Synthetic second-group question",
            answer="Synthetic answer",
            reference=None,
        )
    data["examples"] = [first, second, third, fourth]
    return data


def test_experiment4_semantic_missing_reference_is_unexecuted_unavailable():
    data = _four_example_request_data()
    request = validate_recording_request(data)

    assert request.collection_authorized is False
    assert len(request.examples) == 4
    assert len(request.candidates) == 4
    assert len(request.examples) * len(request.candidates) == 16

    plans = [collection_plan(request, example) for example in request.examples]
    for plan in plans:
        by_name = {candidate["verifier_name"]: candidate for candidate in plan["candidates"]}
        assert by_name["semantic"]["prerequisite_status"] == "missing_reference"
        assert by_name["semantic"]["exclusion_reason"] == "reference context is absent"
        assert by_name["semantic"]["eligible"] is False
        for name in ("confidence", "evidence", "rule"):
            assert by_name[name]["eligible"] is True
            assert by_name[name]["prerequisite_status"] == "unknown"

    # A zero-row bundle demonstrates that the 12 potentially eligible slots
    # have not been mistaken for executed calls or outcomes.
    setup = MeasurementSetup.model_validate(data["expected_setup"])
    untouched = RecordingBundle(request=request, observed_setup=setup, attempts=())
    summary = completeness(untouched)
    assert summary["expected_attempts"] == 16
    assert summary["recorded_outcomes"] == 0
    assert summary["executed_calls"] == 0

    # Exercise the repository collector only for the prerequisite-ineligible
    # Semantic roster. The fixture is an ordinary synthetic diagnostic request;
    # no Experiment 4 authorization flag is changed and no factory is involved.
    semantic_candidate = next(c for c in data["candidates"] if c["verifier_name"] == "semantic")
    semantic_resources = next(
        row for row in setup.resources.verifiers if row.verifier_name == "semantic"
    )
    resources = ResourceManifest(verifiers=(semantic_resources,))
    semantic_setup = MeasurementSetup.model_validate({
        **setup.model_dump(mode="json"),
        "resources": resources.model_dump(mode="json"),
    })
    diagnostic_data = deepcopy(data)
    diagnostic_data.update(
        version="offline_diagnostic_recording_v1",
        intended_use="smoke",
        study_approval=None,
        cache_contract="diagnostic_observation_only",
        execution_configuration_id=resources.manifest_id,
        expected_setup=semantic_setup.model_dump(mode="json"),
        candidates=[semantic_candidate],
    )
    diagnostic_data.pop("maximum_examples")
    diagnostic_data.pop("maximum_attempt_slots")
    for key in (
        "collection_authorized",
        "collection_authorization",
        "eligibility_manifest_id",
        "eligibility_manifest_sha256",
        "eligibility_manifest_file_sha256",
        "eligibility_candidate_roster_sha256",
        "eligibility_group_assignments_sha256",
        "development_source_manifest_sha256",
        "development_candidates_sha256",
        "development_verifier_inputs_sha256",
        "selected_subset_sha256",
    ):
        diagnostic_data.pop(key)
    for example in diagnostic_data["examples"]:
        example.pop("source_candidate_id")
        example.pop("benchmark")
        example["purpose"] = "calibration"
    diagnostic = DiagnosticRecordingRequest.model_validate(diagnostic_data)

    semantic = NeverDispatchSemantic()
    bundle = collect(
        diagnostic,
        [semantic],
        semantic_setup,
        SyntheticObserver(resources),
    )

    assert semantic.calls == 0
    assert len(bundle.attempts) == 4
    assert all(row.attempt.state == "unavailable" for row in bundle.attempts)
    assert all(not row.executed for row in bundle.attempts)
    assert all(row.attempt.report is None for row in bundle.attempts)
    assert all(row.duration_ms is None and row.timing_status is None for row in bundle.attempts)
    assert all(row.measurement is None for row in bundle.attempts)
    assert all("missing_reference" in row.planning_json for row in bundle.attempts)
    semantic_summary = completeness(bundle)
    assert semantic_summary["expected_attempts"] == 4
    assert semantic_summary["recorded_outcomes"] == 4
    assert semantic_summary["executed_calls"] == 0
    assert semantic_summary["complete"] is True


def test_lazy_synthetic_binding_never_constructs_prerequisite_ineligible_semantic():
    data = _four_example_request_data()
    e4_request = validate_recording_request(data)
    assert e4_request.collection_authorized is False
    with pytest.raises(ValueError, match="not authorized"):
        require_collection_authorization(e4_request)

    setup = MeasurementSetup.model_validate(data["expected_setup"])
    resources = setup.resources
    constructed = {}

    def build(name):
        verifier = SyntheticVerifier(name)
        constructed[name] = verifier
        return verifier

    constructors = {name: (lambda name=name: build(name)) for name in
                    ("confidence", "evidence", "rule")}

    def forbidden_semantic_constructor():
        pytest.fail("Semantic constructor called despite missing reference prerequisites")

    constructors["semantic"] = forbidden_semantic_constructor
    lazy_pool = LazyVerifierPool(constructors)
    assert lazy_pool.names == {"confidence", "evidence", "rule", "semantic"}
    assert constructed == {}

    # This is a synthetic collector-contract fixture, not the unauthorized E4
    # request and not an executable research binding. It retains its four names
    # and complete four-entry synthetic resource manifest for collector checks.
    diagnostic_data = deepcopy(data)
    diagnostic_data.update(
        version="offline_diagnostic_recording_v1",
        intended_use="smoke",
        study_approval=None,
        cache_contract="diagnostic_observation_only",
        execution_configuration_id=resources.manifest_id,
        expected_setup=setup.model_dump(mode="json"),
    )
    diagnostic_data.pop("maximum_examples")
    diagnostic_data.pop("maximum_attempt_slots")
    for key in (
        "collection_authorized",
        "collection_authorization",
        "eligibility_manifest_id",
        "eligibility_manifest_sha256",
        "eligibility_manifest_file_sha256",
        "eligibility_candidate_roster_sha256",
        "eligibility_group_assignments_sha256",
        "development_source_manifest_sha256",
        "development_candidates_sha256",
        "development_verifier_inputs_sha256",
        "selected_subset_sha256",
    ):
        diagnostic_data.pop(key)
    for example in diagnostic_data["examples"]:
        example.pop("source_candidate_id")
        example.pop("benchmark")
        example["purpose"] = "calibration"
    diagnostic = DiagnosticRecordingRequest.model_validate(diagnostic_data)

    observer = SyntheticObserver(resources)
    bundle = collect(diagnostic, lazy_pool, setup, observer)

    assert lazy_pool.names == {"confidence", "evidence", "rule", "semantic"}
    assert {row.verifier_name for row in resources.verifiers} == lazy_pool.names
    assert {row.verifier_name for row in bundle.observed_setup.resources.verifiers} == lazy_pool.names
    assert bundle.observed_setup.resources.manifest_id == resources.manifest_id
    assert set(constructed) == {"confidence", "evidence", "rule"}
    assert all(verifier.calls == 4 for verifier in constructed.values())
    semantic_rows = [row for row in bundle.attempts if row.candidate == "semantic"]
    assert len(semantic_rows) == 4
    assert all(row.attempt.state == "unavailable" and not row.executed for row in semantic_rows)
    assert all(row.attempt.report is None for row in semantic_rows)
    assert all(row.duration_ms is None and row.timing_status is None for row in semantic_rows)
    assert all(row.attempt.observed_resources_json is not None for row in semantic_rows)
    assert all(
        VerifierResources.model_validate_json(row.attempt.observed_resources_json) == next(
            resource for resource in resources.verifiers
            if resource.verifier_name == "semantic"
        )
        for row in semantic_rows
    )
    summary = completeness(bundle)
    assert summary["expected_attempts"] == 16
    assert summary["recorded_outcomes"] == 16
    assert summary["executed_calls"] == 12
    assert summary["complete"] is True
    assert observer.snapshot_calls > 0
    assert bundle.observed_setup.evidence_kind == "synthetic_test_fixture"
