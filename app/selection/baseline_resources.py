"""Baseline-only, content-bound Evidence resource selection. No Game adapter use."""
from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path

from app.game.models import content_id
from app.selection.verifier_selector import VerifierSelector

ROOT = Path(__file__).resolve().parents[2]
LOCAL_CONFIGURATION = ROOT / "build/baseline-evidence-resources-v1.json"


@dataclass(frozen=True)
class BaselineEvidenceConfiguration:
    corpus_path: Path
    index_dir: Path
    receipt_path: Path
    corpus_sha256: str
    receipt_sha256: str
    receipt_id: str

    @property
    def configuration_id(self):
        return content_id({k: str(v) for k, v in asdict(self).items()})


class BaselineVerifierSelector(VerifierSelector):
    """Baseline resource hooks; all planning and public resolution stay inherited."""

    @property
    def uses_default_factory(self) -> bool:
        return self._injected is None

    @property
    def baseline_evidence_configuration(self):
        return getattr(self, "_baseline_evidence_configuration", None)

    def configure_baseline_evidence(self, configuration):
        if "evidence" in self._cache and self.baseline_evidence_configuration != configuration:
            raise ValueError("cannot change Evidence resources after construction")
        self._baseline_evidence_configuration = configuration

    def bind_baseline_setup(self, fingerprint: str) -> None:
        if self._cache and getattr(self, "_baseline_setup_fingerprint", None) != fingerprint:
            raise ValueError("cached baseline verifiers have unverified setup provenance")
        self._baseline_setup_fingerprint = fingerprint

    def _default_instance(self, name):
        if name != "evidence" or self.baseline_evidence_configuration is None:
            return super()._default_instance(name)
        if name not in self._cache:
            self._cache[name] = construct_baseline_evidence(self.baseline_evidence_configuration)
        return self._cache[name]


def load_baseline_evidence_configuration():
    """Optional local server configuration; never accept a request-supplied path.

    Other checkouts without the optional local file retain their legacy default.
    An explicitly configured missing file, or any invalid present file, fails.
    """
    from app.utils.config import settings
    from app.game.offline.calibration import read_json
    configured = settings.BASELINE_EVIDENCE_CONFIG_PATH
    path = Path(configured) if configured else LOCAL_CONFIGURATION
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file() and not configured:
        return None
    data = read_json(path)
    if set(data) != {"version", "corpus_path", "index_dir", "receipt_path",
                    "corpus_sha256", "receipt_sha256", "receipt_id"}:
        raise ValueError("invalid baseline Evidence configuration fields")
    if data.pop("version") != "baseline_evidence_resources_v1":
        raise ValueError("unsupported baseline Evidence configuration")
    for key in ("corpus_path", "index_dir", "receipt_path"):
        p = Path(data[key])
        data[key] = (p if p.is_absolute() else ROOT / p).resolve()
    return BaselineEvidenceConfiguration(**data)


def validate_baseline_evidence(configuration):
    """No model loads, service requests, writes, inferred receipts or old-index fallback."""
    from app.benchmark.project_adapter import file_digest, read_json, source_constants

    c = configuration
    if file_digest(c.corpus_path) != c.corpus_sha256 or file_digest(c.receipt_path) != c.receipt_sha256:
        raise ValueError("baseline Evidence corpus/receipt hash mismatch")
    receipt = read_json(c.receipt_path)
    if content_id(receipt) != c.receipt_id:
        raise ValueError("baseline Evidence receipt identity mismatch")
    keys = {"version", "embedding_sha256", "corpus_sha256", "chunk_size", "index_sha256", "chunks_sha256"}
    if set(receipt) != keys or receipt["version"] != "observed_index_build_v1":
        raise ValueError("baseline Evidence receipt schema mismatch")
    if receipt["corpus_sha256"] != c.corpus_sha256 or receipt["chunk_size"] != 500:
        raise ValueError("baseline Evidence receipt corpus/chunk mismatch")
    if (file_digest(c.index_dir / "faiss.index") != receipt["index_sha256"] or
            file_digest(c.index_dir / "chunks.json") != receipt["chunks_sha256"]):
        raise ValueError("baseline Evidence selected index hash mismatch")
    constants = source_constants("app/verifiers/evidence_retriever.py", {"MANIFEST_VERSION", "EMBEDDING_MODEL"})
    version = "sha256:" + c.corpus_sha256
    stat = c.corpus_path.stat()
    expected = dict(version=constants["MANIFEST_VERSION"], corpus_path=str(c.corpus_path),
        corpus_size=stat.st_size, corpus_mtime=stat.st_mtime, corpus_sha256=c.corpus_sha256,
        corpus_version=version, chunk_size=500, embedding_model=constants["EMBEDDING_MODEL"],
        index_version="idx-" + hashlib.sha256(json.dumps([version, 500, constants["EMBEDDING_MODEL"]]).encode()).hexdigest()[:12])
    if read_json(c.index_dir / "manifest.json") != expected:
        raise ValueError("baseline Evidence selected manifest mismatch")
    return receipt


def construct_baseline_evidence(configuration):
    # Check before constructors can trigger EvidenceRetriever's automatic rebuild.
    validate_baseline_evidence(configuration)
    from app.verifiers.evidence_retriever import EvidenceRetriever
    from app.verifiers.evidence_verifier import EvidenceVerifier
    retriever = EvidenceRetriever(corpus_path=str(configuration.corpus_path), index_dir=configuration.index_dir)
    return EvidenceVerifier(corpus_path=str(configuration.corpus_path), retriever=retriever)


def resolve_baseline_evidence_resources(index_receipt_path):
    """Shared observer path resolution; a selected resource never falls back on error."""
    import os
    selected = load_baseline_evidence_configuration()
    if selected is not None:
        if not index_receipt_path or Path(index_receipt_path).resolve() != selected.receipt_path:
            raise ValueError("baseline_selected_receipt_path_mismatch")
        validate_baseline_evidence(selected)
        return selected.corpus_path, selected.index_dir, selected
    corpus = Path(os.environ.get("EVIDENCE_CORPUS_PATH", "data/evidence_corpus.json")).resolve()
    return corpus, corpus.parent / "evidence_index" / corpus.stem, None
