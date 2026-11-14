"""Synthetic contract tests for the inactive research_v1 recording binding."""

import json

import pytest

from app.game.offline.calibration import MeasurementSetup
from app.game.offline.collection import (
    DiagnosticRecordingRequest,
    Experiment4DiagnosticRecordingRequest,
    LazyVerifierPool,
    collect,
    require_collection_authorization,
    validate_recording_request,
)
from app.game.offline.research_v1_recording_binding import (
    CONFIG_ENV,
    ResearchLazyVerifierPool,
    ResearchRosterObserver,
    ResearchV1RecordingBinding,
    VERIFIER_ROSTER,
    make_lazy_verifier_pool,
    resolve_research_configuration,
)
from app.game.resource_provenance import ResourceManifest, VerifierResources
from app.models.schemas import VerificationResult
from app.benchmark.project_adapter import AdapterConfiguration
from tests.test_experiment4_applicability import _four_example_request_data


def _setup():
    required = {
        "semantic": ("implementation", "configuration", "model"),
        "evidence": ("implementation", "configuration", "model", "corpus", "index"),
        "rule": ("implementation", "configuration"),
        "confidence": ("implementation", "configuration", "model", "prompt", "service"),
    }
    resources = ResourceManifest(verifiers=tuple(
        dict(verifier_name=name, resources=tuple(
            dict(kind=kind, resource_id=f"{name}-{kind}", sha256="a" * 64)
            for kind in kinds))
        for name, kinds in required.items()))
    return MeasurementSetup(resources=resources, environment={"host": "SYNTHETIC"},
        dependency_versions={"python": "SYNTHETIC"}, code_revision="b" * 40,
        application_source_digest="c" * 64, evidence_kind="synthetic_test_fixture")


def _adapter_json():
    return AdapterConfiguration(embedding_snapshot=None, nli_snapshot=None,
        corpus_path="synthetic-corpus.json", index_dir="synthetic-index",
        index_receipt=None, service_observation=None).model_dump(mode="json")


def _binding_json(adapter_path):
    return ResearchV1RecordingBinding(version="research_v1_recording_binding_v1",
        binding_id="synthetic-binding-v1", dataset_id="research_v1_exploratory_v1",
        split="development", adapter_configuration_path=str(adapter_path)).model_dump(mode="json")


def _synthetic_generic_request():
    data = _four_example_request_data()
    setup = MeasurementSetup.model_validate(data["expected_setup"])
    data.update(version="offline_diagnostic_recording_v1", intended_use="smoke",
        study_approval=None, cache_contract="diagnostic_observation_only",
        execution_configuration_id=setup.resources.manifest_id,
        expected_setup=setup.model_dump(mode="json"), factory="synthetic:unused")
    data.pop("maximum_examples")
    data.pop("maximum_attempt_slots")
    for key in ("collection_authorized", "collection_authorization", "eligibility_manifest_id",
                "eligibility_manifest_sha256", "eligibility_manifest_file_sha256",
                "eligibility_candidate_roster_sha256", "eligibility_group_assignments_sha256",
                "development_source_manifest_sha256", "development_candidates_sha256",
                "development_verifier_inputs_sha256", "selected_subset_sha256"):
        data.pop(key)
    for example in data["examples"]:
        example.pop("source_candidate_id")
        example.pop("benchmark")
        example["purpose"] = "calibration"
    return DiagnosticRecordingRequest.model_validate(data), setup


def test_explicit_configuration_resolves_and_missing_configuration_fails_closed(tmp_path, monkeypatch):
    adapter_path = tmp_path / "selected-adapter.json"
    adapter_path.write_text(json.dumps(_adapter_json()), encoding="utf-8")
    binding_path = tmp_path / "research-binding.json"
    binding_path.write_text(json.dumps(_binding_json(adapter_path)), encoding="utf-8")

    monkeypatch.setenv(CONFIG_ENV, str(binding_path))
    binding, selected_path, adapter, selected_adapter_path = resolve_research_configuration()
    assert binding.binding_id == "synthetic-binding-v1"
    assert selected_path == binding_path.resolve()
    assert isinstance(adapter, AdapterConfiguration)
    assert selected_adapter_path == adapter_path.resolve()

    monkeypatch.delenv(CONFIG_ENV)
    with pytest.raises(ValueError, match="no fallback is used"):
        resolve_research_configuration()


def test_root_adapter_is_not_implicitly_selected(monkeypatch):
    monkeypatch.delenv(CONFIG_ENV, raising=False)
    # The repository root adapter may exist, but the resolver never consults it.
    with pytest.raises(ValueError, match=CONFIG_ENV):
        resolve_research_configuration()


def test_full_roster_names_and_single_fake_construction():
    constructed = []
    builders = {name: (lambda name=name: constructed.append(name) or type(
        "FakeVerifier", (), {"name": name})()) for name in VERIFIER_ROSTER}
    pool = make_lazy_verifier_pool(builders)
    assert isinstance(pool, LazyVerifierPool)
    assert pool.names == set(VERIFIER_ROSTER)
    assert constructed == []
    first = pool.get("rule")
    second = pool.get("rule")
    assert first.name == "rule"
    assert second is first
    assert constructed == ["rule"]


def test_static_roster_observer_needs_no_instances_or_service_calls():
    setup = _setup()
    service_calls = []
    active_calls = []
    def inspect(_configuration):
        return {"ready": True, "observed_setup": setup.model_dump(mode="json"),
                "inventory": {"service": {"saved": "synthetic-only"}}, "blockers": []}
    def service(_configuration):
        service_calls.append(True)
        raise AssertionError("static observer must not call a service")

    observer = ResearchRosterObserver(object(), setup, inspect_local=inspect,
        active_instance_attestor=lambda verifier, _config, _setup:
            active_calls.append(verifier.name) or True)
    observed = observer.snapshot()
    assert observed == setup.resources
    assert {row.verifier_name for row in observed.verifiers} == set(VERIFIER_ROSTER)
    assert observer.last_evidence == {
        "configuration": "DECLARED",
        "local_resources": "MATCH",
        "live_service": "NOT_CHECKED",
        "active_instances": "NOT_ATTESTED",
    }
    assert service_calls == []
    unconstructed = type("Fake", (), {"name": "semantic"})()
    with pytest.raises(ValueError, match="not constructed by this research lazy pool"):
        observer.attest_constructed_instance(unconstructed)
    pool = ResearchLazyVerifierPool(
        {name: (lambda name=name: type("Fake", (), {"name": name})())
         for name in VERIFIER_ROSTER}, observer)
    semantic = pool.get("semantic")
    assert observer.attest_constructed_instance(semantic) == "ATTESTED"
    assert active_calls == ["semantic"]


def test_observer_live_check_is_explicit_and_does_not_claim_full_readiness():
    setup = _setup()
    saved = {"service": "saved-observation"}
    calls = []
    def inspect(_configuration):
        return {"ready": True, "observed_setup": setup.model_dump(mode="json"),
                "inventory": saved, "blockers": []}
    def service(_configuration):
        calls.append(True)
        return saved["service"]

    observer = ResearchRosterObserver(object(), setup, inspect_local=inspect,
                                      observe_live_service=service)
    assert observer.snapshot() == setup.resources
    assert calls == [True]
    assert observer.last_evidence["live_service"] == "MATCH"
    assert "live_readiness" not in observer.last_evidence
    assert observer.last_evidence["active_instances"] == "NOT_ATTESTED"


def test_binding_requires_complete_roster_and_e4_stays_unauthorized():
    with pytest.raises(ValueError, match="complete four-verifier roster"):
        ResearchV1RecordingBinding.model_validate(dict(
            version="research_v1_recording_binding_v1", binding_id="incomplete",
            dataset_id="research_v1_exploratory_v1", split="development",
            adapter_configuration_path="synthetic.json",
            verifier_roster=("semantic", "semantic", "semantic", "semantic")))
    for field_name in ("dataset_id", "split"):
        description = ResearchV1RecordingBinding.model_fields[field_name].description
        assert "Declared binding target only" in description
        assert "not validated against the invoking RecordingRequest" in description

    e4 = validate_recording_request(_four_example_request_data())
    assert isinstance(e4, Experiment4DiagnosticRecordingRequest)
    assert e4.collection_authorized is False
    with pytest.raises(ValueError, match="not authorized"):
        require_collection_authorization(e4)


def test_observer_rejects_incomplete_or_undeclared_expected_setup_roster():
    setup = _setup()
    incomplete_resources = ResourceManifest(verifiers=setup.resources.verifiers[:-1])
    extra_resources = ResourceManifest(verifiers=setup.resources.verifiers + (
        VerifierResources(verifier_name="other", resources=(
            {"kind": "implementation", "resource_id": "other-implementation", "sha256": "d" * 64},
            {"kind": "configuration", "resource_id": "other-configuration", "sha256": "e" * 64},
        )),
    ))
    for resources in (incomplete_resources, extra_resources):
        wrong_setup = MeasurementSetup.model_validate({
            **setup.model_dump(mode="json"), "resources": resources.model_dump(mode="json")
        })
        with pytest.raises(ValueError, match="must cover exactly"):
            ResearchRosterObserver(object(), wrong_setup,
                inspect_local=lambda _configuration: pytest.fail("inspection must not run"))


def test_research_factory_returns_full_lazy_binding_without_construction(monkeypatch):
    from app.benchmark import project_adapter
    from app.game.offline import research_v1_recording_binding as module

    setup = _setup()
    adapter = AdapterConfiguration(embedding_snapshot=None, nli_snapshot=None,
        corpus_path="synthetic-corpus.json", index_dir="synthetic-index",
        index_receipt=None, service_observation=None)
    binding = ResearchV1RecordingBinding(version="research_v1_recording_binding_v1",
        binding_id="synthetic-binding-v1", dataset_id="research_v1_exploratory_v1",
        split="development", adapter_configuration_path="synthetic-adapter.json")
    monkeypatch.setattr(module, "resolve_research_configuration",
        lambda: (binding, None, adapter, None))
    monkeypatch.setattr(project_adapter, "inspect_setup", lambda _config: {
        "ready": True, "observed_setup": setup.model_dump(mode="json"),
        "blockers": [], "relocation_proof": None,
    })
    def forbidden_service(_configuration):
        pytest.fail("factory initialization must not call the live service observer")
    monkeypatch.setattr(project_adapter, "observe_service", forbidden_service)
    built = []
    monkeypatch.setattr(module, "_production_builders",
        lambda _config, _proof: {name: (lambda name=name: built.append(name) or
            type("Fake", (), {"name": name})()) for name in VERIFIER_ROSTER})

    pool, observed_setup, observer = module.research_v1_factory()
    assert isinstance(pool, ResearchLazyVerifierPool)
    assert pool.names == set(VERIFIER_ROSTER)
    assert observed_setup == setup
    assert built == []
    assert observer.last_evidence["live_service"] == "NOT_CHECKED"


class _FakeVerifier:
    def __init__(self, name, events):
        self.name = name
        self.events = events
        self.calls = 0

    def verify(self, question, answer, context=None):
        self.calls += 1
        self.events.append(("dispatch", self.name))
        return VerificationResult(verifier_name=self.name, passed=True, score=1.0,
            metadata={"decision": "SUPPORT", "synthetic": True})


def test_collector_prerequisites_precede_lazy_build_and_semantic_stays_unconstructed():
    request, setup = _synthetic_generic_request()

    events = []
    made = {}
    def builder(name):
        events.append(("construct", name))
        made[name] = _FakeVerifier(name, events)
        return made[name]
    def forbidden_semantic():
        pytest.fail("missing-reference Semantic constructor was called")
    constructors = {name: (lambda name=name: builder(name))
                    for name in ("confidence", "evidence", "rule")}
    constructors["semantic"] = forbidden_semantic
    def inspect(_configuration):
        return {"ready": True, "observed_setup": setup.model_dump(mode="json"),
                "inventory": {}, "blockers": []}
    observer = ResearchRosterObserver(object(), setup, inspect_local=inspect)
    pool = ResearchLazyVerifierPool(constructors, observer)
    starts = []
    bundle = collect(request, pool, setup, observer,
                     on_start=lambda identity: (events.append(("start", identity)), starts.append(identity)))

    semantic_rows = [row for row in bundle.attempts if row.candidate == "semantic"]
    assert len(semantic_rows) == 4
    assert all(row.attempt.state == "unavailable" and not row.executed for row in semantic_rows)
    assert "semantic" not in made
    assert not any(kind == "dispatch" and name == "semantic" for kind, name in events)
    assert set(made) == {"confidence", "evidence", "rule"}
    assert observer.last_evidence["local_resources"] == "MATCH"
    assert observer.last_evidence["live_service"] == "NOT_CHECKED"
    assert len(starts) == 12
    first_construct = next(i for i, event in enumerate(events) if event[0] == "construct")
    first_start = next(i for i, event in enumerate(events) if event[0] == "start")
    assert first_construct < first_start


def test_constructor_failure_precedes_start_intent_and_dispatch():
    request, setup = _synthetic_generic_request()
    events = []
    def fail_constructor():
        events.append("construct")
        raise RuntimeError("synthetic constructor failure")
    def unused_builder():
        pytest.fail("another verifier should not be built before the first failure")
    builders = {name: unused_builder for name in VERIFIER_ROSTER}
    builders["confidence"] = fail_constructor
    pool = make_lazy_verifier_pool(builders)
    observer = ResearchRosterObserver(object(), setup, inspect_local=lambda _config: {
        "ready": True, "observed_setup": setup.model_dump(mode="json"),
        "inventory": {}, "blockers": [],
    })
    starts = []
    with pytest.raises(RuntimeError, match="synthetic constructor failure"):
        collect(request, pool, setup, observer, on_start=lambda identity: starts.append(identity))
    assert events == ["construct"]
    assert starts == []


def test_research_binding_is_separate_from_generic_factory(monkeypatch):
    from app.game.offline import recording_adapters
    from app.game.offline import research_v1_recording_binding as binding_module
    from app.benchmark import project_adapter

    generic_factory = recording_adapters.project_factory
    assert binding_module.research_v1_factory is not generic_factory
    assert recording_adapters.project_factory is generic_factory
    setup = _setup()
    synthetic_pool = object()
    monkeypatch.setattr(project_adapter, "create_verifiers", lambda: (synthetic_pool, setup))
    verifiers, actual_setup, observer = recording_adapters.project_factory()
    assert verifiers is synthetic_pool
    assert actual_setup is setup
    assert type(observer).__name__ == "ProjectObserver"
