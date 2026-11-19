"""Opt-in baseline cost collection; never invoked by application startup.

All eligible candidates are measured, including potential fallbacks. This is a
cost study, not a validation campaign or a claim of production team execution.
"""
import argparse
import json
from pathlib import Path
from typing import Literal

from app.analysis.question_analyzer import QuestionAnalyzer
from app.benchmark.prepare_collection import PreparationInput
from app.benchmark.baseline_setup import observe_baseline_setup, INITIALIZATION, NAMES
from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.offline.calibration import MeasurementSetup, MeasurementInput, AttemptMeasurement, read_json
from app.game.offline.timing import TimedVerifier
from app.selection.capabilities import BUILTIN_CAPABILITIES
from app.selection.baseline_resources import BaselineVerifierSelector


class BaselineCollectionRequest(FrozenModel):
    version: Literal["baseline_collection_v1"] = "baseline_collection_v1"
    collection_authorized: Literal[True]
    expected_setup: MeasurementSetup
    preparation: PreparationInput
    index_receipt_path: str
    service_observation_path: str


def collect_baseline(request, selector, observe_setup, attempts, events):
    """Caller owns partial records. Exceptions propagate; no retries or feedback.

    The selector is real; tests may supply controlled verifier instances. Observe
    before/after each call outside TimedVerifier, preserving its timing boundary.
    """
    request = BaselineCollectionRequest.model_validate(request)
    expected = request.expected_setup
    if expected.environment.get("initialization") != INITIALIZATION:
        raise ValueError("collection_requires_baseline_setup")
    if expected.evidence_kind == "empirical" and (type(selector) is not BaselineVerifierSelector
                                                 or not selector.uses_default_factory):
        raise ValueError("empirical_baseline_collection_requires_default_factory")

    def check():
        try:
            matches = MeasurementSetup.model_validate(observe_setup()) == expected
        except BaseException:
            events.append(dict(event="resource_drift", eligible_for_calibration=False))
            raise
        if not matches:
            events.append(dict(event="resource_drift", eligible_for_calibration=False))
            raise ValueError("baseline_collection_setup_changed")

    check()
    constructed = set()
    analyzer = QuestionAnalyzer(mode="heuristic")
    for example in request.preparation.examples:
        plan = selector.plan(analyzer.analyze(example.question), example.context)
        expected.resources.require_candidates(c.verifier_name for c in plan.candidates)
        for candidate in plan.candidates:
            if not candidate.eligible:
                events.append(dict(event="excluded", run_id=example.run_id,
                    verifier_name=candidate.verifier_name, reason=candidate.exclusion_reason))
        for name in plan.initial_selected + plan.fallback:
            # Deliberately outside the attempt timer. Do not move into a proxy.
            try:
                verifier = selector.resolve(name)
            except BaseException as exc:
                events.append(dict(event="construction_failed", verifier_name=name,
                                   run_id=example.run_id, error_type=type(exc).__name__,
                                   verify_invoked=False))
                raise
            if name not in constructed:
                events.append(dict(event="constructed", verifier_name=name, run_id=example.run_id,
                    construction_order=len(constructed), initialization=INITIALIZATION,
                    setup_fingerprint=expected.fingerprint))
                constructed.add(name)
            check()
            resource = next(v for v in expected.resources.verifiers if v.verifier_name == name)
            metadata = {k: getattr(example, k) for k in ("run_id", "example_id", "split_identity",
                "question_id", "dataset_id", "role", "purpose")}
            metadata.update(content_identity=content_id([example.question, example.answer, example.context]),
                setup_fingerprint=expected.fingerprint,
                verifier_fingerprint=content_id(resource.model_dump(mode="json")))
            events.append(dict(event="dispatch", run_id=example.run_id, verifier_name=name,
                initial_selected=list(plan.initial_selected), fallback=list(plan.fallback)))
            try:
                TimedVerifier(verifier, [], measurement_metadata=metadata, measurements=attempts).verify(
                    example.question, example.answer, example.context)
            except BaseException:
                # Preserve the provider's original exception after recording any
                # additional provenance failure in the diagnostic event log.
                try:
                    check()
                except BaseException:
                    pass
                raise
            else:
                check()


def measurement_input(request, attempts, events):
    if any(e.get("eligible_for_calibration") is False for e in events):
        raise ValueError("drifted_attempts_are_diagnostic_only")
    return MeasurementInput(setup=request.expected_setup,
        permitted_datasets=request.preparation.permitted_datasets,
        preparation_authorization=request.preparation.preparation_authorization,
        attempts=tuple(AttemptMeasurement.model_validate(a) for a in attempts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="Explicitly authorize collection, never startup")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("collection requires --execute and an authorized request")
    request = BaselineCollectionRequest.model_validate(read_json(args.request))
    if request.expected_setup.evidence_kind != "empirical":
        raise ValueError("CLI requires empirical setup")
    request.expected_setup.resources.require_candidates(NAMES)
    if args.output.resolve() == args.audit_output.resolve():
        raise ValueError("measurement and audit paths must differ")
    # Both outputs must be new; reserve before resolving any live verifier.
    if args.output.exists() or args.audit_output.exists():
        raise FileExistsError("use fresh baseline collection paths")
    attempts, events = [], []
    with args.output.open("x", encoding="utf-8") as output, args.audit_output.open("x", encoding="utf-8") as audit:
        selector = BaselineVerifierSelector(capabilities=BUILTIN_CAPABILITIES)
        from app.selection.baseline_resources import load_baseline_evidence_configuration
        selector.configure_baseline_evidence(load_baseline_evidence_configuration())
        observe = lambda: observe_baseline_setup(index_receipt_path=request.index_receipt_path,
                                                 service_observation_path=request.service_observation_path)
        try:
            collect_baseline(request, selector, observe, attempts, events)
        finally:
            valid = bool(attempts) and not any(e.get("eligible_for_calibration") is False for e in events)
            if valid:
                output.write(measurement_input(request, attempts, events).model_dump_json(indent=2))
            audit.write(json.dumps(dict(setup_fingerprint=request.expected_setup.fingerprint,
                events=events, attempts=attempts, measurements_exported=valid,
                initialization=INITIALIZATION), indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
