"""Observe the default CPU baseline without constructing verifiers or rebuilding assets.

An index build receipt is mandatory. Hashing old vectors is not a build receipt.
Service observation makes metadata GETs only, and only after local checks pass.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess

from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup
from app.game.resource_provenance import ResourceManifest

INITIALIZATION = "baseline_default_lazy_resolve_v1"
NAMES = ("semantic", "evidence", "rule", "confidence")
_nli_binding = None


def _check_nli_cache(fingerprint):
    """Do not certify a model cached before this observer established provenance."""
    from app.verifiers.evidence_verifier import default_nli_pipeline
    if default_nli_pipeline.cache_info().currsize and _nli_binding != fingerprint:
        raise ValueError("baseline_cached_nli_has_unverified_provenance")


def observe_baseline_setup(*, index_receipt_path, service_observation_path):
    global _nli_binding
    from app.benchmark import project_adapter as adapter
    from app.selection.baseline_resources import resolve_baseline_evidence_resources

    root = adapter.ROOT
    corpus, index, selected = resolve_baseline_evidence_resources(index_receipt_path)
    if not index_receipt_path or not Path(index_receipt_path).is_file():
        raise ValueError("baseline_index_build_receipt_unavailable")
    if not service_observation_path or not Path(service_observation_path).is_file():
        raise ValueError("baseline_service_observation_unavailable")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise ValueError("baseline_model_resolution_must_be_offline_and_frozen")
    # Do not silently observe one cache while constructors use another.
    if any(os.environ.get(k) for k in ("TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME")):
        raise ValueError("baseline_cache_override_requires_review")
    from huggingface_hub import constants as hub_constants
    from huggingface_hub import is_offline_mode
    if not hub_constants.HF_HUB_OFFLINE or not is_offline_mode():
        raise ValueError("baseline_offline_settings_were_not_captured_before_import")
    cache = Path(hub_constants.HF_HUB_CACHE)

    def snapshot(repo):
        directory = cache / ("models--" + repo.replace("/", "--"))
        revision = (directory / "refs/main").read_text(encoding="utf-8").strip()
        if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
            raise ValueError("baseline_model_revision_unresolved")
        return directory / "snapshots" / revision

    embedding = adapter.directory_digest(snapshot("sentence-transformers/all-MiniLM-L6-v2"))["sha256"]
    nli = adapter.directory_digest(snapshot("cross-encoder/nli-deberta-v3-small"))["sha256"]
    corpus_sha = adapter.file_digest(corpus)
    hashes = {name: adapter.file_digest(index / name)
              for name in ("faiss.index", "chunks.json", "manifest.json")}
    receipt = adapter.read_json(index_receipt_path)
    expected_receipt = dict(version="observed_index_build_v1", embedding_sha256=embedding,
        corpus_sha256=corpus_sha, chunk_size=500, index_sha256=hashes["faiss.index"],
        chunks_sha256=hashes["chunks.json"])
    if receipt != expected_receipt:
        raise ValueError("baseline_index_build_receipt_mismatch")
    manifest = adapter.read_json(index / "manifest.json")
    constants = adapter.source_constants("app/verifiers/evidence_retriever.py",
                                        {"EMBEDDING_MODEL", "MANIFEST_VERSION"})
    corpus_version = "sha256:" + corpus_sha
    import hashlib
    expected_manifest = dict(version=constants["MANIFEST_VERSION"], corpus_path=str(corpus),
        corpus_size=corpus.stat().st_size, corpus_mtime=corpus.stat().st_mtime,
        corpus_sha256=corpus_sha, corpus_version=corpus_version, chunk_size=500,
        embedding_model=constants["EMBEDDING_MODEL"], index_version="idx-" + hashlib.sha256(
            json.dumps([corpus_version, 500, constants["EMBEDDING_MODEL"]]).encode()).hexdigest()[:12])
    if manifest != expected_manifest:
        raise ValueError("baseline_index_manifest_mismatch")
    _check_nli_cache(nli)
    # Default constructors choose a device automatically. This reviewed observer
    # deliberately supports CPU only, rather than asserting an unobserved GPU setup.
    from sentence_transformers.util import get_device_name
    if get_device_name() != "cpu":
        raise ValueError("baseline_device_requires_review")
    saved = adapter.ServiceObservation.model_validate(adapter.read_json(service_observation_path))
    config = adapter.AdapterConfiguration(embedding_snapshot=None, nli_snapshot=None,
        corpus_path=str(corpus), index_dir=str(index), index_receipt=str(index_receipt_path),
        service_observation=str(service_observation_path),
        ollama_url=os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"))
    if adapter.observe_service(config) != saved:
        raise ValueError("baseline_live_service_mismatch")
    shared = ["app/verifiers/base_verifier.py", "app/models/schemas.py", "app/benchmark/project_adapter.py"]
    implementations = {
        "semantic": ["semantic_verifier.py", "claim_generator.py", "confidence_verifier.py"],
        "evidence": ["evidence_verifier.py", "evidence_retriever.py", "claim_generator.py"],
        "rule": ["rule_verifier.py"],
        "confidence": ["confidence_verifier.py", "self_consistency.py", "evidence_verifier.py", "claim_generator.py"],
    }
    configuration = dict(initialization=INITIALIZATION, corpus_path=str(corpus), index_dir=str(index),
        embedding_alias="all-MiniLM-L6-v2", nli_alias="cross-encoder/nli-deberta-v3-small",
        device="cpu", ollama_url=config.ollama_url, ollama_model=config.ollama_model,
        n_samples=5, temperature=.8, timeout=60., chunk_size=500)
    prompt = adapter.source_constants("app/verifiers/self_consistency.py", {"SHORT_ANSWER_PROMPT"})["SHORT_ANSWER_PROMPT"]
    rows = []
    for name in NAMES:
        resources = [("implementation", name + "-implementation", content_id([
            (p, adapter.file_digest(root / p)) for p in shared + ["app/verifiers/" + f for f in implementations[name]]])),
            ("configuration", name + "-baseline-configuration", content_id(configuration))]
        if name in {"semantic", "evidence"}:
            resources.append(("model", "local-embedding-snapshot", embedding))
        if name in {"evidence", "confidence"}:
            resources.append(("model", "local-nli-snapshot", nli))
        if name == "evidence":
            resources += [("corpus", "evidence-corpus", corpus_sha),
                          ("index", "evidence-index", content_id([hashes, receipt]))]
        if name == "confidence":
            resources += [("model", "ollama-model", saved.model_digest[7:]),
                          ("service", "ollama-service", content_id(saved.model_dump(mode="json"))),
                          ("prompt", "self-consistency-short-answer", content_id(prompt))]
        rows.append(dict(verifier_name=name, resources=[dict(kind=k, resource_id=i, sha256=h) for k, i, h in resources]))
    environment = adapter.hardware()
    environment["initialization"] = INITIALIZATION
    environment["baseline_evidence_configuration_id"] = selected.configuration_id if selected else "legacy_default"
    environment["model_resolution"] = "HF_HUB_OFFLINE=1;TRANSFORMERS_OFFLINE=1"
    import torch
    environment["torch_num_threads"] = str(torch.get_num_threads())
    environment["torch_num_interop_threads"] = str(torch.get_num_interop_threads())
    versions = {name: importlib.metadata.version(name) for name in adapter.PACKAGES}
    import platform
    versions["python"] = platform.python_version()
    setup = MeasurementSetup(resources=ResourceManifest(verifiers=tuple(rows)), environment=environment,
        dependency_versions=versions, code_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        application_source_digest=content_id([(p.relative_to(root).as_posix(), adapter.file_digest(p))
            for p in sorted((root / "app").rglob("*.py"))]), evidence_kind="empirical")
    _nli_binding = nli
    return setup
