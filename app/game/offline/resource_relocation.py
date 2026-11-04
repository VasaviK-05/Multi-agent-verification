"""Explicit, content-verified relocation for a resource-bound game artifact.

The ordinary project preflight remains strict. This adapter is only used when an
operator supplies a relocation binding, and it authorizes exactly one mapped
resource fingerprint after checking the bound files and manifest semantics.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictFloat, StrictInt, model_validator

from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.resource_provenance import ResourceManifest


class ResourceRelocationBinding(FrozenModel):
    version: Literal["verified_resource_relocation_v1"]
    expected_resource_manifest_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    historical_corpus_path: str
    current_corpus_path: str
    historical_manifest_path: str
    current_manifest_path: str
    historical_corpus_mtime: StrictFloat
    current_corpus_mtime: StrictFloat
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    corpus_size: StrictInt = Field(gt=0)
    faiss_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chunks_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    receipt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    receipt_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    embedding_model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    nli_model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_configuration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_version: StrictInt
    chunk_size: StrictInt = Field(gt=0)
    embedding_model: str
    index_version: str
    historical_index_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_index_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def distinct_locations(self):
        if self.historical_corpus_path == self.current_corpus_path:
            raise ValueError("relocation binding must name distinct corpus locations")
        if self.historical_manifest_path == self.current_manifest_path:
            raise ValueError("relocation binding must name distinct manifest locations")
        return self

    @property
    def binding_id(self) -> str:
        return content_id(self.model_dump(mode="json"))


def verify_relocated_index(
    binding: ResourceRelocationBinding,
    *,
    expected_manifest: ResourceManifest,
    observed_manifest: ResourceManifest,
    stored_manifest: dict,
    current_manifest: dict,
    corpus_path: Path,
    manifest_path: Path,
    corpus_sha256: str,
    index_hashes: dict[str, str],
    receipt_path: Path,
    receipt: dict,
    expected_receipt: dict,
    embedding_model_sha256: str,
    nli_model_sha256: str,
    semantic_configuration_sha256: str,
) -> dict:
    """Authorize a single index-ID mapping after verifying all source content.

    The mapping is never used to excuse a corpus, index, chunks, model, receipt,
    settings, or implementation mismatch. Only the resource ID
    ``evidence-index`` may have a historical/current fingerprint pair.
    """
    manifest_path = manifest_path.resolve()
    corpus_path = corpus_path.resolve()
    receipt_path = receipt_path.resolve()
    stat = corpus_path.stat()
    actual_corpus_sha256 = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
    actual_index_hashes = {
        name: hashlib.sha256((manifest_path.parent / name).read_bytes()).hexdigest()
        for name in ("faiss.index", "chunks.json", "manifest.json")
    }
    expected_manifest_id = expected_manifest.manifest_id
    if binding.expected_resource_manifest_id != expected_manifest_id:
        raise ValueError("relocation binding is for a different policy resource manifest")
    if binding.historical_corpus_path != stored_manifest.get("corpus_path"):
        raise ValueError("historical corpus path differs from the stored index manifest")
    if binding.current_corpus_path != str(corpus_path):
        raise ValueError("current corpus path differs from the explicit relocation target")
    if binding.historical_manifest_path == str(manifest_path):
        raise ValueError("historical manifest location must differ from current location")
    if binding.current_manifest_path != str(manifest_path):
        raise ValueError("current manifest path differs from the explicit relocation target")
    if current_manifest.get("corpus_path") != str(corpus_path):
        raise ValueError("current index manifest names a different corpus path")
    if binding.historical_corpus_mtime != stored_manifest.get("corpus_mtime"):
        raise ValueError("historical corpus timestamp differs from the stored index manifest")
    if binding.current_corpus_mtime != stat.st_mtime:
        raise ValueError("current corpus timestamp differs from the relocation binding")
    if current_manifest.get("corpus_mtime") != stat.st_mtime:
        raise ValueError("current index manifest timestamp differs from the corpus file")

    relocatable_fields = {"corpus_path", "corpus_mtime"}
    if set(stored_manifest) != set(current_manifest):
        raise ValueError("stored index manifest fields differ from the current manifest schema")
    differences = {
        key for key in stored_manifest
        if stored_manifest[key] != current_manifest[key]
    }
    if differences - relocatable_fields:
        raise ValueError("non-relocation index manifest fields differ: " + ", ".join(sorted(differences - relocatable_fields)))
    if not differences:
        raise ValueError("index manifest has no path or timestamp relocation to bind")

    if binding.manifest_version != current_manifest.get("version"):
        raise ValueError("index manifest version differs from relocation binding")
    if binding.chunk_size != current_manifest.get("chunk_size"):
        raise ValueError("index chunk size differs from relocation binding")
    if binding.embedding_model != current_manifest.get("embedding_model"):
        raise ValueError("index embedding model setting differs from relocation binding")
    if binding.index_version != current_manifest.get("index_version"):
        raise ValueError("index version differs from relocation binding")
    if (binding.corpus_sha256 != corpus_sha256 or binding.corpus_sha256 != actual_corpus_sha256
            or binding.corpus_sha256 != current_manifest.get("corpus_sha256")):
        raise ValueError("corpus content differs from relocation binding")
    if binding.corpus_size != stat.st_size or binding.corpus_size != current_manifest.get("corpus_size"):
        raise ValueError("corpus size differs from relocation binding")
    if index_hashes != actual_index_hashes:
        raise ValueError("observed index file hashes differ from the files at the relocated index path")
    if binding.faiss_sha256 != actual_index_hashes.get("faiss.index"):
        raise ValueError("FAISS index content differs from relocation binding")
    if binding.chunks_sha256 != actual_index_hashes.get("chunks.json"):
        raise ValueError("index chunks content differs from relocation binding")
    if binding.manifest_sha256 != actual_index_hashes.get("manifest.json"):
        raise ValueError("stored index manifest content differs from relocation binding")
    receipt_digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    if binding.receipt_sha256 != receipt_digest:
        raise ValueError("index receipt bytes differ from relocation binding")
    if json.loads(receipt_path.read_text(encoding="utf-8")) != receipt:
        raise ValueError("loaded index receipt differs from bytes at the relocated receipt path")
    if receipt != expected_receipt:
        raise ValueError("index receipt does not validate against current corpus, vectors, chunks, and model")
    if binding.receipt_fingerprint != content_id(receipt):
        raise ValueError("index receipt fingerprint differs from relocation binding")
    if binding.embedding_model_sha256 != embedding_model_sha256:
        raise ValueError("embedding model content differs from relocation binding")
    if binding.nli_model_sha256 != nli_model_sha256:
        raise ValueError("NLI model content differs from relocation binding")
    if binding.semantic_configuration_sha256 != semantic_configuration_sha256:
        raise ValueError("semantic adapter settings differ from relocation binding")

    expected_rows = {
        (r.kind, r.resource_id): r.sha256
        for verifier in expected_manifest.verifiers for r in verifier.resources
    }
    observed_rows = {
        (r.kind, r.resource_id): r.sha256
        for verifier in observed_manifest.verifiers for r in verifier.resources
    }
    mapped_key = ("index", "evidence-index")
    if binding.historical_index_fingerprint != expected_rows.get(mapped_key):
        raise ValueError("historical index fingerprint differs from the policy artifact")
    if binding.current_index_fingerprint != observed_rows.get(mapped_key):
        raise ValueError("current index fingerprint differs from observed resources")
    if binding.current_index_fingerprint == binding.historical_index_fingerprint:
        raise ValueError("relocation binding does not describe a fingerprint change")
    expected_without_index = {k: v for k, v in expected_rows.items() if k != mapped_key}
    observed_without_index = {k: v for k, v in observed_rows.items() if k != mapped_key}
    if expected_without_index != observed_without_index:
        mismatches = sorted(f"{kind}:{name} expected={expected_without_index.get((kind, name))} "
            f"observed={observed_without_index.get((kind, name))}"
            for kind, name in set(expected_without_index) | set(observed_without_index)
            if expected_without_index.get((kind, name)) != observed_without_index.get((kind, name)))
        raise ValueError("non-relocation resource fingerprints differ: " + ", ".join(mismatches))

    return {
        "version": binding.version,
        "binding_id": binding.binding_id,
        "expected_resource_manifest_id": expected_manifest_id,
        "historical_resource_manifest_id": expected_manifest_id,
        "observed_resource_manifest_id": observed_manifest.manifest_id,
        "historical_manifest_path": binding.historical_manifest_path,
        "current_manifest_path": binding.current_manifest_path,
        "historical_corpus_path": binding.historical_corpus_path,
        "current_corpus_path": binding.current_corpus_path,
        "historical_corpus_mtime": binding.historical_corpus_mtime,
        "current_corpus_mtime": binding.current_corpus_mtime,
        "historical_index_fingerprint": binding.historical_index_fingerprint,
        "current_index_fingerprint": binding.current_index_fingerprint,
        "verified_corpus_sha256": corpus_sha256,
        "verified_faiss_sha256": index_hashes["faiss.index"],
        "verified_chunks_sha256": index_hashes["chunks.json"],
        "verified_embedding_model_sha256": embedding_model_sha256,
        "verified_nli_model_sha256": nli_model_sha256,
        "verified_receipt_fingerprint": content_id(receipt),
        "verified_semantic_configuration_sha256": semantic_configuration_sha256,
        "authorized_resource_ids": ["index:evidence-index"],
    }
