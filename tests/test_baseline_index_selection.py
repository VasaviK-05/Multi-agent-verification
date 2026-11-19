"""Offline resource wiring tests; synthetic bytes and mocked model constructors."""
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.game.models import content_id
from app.selection import baseline_resources as resources
from app.selection.verifier_selector import VerifierSelector
from app.selection.baseline_budget import BaselineBudgetSnapshot
from app.models.schemas import ValidationRequest
from app.services.validation_service import ValidationService
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.analysis.question_analyzer import QuestionAnalyzer
from tests.test_adaptive_pipeline import offline_pipeline_boundaries, MetadataChecker, factual_metadata


@pytest.fixture(autouse=True)
def offline(monkeypatch, offline_pipeline_boundaries, tmp_path):
    from app.utils.config import settings
    monkeypatch.setattr(settings, "BASELINE_EVIDENCE_CONFIG_PATH", "")
    monkeypatch.setattr(resources, "LOCAL_CONFIGURATION", tmp_path / "no-local-config")


@pytest.fixture
def selected(tmp_path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text('[]', encoding="utf-8")
    index = tmp_path / "new-index"
    index.mkdir()
    (index / "faiss.index").write_bytes(b"SYNTHETIC vectors; never read by faiss")
    (index / "chunks.json").write_text('[]', encoding="utf-8")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    digest = sha(corpus)
    receipt = dict(version="observed_index_build_v1", embedding_sha256="a" * 64,
        corpus_sha256=digest, chunk_size=500, index_sha256=sha(index / "faiss.index"),
        chunks_sha256=sha(index / "chunks.json"))
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    version = "sha256:" + digest
    manifest = dict(version=2, corpus_path=str(corpus), corpus_size=corpus.stat().st_size,
        corpus_mtime=corpus.stat().st_mtime, corpus_sha256=digest, corpus_version=version,
        chunk_size=500, embedding_model="all-MiniLM-L6-v2", index_version="idx-" + hashlib.sha256(
            json.dumps([version, 500, "all-MiniLM-L6-v2"]).encode()).hexdigest()[:12])
    (index / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return resources.BaselineEvidenceConfiguration(corpus, index, path, digest, sha(path), content_id(receipt))


def test_selected_index_and_receipt_resolve_identically_for_observer(selected, monkeypatch):
    monkeypatch.setattr(resources, "load_baseline_evidence_configuration", lambda: selected)
    corpus, index, cfg = resources.resolve_baseline_evidence_resources(selected.receipt_path)
    assert corpus == selected.corpus_path and index == selected.index_dir and cfg is selected
    assert resources.validate_baseline_evidence(selected)["corpus_sha256"] == selected.corpus_sha256
    with pytest.raises(ValueError, match="receipt_path_mismatch"):
        resources.resolve_baseline_evidence_resources(selected.receipt_path.parent / "old-receipt.json")


def test_retriever_and_verifier_receive_selected_path_without_answer_changes(selected, monkeypatch):
    from app.verifiers import evidence_retriever, evidence_verifier
    retriever = Mock(return_value=object())
    verifier = Mock(return_value=object())
    monkeypatch.setattr(evidence_retriever, "EvidenceRetriever", retriever)
    monkeypatch.setattr(evidence_verifier, "EvidenceVerifier", verifier)
    result = resources.construct_baseline_evidence(selected)
    retriever.assert_called_once_with(corpus_path=str(selected.corpus_path), index_dir=selected.index_dir)
    verifier.assert_called_once_with(corpus_path=str(selected.corpus_path), retriever=retriever.return_value)
    assert result is verifier.return_value


@pytest.mark.parametrize("change", ["missing_index", "changed_vectors", "changed_chunks", "changed_manifest", "wrong_receipt", "wrong_corpus"])
def test_invalid_selected_resources_fail_before_any_constructor(selected, monkeypatch, change):
    from app.verifiers import evidence_retriever, evidence_verifier
    constructor = Mock(side_effect=AssertionError("no model construction or automatic rebuild"))
    monkeypatch.setattr(evidence_retriever, "EvidenceRetriever", constructor)
    monkeypatch.setattr(evidence_verifier, "EvidenceVerifier", constructor)
    if change == "missing_index":
        (selected.index_dir / "faiss.index").unlink()  # Temporary synthetic fixture only.
    elif change == "changed_vectors":
        (selected.index_dir / "faiss.index").write_bytes(b"modified synthetic")
    elif change == "changed_chunks":
        (selected.index_dir / "chunks.json").write_text('[1]', encoding="utf-8")
    elif change == "changed_manifest":
        (selected.index_dir / "manifest.json").write_text('{}', encoding="utf-8")
    elif change == "wrong_receipt":
        selected = replace(selected, receipt_id="wrong")
    else:
        selected = replace(selected, corpus_sha256="wrong")
    with pytest.raises((OSError, ValueError)):
        resources.construct_baseline_evidence(selected)
    constructor.assert_not_called()


def test_selector_configures_new_index_and_never_rebinds_a_cached_verifier(selected, monkeypatch):
    builder = Mock(return_value=MetadataChecker("evidence"))
    monkeypatch.setattr(resources, "construct_baseline_evidence", builder)
    selector = resources.BaselineVerifierSelector()
    selector.configure_baseline_evidence(selected)
    assert selector.resolve("evidence") is selector.resolve("evidence")
    builder.assert_called_once_with(selected)
    with pytest.raises(ValueError, match="after construction"):
        selector.configure_baseline_evidence(None)


def test_injected_selector_and_verifiers_are_preserved(selected, monkeypatch):
    injected = MetadataChecker("evidence")
    for selector in (VerifierSelector(verifiers=[injected]),
                     resources.BaselineVerifierSelector(verifiers=[injected])):
        builder = Mock(side_effect=AssertionError("injected Evidence must not be replaced"))
        monkeypatch.setattr(resources, "construct_baseline_evidence", builder)
        if isinstance(selector, resources.BaselineVerifierSelector):
            selector.configure_baseline_evidence(selected)
            assert not selector.uses_default_factory
        service = ValidationService(ValidationOrchestrator(
            verifier_selector=selector, question_analyzer=QuestionAnalyzer(mode="heuristic")))
        assert service._orchestrator.verifier_selector is selector
        assert service._orchestrator.reputation_manager is selector.reputation_manager
        assert selector.resolve("evidence") is injected
        builder.assert_not_called()


def test_baseline_inherits_selection_and_resolution_without_overrides():
    cls = resources.BaselineVerifierSelector
    for name in ("plan", "resolve", "minimum_count", "target_count", "ranking_utility", "iter_ranked", "select"):
        assert getattr(cls, name) is getattr(VerifierSelector, name)


def test_standalone_baseline_uses_real_selector_new_resource_and_one_budget_capture(selected, monkeypatch):
    from app.services import validation_service
    import app.selection.verifier_selector as module
    monkeypatch.setattr(validation_service.settings, "EXECUTION_MODE", "baseline")
    monkeypatch.setattr(resources, "load_baseline_evidence_configuration", lambda: selected)
    evidence = MetadataChecker("evidence", score=1., metadata=factual_metadata())
    builder = Mock(return_value=evidence)
    monkeypatch.setattr(resources, "construct_baseline_evidence", builder)
    monkeypatch.setattr(module, "_build_default_verifier", lambda n: MetadataChecker(n, score=1., metadata=factual_metadata()))
    service = ValidationService()
    run = service._orchestrator
    provider = Mock(return_value=BaselineBudgetSnapshot(reason="SYNTHETIC unavailable calibration"))
    monkeypatch.setattr(run, "_baseline_budget_provider", provider)
    request = ValidationRequest(question="What is the population of a patient?", answer="original answer", context="original context")
    before = request.model_dump()
    result = service.validate(request)
    assert type(run.verifier_selector) is resources.BaselineVerifierSelector
    assert run.verifier_selector.baseline_evidence_configuration is selected
    builder.assert_called_once_with(selected)
    provider.assert_called_once_with(run.verifier_selector)
    assert result.final_status == "passed" and request.model_dump() == before
    assert result.execution_audit["baseline_evidence_configuration_id"] == selected.configuration_id
    assert result.execution_audit["baseline_budget"]["status"] == "unconfigured"


def test_explicit_missing_configuration_is_an_error_not_old_index_fallback(tmp_path, monkeypatch):
    from app.utils.config import settings
    monkeypatch.setattr(settings, "BASELINE_EVIDENCE_CONFIG_PATH", str(tmp_path / "missing.json"))
    with pytest.raises(OSError):
        resources.load_baseline_evidence_configuration()


@pytest.mark.parametrize("explicit", [False, True])
def test_server_resource_json_loads_same_immutable_configuration(selected, tmp_path, monkeypatch, explicit):
    from app.utils.config import settings
    from dataclasses import asdict, FrozenInstanceError
    path = tmp_path / "resource-config.json"
    data = {k: str(v) for k, v in asdict(selected).items()}
    data["version"] = "baseline_evidence_resources_v1"
    path.write_text(json.dumps(data), encoding="utf-8")
    if explicit:
        monkeypatch.setattr(settings, "BASELINE_EVIDENCE_CONFIG_PATH", str(path))
    else:
        monkeypatch.setattr(resources, "LOCAL_CONFIGURATION", path)
    loaded = resources.load_baseline_evidence_configuration()
    assert loaded == selected and loaded.configuration_id == selected.configuration_id
    resources.validate_baseline_evidence(loaded)
    with pytest.raises(FrozenInstanceError):
        loaded.index_dir = tmp_path / "old-index"
