"""Explicit, lazy research_v1 recording binding.

This module is inactive unless a request selects ``research_v1_factory`` and
``RESEARCH_V1_RECORDING_BINDING_CONFIG`` names an explicit binding document.
The binding document selects an adapter configuration; it does not itself
authorize collection or establish live resource/service readiness.

Verifier construction is deferred to ``LazyVerifierPool.get``. The factory
performs local setup inspection only. The collector's observer snapshots then
repeat local inspection and compare a live service observation. The collector
currently resolves a lazy constructor before writing the attempt start intent;
constructor failures therefore occur before verifier dispatch/start is
journaled. This module preserves that lifecycle and does not claim its
durability properties beyond the collector's existing platform contract.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Literal

from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel
from app.game.offline.calibration import MeasurementSetup, Text
from app.game.offline.collection import LazyVerifierPool
from app.game.resource_provenance import ResourceManifest


CONFIG_ENV = "RESEARCH_V1_RECORDING_BINDING_CONFIG"
VERIFIER_ROSTER = ("semantic", "evidence", "rule", "confidence")
VerifierName = Literal["semantic", "evidence", "rule", "confidence"]


class ResearchV1RecordingBinding(FrozenModel):
    """Explicit selector for a research adapter configuration.

    This is a configuration link, not an approval or a service/resource
    observation. ``dataset_id`` and ``split`` are declared target metadata;
    the zero-argument factory cannot validate them against its invoking request.
    The referenced adapter file must be supplied by the runtime owner; this
    implementation creates no production config or resource IDs.
    """

    version: Literal["research_v1_recording_binding_v1"]
    binding_id: Text
    dataset_id: Literal["research_v1_exploratory_v1"] = Field(
        description="Declared binding target only; not validated against the invoking RecordingRequest."
    )
    split: Literal["development"] = Field(
        description="Declared binding target only; not validated against the invoking RecordingRequest."
    )
    adapter_configuration_path: Text
    verifier_roster: tuple[VerifierName, ...] = Field(
        default=("semantic", "evidence", "rule", "confidence"), min_length=4, max_length=4
    )

    @model_validator(mode="after")
    def exact_roster(self):
        if set(self.verifier_roster) != set(VERIFIER_ROSTER):
            raise ValueError("research_v1 binding must declare the complete four-verifier roster")
        return self


def resolve_research_configuration(path: str | Path | None = None):
    """Resolve a binding only from an explicit argument or dedicated env var.

    Relative adapter paths are resolved against the binding document's
    directory. No root ``adapter.json`` fallback is attempted.
    """
    selected = path if path is not None else os.environ.get(CONFIG_ENV)
    if selected is None or not str(selected).strip():
        raise ValueError(f"supply a research binding path or set {CONFIG_ENV}; no fallback is used")

    binding_path = Path(selected).expanduser().resolve()
    try:
        raw = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid explicit research binding configuration: {binding_path}") from exc
    binding = ResearchV1RecordingBinding.model_validate(raw)

    adapter_path = Path(binding.adapter_configuration_path).expanduser()
    if not adapter_path.is_absolute():
        adapter_path = binding_path.parent / adapter_path
    adapter_path = adapter_path.resolve()
    if not adapter_path.is_file():
        raise ValueError(f"explicit adapter configuration does not exist: {adapter_path}")

    from app.benchmark.project_adapter import AdapterConfiguration

    try:
        adapter = AdapterConfiguration.model_validate_json(adapter_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"explicit adapter configuration is invalid: {adapter_path}") from exc
    return binding, binding_path, adapter, adapter_path


def make_lazy_verifier_pool(builders: dict[str, Callable[[], object]]) -> LazyVerifierPool:
    """Build a named lazy pool while enforcing the full research roster."""
    if set(builders) != set(VERIFIER_ROSTER):
        raise ValueError("research_v1 factory builders must cover the complete declared roster")
    return LazyVerifierPool(builders)


class ResearchLazyVerifierPool(LazyVerifierPool):
    """Lazy pool that reports only actually resolved instances to its observer."""

    def __init__(self, builders, observer):
        super().__init__(builders)
        self._observer = observer

    def get(self, name):
        verifier = super().get(name)
        self._observer._record_constructed_instance(verifier)
        return verifier


class ResearchRosterObserver:
    """Roster-level observer independent of constructed verifier instances.

    The expected setup must contain exactly the four names in
    ``VERIFIER_ROSTER``. This follows ``ResourceManifest.require_candidates``
    semantics: the captured roster must match exactly, with no missing or
    undeclared verifier entries.

    ``inspect_local`` must return the existing project adapter report shape.
    If ``observe_live_service`` is supplied, each snapshot compares the live
    metadata observation with the saved service identity in that report.
    Omitting it is useful for synthetic/static checks and leaves live readiness
    explicitly NOT_CHECKED.
    """

    def __init__(
        self,
        configuration,
        expected_setup: MeasurementSetup,
        *,
        inspect_local: Callable | None = None,
        observe_live_service: Callable | None = None,
        active_instance_attestor: Callable | None = None,
    ):
        self.configuration = configuration
        self.expected_setup = MeasurementSetup.model_validate(expected_setup)
        self.expected_setup.resources.require_candidates(VERIFIER_ROSTER)
        if inspect_local is None:
            from app.benchmark.project_adapter import inspect_setup
            inspect_local = inspect_setup
        self._inspect_local = inspect_local
        self._observe_live_service = observe_live_service
        self._active_instance_attestor = active_instance_attestor
        self._constructed_instances = {}
        self.last_evidence = {
            "configuration": "DECLARED",
            "local_resources": "NOT_CHECKED",
            "live_service": "NOT_CHECKED",
            "active_instances": "NOT_ATTESTED",
        }

    def snapshot(self) -> ResourceManifest:
        report = self._inspect_local(self.configuration)
        if not report.get("ready") or report.get("observed_setup") is None:
            self.last_evidence = {**self.last_evidence, "local_resources": "BLOCKED"}
            raise ValueError("research_v1 local resource inspection is not ready: " +
                             json.dumps(report.get("blockers", [])))
        observed = MeasurementSetup.model_validate(report["observed_setup"])
        if observed.fingerprint != self.expected_setup.fingerprint:
            self.last_evidence = {**self.last_evidence, "local_resources": "MISMATCH"}
            raise ValueError("research_v1 local setup changed from the factory setup")

        live_status = "NOT_CHECKED"
        if self._observe_live_service is not None:
            saved = report.get("inventory", {}).get("service")
            current = self._observe_live_service(self.configuration)
            if hasattr(current, "model_dump"):
                current = current.model_dump(mode="json")
            if current != saved:
                self.last_evidence = {**self.last_evidence, "local_resources": "MATCH",
                                      "live_service": "MISMATCH"}
                raise ValueError("research_v1 live service differs from the saved observation")
            live_status = "MATCH"

        self.last_evidence = {
            "configuration": "DECLARED",
            "local_resources": "MATCH",
            "live_service": live_status,
            "active_instances": "NOT_ATTESTED",
        }
        return observed.resources

    def _record_constructed_instance(self, verifier) -> None:
        """Internal callback from ResearchLazyVerifierPool after successful get."""
        name = getattr(verifier, "name", None)
        if name not in VERIFIER_ROSTER:
            raise ValueError("constructed verifier is outside the declared research roster")
        self._constructed_instances[name] = verifier

    def attest_constructed_instance(self, verifier) -> str:
        """Optionally attest an instance already returned by the research lazy pool."""
        name = getattr(verifier, "name", None)
        if name not in VERIFIER_ROSTER or self._constructed_instances.get(name) is not verifier:
            raise ValueError("instance was not constructed by this research lazy pool")
        if self._active_instance_attestor is None:
            return "NOT_ATTESTED"
        result = self._active_instance_attestor(verifier, self.configuration, self.expected_setup)
        if result is not True:
            raise ValueError(f"active verifier instance was not attested: {name}")
        self.last_evidence = {**self.last_evidence, "active_instances": "PARTIALLY_ATTESTED"}
        return "ATTESTED"


def _production_builders(configuration, relocation_proof=None):
    """Create per-name closures; heavyweight imports/loads occur only on get()."""
    from app.benchmark.project_adapter import local_path

    shared = {}

    def embedding():
        if "embedding" not in shared:
            from sentence_transformers import SentenceTransformer
            shared["embedding"] = SentenceTransformer(
                str(local_path(configuration.embedding_snapshot)), device="cpu", local_files_only=True
            )
        return shared["embedding"]

    def nli():
        if "nli" not in shared:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            tokenizer = AutoTokenizer.from_pretrained(
                str(local_path(configuration.nli_snapshot)), local_files_only=True
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                str(local_path(configuration.nli_snapshot)), local_files_only=True
            )
            shared["nli"] = pipeline("text-classification", model=model, tokenizer=tokenizer,
                                     top_k=None, device=-1)
        return shared["nli"]

    def semantic():
        from app.verifiers.semantic_verifier import SemanticVerifier
        return SemanticVerifier(model=embedding())

    def evidence():
        from app.verifiers.evidence_retriever import EvidenceRetriever
        from app.verifiers.evidence_verifier import EvidenceVerifier
        retriever = EvidenceRetriever(corpus_path=str(local_path(configuration.corpus_path)),
            chunk_size=configuration.chunk_size, index_dir=local_path(configuration.index_dir),
            model=embedding(), relocation_proof=relocation_proof)
        if (retriever.index.ntotal != len(retriever.chunks) or
                retriever.index.d != embedding().get_sentence_embedding_dimension()):
            raise ValueError("loaded evidence index dimensions/counts differ from local resources")
        return EvidenceVerifier(corpus_path=str(local_path(configuration.corpus_path)),
                                retriever=retriever, nli=nli())

    def rule():
        from app.verifiers.rule_verifier import RuleVerifier
        return RuleVerifier()

    def confidence():
        from app.verifiers.confidence_verifier import ConfidenceVerifier
        from app.verifiers.self_consistency import (AgreementLabeler, OllamaSampler,
                                                    SelfConsistencyJudge)
        provider = SelfConsistencyJudge(
            sampler=OllamaSampler(url=configuration.ollama_url, model=configuration.ollama_model,
                                  temperature=configuration.temperature, timeout=configuration.timeout),
            labeler=AgreementLabeler(nli=nli()), n_samples=configuration.n_samples)
        return ConfidenceVerifier(judgment_provider=provider)

    return {"semantic": semantic, "evidence": evidence, "rule": rule, "confidence": confidence}


def research_v1_factory():
    """Offline collector entry point selected only by an explicit request.

    The initial setup inspection is local/static and does not contact a
    service. The returned observer performs live service metadata comparison
    only when the collector explicitly calls ``snapshot()`` during collection.
    """
    binding, _, configuration, _ = resolve_research_configuration()
    from app.benchmark.project_adapter import inspect_setup, observe_service

    report = inspect_setup(configuration)
    if not report.get("ready") or report.get("observed_setup") is None:
        raise ValueError("research_v1 local resource preflight failed: " +
                         json.dumps(report.get("blockers", [])))
    setup = MeasurementSetup.model_validate(report["observed_setup"])
    setup.resources.require_candidates(binding.verifier_roster)
    if set(binding.verifier_roster) != set(VERIFIER_ROSTER):
        raise ValueError("research_v1 binding roster differs from the supported roster")

    observer = ResearchRosterObserver(configuration, setup, inspect_local=inspect_setup,
                                      observe_live_service=observe_service)
    builders = _production_builders(configuration, report.get("relocation_proof"))
    pool = ResearchLazyVerifierPool(builders, observer)
    return pool, setup, observer
