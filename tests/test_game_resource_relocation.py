"""Strict tests for explicitly bound content-preserving resource relocation."""

import hashlib
import json
import os

import pytest

from app.game.models import content_id
from app.game.offline.resource_relocation import (
    ResourceRelocationBinding,
    verify_relocated_index,
)
from app.game.resource_provenance import ResourceManifest


def _resource_manifest(index_fingerprint):
    return ResourceManifest(verifiers=({
        "verifier_name": "evidence",
        "resources": [
            {"kind": "configuration", "resource_id": "evidence-adapter-configuration", "sha256": "1" * 64},
            {"kind": "implementation", "resource_id": "evidence-implementation", "sha256": "2" * 64},
            {"kind": "model", "resource_id": "local-embedding-snapshot", "sha256": "3" * 64},
            {"kind": "model", "resource_id": "local-nli-snapshot", "sha256": "4" * 64},
            {"kind": "corpus", "resource_id": "evidence-corpus", "sha256": "5" * 64},
            {"kind": "index", "resource_id": "evidence-index", "sha256": index_fingerprint},
        ],
    },))


def _case(tmp_path):
    corpus_path = tmp_path / "new-root" / "corpus.json"
    corpus_path.parent.mkdir(parents=True)
    corpus_bytes = b'{"id":"same","text":"retained fact"}'
    corpus_path.write_bytes(corpus_bytes)
    old_mtime = 1_700_000_000.0
    new_mtime = 1_710_000_000.0
    os.utime(corpus_path, (new_mtime, new_mtime))

    index_dir = tmp_path / "new-root" / "index"
    index_dir.mkdir()
    faiss = b"unchanged vector bytes"
    chunks = b"unchanged chunk bytes"
    for name, data in (("faiss.index", faiss), ("chunks.json", chunks),
                       ("manifest.json", b"stored relocated manifest")):
        (index_dir / name).write_bytes(data)
    index_hashes = {name: hashlib.sha256((index_dir / name).read_bytes()).hexdigest()
                    for name in ("faiss.index", "chunks.json", "manifest.json")}

    receipt = {"version": "observed_index_build_v1", "chunk_size": 500,
               "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
               "index_sha256": index_hashes["faiss.index"],
               "chunks_sha256": index_hashes["chunks.json"],
               "embedding_sha256": "7" * 64}
    receipt_path = tmp_path / "new-root" / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    receipt_digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    historical_corpus = r"C:\historical\corpus.json"
    historical_manifest = r"C:\historical\index\manifest.json"
    current_manifest_path = index_dir / "manifest.json"
    corpus_sha = hashlib.sha256(corpus_bytes).hexdigest()
    current = {"version": 2, "corpus_path": str(corpus_path.resolve()),
        "corpus_size": len(corpus_bytes), "corpus_mtime": new_mtime,
        "corpus_sha256": corpus_sha, "corpus_version": "sha256:" + corpus_sha,
        "chunk_size": 500, "embedding_model": "all-MiniLM-L6-v2", "index_version": "idx-test"}
    stored = dict(current, corpus_path=historical_corpus, corpus_mtime=old_mtime)
    expected_index = content_id([dict(index_hashes, **{"manifest.json": "8" * 64}), receipt])
    current_index = content_id([index_hashes, receipt])
    expected = _resource_manifest(expected_index)
    observed = _resource_manifest(current_index)
    binding = ResourceRelocationBinding(
        version="verified_resource_relocation_v1",
        expected_resource_manifest_id=expected.manifest_id,
        historical_corpus_path=historical_corpus,
        current_corpus_path=str(corpus_path.resolve()),
        historical_manifest_path=historical_manifest,
        current_manifest_path=str(current_manifest_path.resolve()),
        historical_corpus_mtime=old_mtime,
        current_corpus_mtime=new_mtime,
        corpus_sha256=corpus_sha,
        corpus_size=len(corpus_bytes),
        faiss_sha256=index_hashes["faiss.index"],
        chunks_sha256=index_hashes["chunks.json"],
        manifest_sha256=index_hashes["manifest.json"],
        receipt_sha256=receipt_digest,
        receipt_fingerprint=content_id(receipt),
        embedding_model_sha256="3" * 64,
        nli_model_sha256="4" * 64,
        semantic_configuration_sha256="1" * 64,
        manifest_version=2,
        chunk_size=500,
        embedding_model="all-MiniLM-L6-v2",
        index_version="idx-test",
        historical_index_fingerprint=expected_index,
        current_index_fingerprint=current_index,
    )
    kwargs = dict(binding=binding, expected_manifest=expected,
        observed_manifest=observed, stored_manifest=stored,
        current_manifest=current, corpus_path=corpus_path,
        manifest_path=current_manifest_path, corpus_sha256=corpus_sha,
        index_hashes=index_hashes, receipt_path=receipt_path, receipt=receipt,
        expected_receipt=receipt, embedding_model_sha256="3" * 64,
        nli_model_sha256="4" * 64, semantic_configuration_sha256="1" * 64)
    return kwargs


def test_identical_content_at_relocated_paths_and_new_timestamps_is_audited(tmp_path):
    report = verify_relocated_index(**_case(tmp_path))
    assert report["authorized_resource_ids"] == ["index:evidence-index"]
    assert report["historical_corpus_path"] == r"C:\historical\corpus.json"
    assert report["current_corpus_path"].endswith("new-root\\corpus.json")
    assert report["historical_corpus_mtime"] != report["current_corpus_mtime"]
    assert len(report["binding_id"]) == 64


def test_same_size_changed_corpus_with_preserved_mtime_rejects(tmp_path):
    case = _case(tmp_path)
    path = case["corpus_path"]
    stat = path.stat()
    original = path.read_bytes()
    altered = original.replace(b"same", b"diff")
    assert len(altered) == len(original)
    path.write_bytes(altered)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert path.stat().st_mtime_ns == stat.st_mtime_ns
    with pytest.raises(ValueError, match="corpus content differs"):
        verify_relocated_index(**case)


@pytest.mark.parametrize("field", ["faiss_sha256", "chunks_sha256", "manifest_sha256",
                                      "embedding_model_sha256", "nli_model_sha256",
                                      "semantic_configuration_sha256"])
def test_changed_content_or_semantic_setting_rejects(tmp_path, field):
    case = _case(tmp_path)
    if field in {"faiss_sha256", "chunks_sha256", "manifest_sha256"}:
        filename = {"faiss_sha256": "faiss.index", "chunks_sha256": "chunks.json",
                    "manifest_sha256": "manifest.json"}[field]
        path = case["manifest_path"].parent / filename
        original = path.read_bytes()
        path.write_bytes(b"X" + original[1:])
        case["index_hashes"] = dict(case["index_hashes"], **{
            filename: hashlib.sha256(path.read_bytes()).hexdigest()})
    elif field == "embedding_model_sha256":
        case["embedding_model_sha256"] = "a" * 64
    elif field == "nli_model_sha256":
        case["nli_model_sha256"] = "a" * 64
    else:
        case["semantic_configuration_sha256"] = "a" * 64
    with pytest.raises(ValueError):
        verify_relocated_index(**case)


def test_changed_receipt_rejects(tmp_path):
    case = _case(tmp_path)
    case["receipt"] = dict(case["receipt"], chunk_size=501)
    case["receipt_path"].write_text(json.dumps(case["receipt"]), encoding="utf-8")
    with pytest.raises(ValueError, match="receipt"):
        verify_relocated_index(**case)


def test_missing_corpus_rejects(tmp_path):
    case = _case(tmp_path)
    case["corpus_path"].unlink()
    with pytest.raises(FileNotFoundError):
        verify_relocated_index(**case)


def test_missing_index_file_rejects(tmp_path):
    case = _case(tmp_path)
    (case["manifest_path"].parent / "faiss.index").unlink()
    with pytest.raises(FileNotFoundError):
        verify_relocated_index(**case)


def test_legacy_manifest_rejects(tmp_path):
    case = _case(tmp_path)
    case["stored_manifest"] = dict(case["stored_manifest"], version=1)
    with pytest.raises(ValueError, match="non-relocation index manifest fields"):
        verify_relocated_index(**case)


def test_non_index_resource_mismatch_is_not_authorized(tmp_path):
    case = _case(tmp_path)
    altered = case["observed_manifest"].model_dump(mode="json")
    for verifier in altered["verifiers"]:
        for resource in verifier["resources"]:
            if resource["resource_id"] == "evidence-implementation":
                resource["sha256"] = "a" * 64
    case["observed_manifest"] = ResourceManifest.model_validate(altered)
    with pytest.raises(ValueError, match="non-relocation resource fingerprints differ"):
        verify_relocated_index(**case)


def _runtime_with_changed_resource(explicit_authorizer):
    import random

    from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
    from app.game.execution import GameRuntime
    from app.game.offline.evaluation import export_artifact
    from app.game.offline.reliability import fit_reliability_first
    from app.models.schemas import ValidationRequest
    from tests.test_game_offline import report
    from tests.test_game_foundation import analysis
    from tests.test_game_reliability_first import full_fixture

    context, manifest, contract, attacks, payoffs, selector = full_fixture()
    bound, policy = fit_reliability_first(context, manifest, contract, attacks, payoffs)
    artifact = export_artifact(policy, bound, manifest, contract, attacks, applicable_domain=bound.plan.domain)
    expected = artifact.contract.resource_manifest
    altered = expected.model_dump(mode="json")
    resource = altered["verifiers"][0]["resources"][0]
    resource["sha256"] = "f" * 64
    observed = ResourceManifest.model_validate(altered)

    class Observer:
        def snapshot(self):
            return observed

        def authorize_relocation(self, expected_manifest, observed_manifest):
            if not explicit_authorizer:
                raise AssertionError("non-relocation observer must not authorize a mismatch")
            return {"version": "verified_resource_relocation_v1", "binding_id": "b" * 64,
                "expected_resource_manifest_id": expected_manifest.manifest_id,
                "historical_resource_manifest_id": expected_manifest.manifest_id,
                "observed_resource_manifest_id": observed_manifest.manifest_id,
                "authorized_resource_ids": ["index:evidence-index"]}

    for verifier in selector._injected:
        verifier.verify = lambda *args, n=verifier.name, **kwargs: report(n)
    runtime = GameRuntime(InMemoryPolicyProvider((artifact,)),
        DeploymentEpisode(episode_id="relocation-test", context=bound, contract=artifact.contract,
            execution_configuration_id=artifact.execution_configuration_id),
        random.Random(42), allow_synthetic_for_tests=True, resource_observer=Observer())
    dev = manifest.partition("development").examples[0]
    return runtime.run(selector, analysis(), ValidationRequest(question=dev.question, answer=dev.answer), dev.validation_id)


def test_runtime_rejects_mapping_for_any_resource_except_bound_index():
    run = _runtime_with_changed_resource(True)
    assert run.public_status == "uncertain"
    assert run.summary["selection_status"] == "provenance_incompatible"
    assert "relocation can authorize only the evidence-index fingerprint" in run.summary["selection_reasons"][0]
    assert run.summary["selected_strategy_id"] is None and run.summary["attempted_verifiers"] == []


def test_runtime_without_relocation_authorizer_remains_strict():
    from app.game.artifacts import DeploymentEpisode, InMemoryPolicyProvider
    from app.game.execution import GameRuntime
    from app.game.offline.evaluation import export_artifact
    from app.game.offline.reliability import fit_reliability_first
    from app.models.schemas import ValidationRequest
    from tests.test_game_foundation import analysis
    from tests.test_game_offline import report
    from tests.test_game_reliability_first import full_fixture
    import random

    context, manifest, contract, attacks, payoffs, selector = full_fixture()
    bound, policy = fit_reliability_first(context, manifest, contract, attacks, payoffs)
    artifact = export_artifact(policy, bound, manifest, contract, attacks, applicable_domain=bound.plan.domain)
    altered = artifact.contract.resource_manifest.model_dump(mode="json")
    altered["verifiers"][0]["resources"][0]["sha256"] = "f" * 64
    observed = ResourceManifest.model_validate(altered)

    class Observer:
        def snapshot(self):
            return observed

    for verifier in selector._injected:
        verifier.verify = lambda *args, n=verifier.name, **kwargs: report(n)
    runtime = GameRuntime(InMemoryPolicyProvider((artifact,)),
        DeploymentEpisode(episode_id="strict-test", context=bound, contract=artifact.contract,
            execution_configuration_id=artifact.execution_configuration_id),
        random.Random(42), allow_synthetic_for_tests=True, resource_observer=Observer())
    dev = manifest.partition("development").examples[0]
    run = runtime.run(selector, analysis(), ValidationRequest(question=dev.question, answer=dev.answer), dev.validation_id)
    assert run.public_status == "uncertain"
    assert run.summary["selection_status"] == "provenance_incompatible"
    assert "relocation can authorize only the evidence-index fingerprint" in run.summary["selection_reasons"][0]
    assert run.summary["selected_strategy_id"] is None and run.summary["attempted_verifiers"] == []
