"""Narrow source review capsule, separate from resource/activation permission.

An attestation here proves the exact reviewed source transition only. It never
returns a historical ResourceManifest, excuses model/service differences, or
authorizes execution. A caller must still validate actual resources and objects.
"""
import ast
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_capsule(capsule, root, *, policy_id, observed_manifest_id):
    """Bind source review to one policy, exact tree, and observed resource ID."""
    if capsule['version'] != 'reviewed_er_source_transition_v1':
        raise ValueError('unsupported source transition')
    if policy_id != capsule['policy_id'] or observed_manifest_id != capsule['observed_manifest_id']:
        raise ValueError('source transition policy/resource binding differs')
    payload = {k: v for k, v in capsule.items() if k != 'capsule_id'}
    if digest(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()) != capsule['capsule_id']:
        raise ValueError('source transition content identity differs')
    root = Path(root).resolve()
    for path, expected in capsule['target_files'].items():
        target = (root / path).resolve()
        if not target.is_relative_to(root) or digest(target.read_bytes()) != expected:
            raise ValueError('unreviewed required source: ' + path)
    if capsule['execution_authorized'] is not False:
        raise ValueError('source capsule cannot authorize execution')
    return dict(capsule_id=capsule['capsule_id'], policy_id=policy_id,
                observed_manifest_id=observed_manifest_id, source_review_verified=True,
                execution_authorized=False)


def method_invariants(old_source, new_source, class_name, permitted_methods):
    """Compare every existing class member except explicitly reviewed load gates."""
    def members(source):
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        return {n.name: ast.dump(n, include_attributes=False) for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    old, new = members(old_source), members(new_source)
    changed = {n for n in old.keys() | new.keys() if old.get(n) != new.get(n)}
    if changed - set(permitted_methods):
        raise ValueError('verification semantics changed outside reviewed gates: ' + repr(sorted(changed)))
    return sorted(changed)


def verify_er_transition(capsule, root, *, policy_id, expected, observed,
                         old_configuration, new_configuration, selector, native_pool):
    """Verify exact source/config transition on non-relocated required resources.

    Returns both identities, never a rewritten historical manifest. Index deltas
    require a separate composed relocation contract and deliberately fail here.
    This is not a singleton/full-roster authorization or activation mechanism.
    """
    from app.game.models import content_id
    from app.game.resource_provenance import ResourceManifest
    if capsule.get('capsule_id') != 'd78864a6cceb0262408617c724c8789f93811f9b72aa87856abb57dc49d24993':
        raise ValueError('unreviewed transition capsule')
    check_capsule(capsule, root, policy_id=policy_id,
                  observed_manifest_id=capsule['observed_manifest_id'])
    expected = ResourceManifest.model_validate(expected)
    observed = ResourceManifest.model_validate(observed)
    if expected.manifest_id != capsule['expected_scope_id']:
        raise ValueError('different historical scoped contract')
    if {v.verifier_name for v in observed.verifiers} != {'evidence', 'rule'}:
        raise ValueError('E/R transition requires exact scope')
    native_pool = tuple(native_pool)
    if len(native_pool) != 2 or {v.name for v in native_pool} != {'evidence', 'rule'}:
        raise ValueError('exact native E/R pool required')
    if any(selector.resolve(v.name) is not v for v in native_pool):
        raise ValueError('active native objects differ')
    old = dict(old_configuration)
    new = dict(new_configuration)
    # No path/service/model/settings exception: the only new field may be null.
    if new.pop('resource_relocation_binding', None) is not None or new != old:
        raise ValueError('configuration changes require separate relocation/settings proof')
    def entries(manifest):
        return {(v.verifier_name, r.kind, r.resource_id): r.sha256
                for v in manifest.verifiers for r in v.resources}
    original, actual = entries(expected), entries(observed)
    if original.keys() != actual.keys():
        raise ValueError('required resource inventory differs')
    source_rows = capsule['implementation_transitions']
    for key, historical in original.items():
        name, kind, resource = key
        if kind == 'implementation':
            permitted = source_rows[name]
            if historical != permitted['old'] or actual[key] != permitted['new']:
                raise ValueError('unreviewed implementation transition')
        elif kind == 'configuration':
            if historical != content_id(old) or actual[key] != content_id(new_configuration):
                raise ValueError('configuration fingerprint differs')
        elif actual[key] != historical:
            raise ValueError('required resource differs: ' + resource)
    return dict(version='verified_nonrelocated_er_transition_v1', capsule_id=capsule['capsule_id'],
        policy_id=policy_id, historical_scope_id=expected.manifest_id,
        observed_scope_id=observed.manifest_id, active_instances_checked=True,
        operational_activation=False)
