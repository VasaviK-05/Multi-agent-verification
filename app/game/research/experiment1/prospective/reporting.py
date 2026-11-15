"""Explicit research reporting only. No fitting, dispatch, path discovery or sampling."""
import hashlib
import json

from app.game.models import content_id
from app.game.offline.records import Partition
from app.game.research.__main__ import _object, _nonfinite
from app.game.research.experiment1.runner import atomic_cube
from app.game.research.experiment1.metrics import (
    Statistics, point_report, paired_point_differences, bootstrap_report,
)
from app.game.resource_provenance import VerifierResources
from .models import Manifest, Authorizations
from .readiness import readiness


def _gate(manifest, cohort, stage, actual_commit, actual_source_fingerprint, authorizations):
    status = readiness(manifest, actual_commit=actual_commit,
        actual_source_fingerprint=actual_source_fingerprint, authorizations=authorizations)
    row = next(r for r in status['cohorts'] if r['cohort'] == cohort)['stages'][stage]
    if not row['ready']:
        raise ValueError('prospective study blocked: ' + '; '.join(b['code'] for b in row['blockers']))


def _results(manifest, c, role, cube, payload_sha256=None):
    points = point_report(cube)
    stats = Statistics(confidence_level=.95, resamples=manifest.statistics.resamples,
                       seed=manifest.statistics.seed)
    # Every method shares this one cube: no alternative references, labels, roster or failures.
    rows = [dict(cohort=c.name, method=p['method'], attack_id=a['attack_id'],
                 attack_kind=a['attack_kind'], dependency_group_id=a['dependency_group_id'],
                 **a['metrics']) for p in points for a in p['attacks']]
    return dict(version='prospective_experiment1_report_v1', study_id=manifest.study_id,
        manifest_id=manifest.manifest_id, protocol_id=manifest.protocol_id, cohort=c.name, role=role,
        evidence_kind=c.training.evidence_kind, policy_id=c.frozen.comparison.full_artifact.policy.policy_id,
        comparison_id=c.frozen.comparison.comparison_id, cube_id=content_id(cube.model_dump(mode='json')),
        payload_sha256=payload_sha256,
        provenance=dict(source_commit=manifest.source_commit, source_fingerprint=manifest.source_fingerprint,
            environment=manifest.reporting_environment, statistics=manifest.statistics.model_dump(mode='json'),
            collection_id=manifest.collection_id(c.name), fitting_id=manifest.fitting_id(c.name),
            dataset_ids=dict(c.population.dataset_ids), population_source_sha256=c.population.source_sha256,
            training_manifest_id=c.training.manifest_id, resources=c.resources.model_dump(mode='json'),
            choices=c.choices.model_dump(mode='json'), cost_units=cube.cost_units,
            attack_scope='offline report-level corruption; not actual evidence poisoning',
            attacks=[a.model_dump(mode='json') for a in cube.attacks],
            strategies=[s.model_dump(mode='json') for s in c.frozen.comparison.full_artifact.policy.strategies],
            methods=[m.model_dump(mode='json') for m in cube.methods],
            specification_id=c.frozen.specification.specification_id,
            contract_id=content_id(c.frozen.specification.contract.model_dump(mode='json'))),
        metrics=points, publication_rows=rows,
        paired_differences=paired_point_differences(points), uncertainty=bootstrap_report(cube, stats),
        unavailable_methods=[m.model_dump(mode='json') for m in c.frozen.comparison.unavailable_methods],
        development_floor=c.choices.development_coverage_floor,
        heldout_coverage_interpretation='Observed outcome, not a guaranteed or retuned constraint',
        primary_metric='worst_case_expected_loss',
        metric_semantics=dict(worst_case_expected_loss='max_attack_expected_decision_validation_loss',
            worst_case_total_loss='max_attack_expected_validation_plus_resource_cost',
            legacy_worst_case_expected_loss='cost_inclusive; map to worst_case_total_loss, never join by name'),
        fairness=dict(common_inputs=True, common_feasible_rows=True, common_execution_contract=True,
            uniform_reweighted=False, exact_probabilities=True, empirical_baseline_selection=False))


def report_development(manifest, cohort, *, actual_commit, actual_source_fingerprint, authorizations):
    manifest = Manifest.model_validate(manifest)
    auth = Authorizations.model_validate(authorizations)
    _gate(manifest, cohort, 'final_test_authorization_review', actual_commit, actual_source_fingerprint, auth)
    c = manifest.cohort(cohort)
    return _results(manifest, c, 'development', atomic_cube(c.frozen, 'development'))


def report_final(manifest, cohort, *, actual_commit, actual_source_fingerprint,
                 authorizations, payload_loader):
    """Check an EXTERNAL exact-manifest release before invoking the caller's loader.

    The loader must return the exact released UTF-8 Partition bytes. The readiness
    checker never accepts this loader, follows a payload path, or sees outcomes.
    Approval records are trusted external decisions, not cryptographic signatures.
    """
    manifest = Manifest.model_validate(manifest)
    auth = Authorizations.model_validate(authorizations)
    _gate(manifest, cohort, 'final_test_scoring', actual_commit, actual_source_fingerprint, auth)
    c = manifest.cohort(cohort)
    release = next(r for r in auth.releases if r.cohort == cohort)
    raw = payload_loader()
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != release.payload_sha256:
        raise ValueError('released payload SHA-256 mismatch')
    data = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_nonfinite)
    final = c.training.final_test_reservation.validate_payload(Partition.model_validate(data))
    expected = {m.example_id: m for m in c.population.members if m.role == 'final_test'}
    names = {v.verifier_name for v in c.candidates}
    for e in final.examples:
        m = expected[e.example_id]
        reference = hashlib.sha256(e.reference.encode()).hexdigest() if e.reference else None
        if (e.label_method, e.label_source, reference) != (m.label.method, m.label.source, m.reference_sha256):
            raise ValueError('released label provenance or reference differs from approved population')
        if {a.verifier_name for a in e.attempts} != names or any(a.state == 'missing' for a in e.attempts):
            raise ValueError('incomplete released verifier recordings')
        if e.execution_configuration_id != c.resources.manifest_id:
            raise ValueError('released resource configuration mismatch')
        for a in e.attempts:
            if a.observed_resources_json is None:
                raise ValueError('released resource observation missing')
            c.resources.require_observation(VerifierResources.model_validate_json(a.observed_resources_json))
    cube = atomic_cube(c.frozen, 'final_test', final_partition=final)
    return _results(manifest, c, 'final_test', cube, release.payload_sha256)
