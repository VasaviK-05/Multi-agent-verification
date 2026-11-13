"""Read-only research_v1 eligibility integrity and source-identity checks.

No verifier, recording, policy, database or dataset generator is imported/run.
Artifact strings are data. Only fixed approved members and permitted source
members are opened; repository paths in the manifest are never followed.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

MANIFEST_ID = 'research_v1_exploratory_eligibility_approved_v1'
EXPECTED_BODY_SHA256 = 'f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d'
LOGICAL_MANIFEST = f'evaluation/artifacts/person1/{MANIFEST_ID}/eligibility_manifest.json'
OUTPUTS = ('development_eligible.jsonl', 'development_excluded.jsonl',
           'group_assignments.jsonl', 'label_validation.jsonl', 'leakage_audit.json')


class EligibilityCompatibilityError(ValueError):
    pass


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _require(condition, message):
    if not condition:
        raise EligibilityCompatibilityError(message)


def _member(archive, name):
    matches = [i for i in archive.infolist() if i.filename == name and not i.is_dir()]
    _require(len(matches) == 1, 'missing or duplicate artifact member: ' + name)
    return archive.read(matches[0])


def verify_archive(path):
    """Authenticate the exact user-designated body and all five output bytes."""
    with zipfile.ZipFile(path) as archive:
        roots = [f'artifacts/person1/{MANIFEST_ID}/',
                 f'evaluation/artifacts/person1/{MANIFEST_ID}/']
        roots = [r for r in roots if r + 'eligibility_manifest.json' in archive.namelist()]
        _require(len(roots) == 1, 'approved manifest must have exactly one recognized root')
        root = roots[0]
        raw = _member(archive, root + 'eligibility_manifest.json')
        manifest = json.loads(raw)
        body = {k: v for k, v in manifest.items() if k != 'eligibility_manifest_sha256'}
        body_hash = sha256((json.dumps(body, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())
        _require(body_hash == EXPECTED_BODY_SHA256 == manifest.get('eligibility_manifest_sha256'),
                 'approved manifest body SHA-256 differs')
        sidecar = _member(archive, root + 'eligibility_manifest.file_sha256.txt')
        _require(sha256(raw) == sidecar.decode('ascii').strip(), 'complete-file sidecar SHA-256 differs')
        _require(manifest.get('manifest_id') == MANIFEST_ID and manifest.get('approved') is True,
                 'manifest identity/eligibility approval differs')
        _require(manifest.get('approval', {}).get('scope') == 'Development eligibility for research_v1_exploratory_v1 only',
                 'approval scope differs')
        for flag in ('collection_authorized', 'recording_authorized', 'final_test_authorized', 'frozen_protocol'):
            _require(manifest.get(flag) is False, 'unexpected authorization: ' + flag)
        _require(manifest.get('semantic_clearance') == 'NOT_CLAIMED', 'semantic clearance must remain unresolved')
        _require(set(manifest['output_sha256']) == set(OUTPUTS), 'supporting output roster differs')
        outputs = {}; hashes = {}
        for name in OUTPUTS:
            data = _member(archive, root + name)
            hashes[name] = sha256(data)
            _require(hashes[name] == manifest['output_sha256'][name], 'supporting SHA-256 differs: ' + name)
            outputs[name] = ([json.loads(line) for line in data.decode().splitlines() if line]
                             if name.endswith('.jsonl') else json.loads(data))
    eligible = outputs['development_eligible.jsonl']; excluded = outputs['development_excluded.jsonl']
    groups = outputs['group_assignments.jsonl']; labels = outputs['label_validation.jsonl']
    leakage = outputs['leakage_audit.json']
    ids = [r['candidate_id'] for r in eligible]
    _require(len(ids) == len(set(ids)) == manifest['counts']['eligible_candidates'] == 744,
             'approved candidates must be 744 unique stable IDs')
    by_group = defaultdict(list)
    for row in eligible:
        _require(row['eligible'] is True and row['partition'] == 'development' and
                 row['dataset_version'] == 'research_v1_exploratory_v1', 'candidate scope differs')
        _require(row['split_identity'] == row['related_group_id'], 'split/group identity differs')
        _require(row['human_verified'] is False and row['label_protocol'] == 'provisional_automated_labeling_v1',
                 'automated label provenance differs')
        _require(row.get('exclusion_reason') is None and row['exclusion_reasons'] == [], 'eligible row is excluded')
        by_group[row['related_group_id']].append(row)
    _require(len(by_group) == manifest['counts']['eligible_groups'] == 372, 'approved group count differs')
    _require(len({r['question_id'] for r in eligible}) == 372, 'questions must map to one approved group')
    benchmarks = Counter()
    for group in by_group.values():
        _require(len(group) == 2 and Counter(r['label_class'] for r in group) ==
                 {'VERIFIED_CORRECT': 1, 'SYNTHETIC_INCORRECT': 1}, 'group lacks exact binary pair')
        _require(len({r['question_id'] for r in group}) == len({r['benchmark'] for r in group}) == 1,
                 'group question/benchmark inconsistent')
        benchmarks[group[0]['benchmark']] += 1
    _require(benchmarks == {'GSM8K': 187, 'HotpotQA': 185}, 'benchmark group counts differ')
    _require(len(groups) == 387 and len({g['related_group_id'] for g in groups}) == 387,
             'pre-quarantine group inventory differs')
    selected_groups = {g['related_group_id'] for g in groups if g['eligible']}
    _require(selected_groups == set(by_group), 'group assignments and candidate roster differ')
    quarantined = set(leakage['quarantined_development_groups'])
    _require(len(quarantined) == 15 and not quarantined & set(by_group), 'quarantined groups admitted')
    _require({g['related_group_id'] for g in groups if not g['eligible']} == quarantined,
             'group exclusions and quarantine differ')
    _require(len(excluded) == manifest['counts']['excluded_rows'] == 375, 'exclusion row count differs')
    _require(Counter(r['exclusion_reason'] for r in excluded) == {
        'unresolved_not_a_binary_label': 332, 'shared_history_reference_context': 30, 'no_verified_gold': 13},
        'exclusion reasons differ')
    excluded_ids = {r['candidate_id'] for r in excluded if r['candidate_id'] is not None}
    _require(len(excluded_ids) == 362 and not excluded_ids & set(ids), 'eligible/excluded candidate identities overlap')
    label_index = {r['candidate_id']: r for r in labels}
    _require(len(labels) == len(label_index) == 1106, 'label validation inventory differs')
    for row in eligible:
        validation = label_index.get(row['candidate_id'], {})
        for field in ('benchmark', 'question_id', 'related_group_id', 'source_dataset_id',
                      'label_class', 'label_protocol', 'label_method', 'label_source', 'human_verified'):
            _require(validation.get(field) == row[field], 'label provenance link differs: ' + field)
        _require(validation.get('validation_status') == 'passed', 'approved label validation not passed')
    _require(leakage['semantic_clearance'] == 'NOT_CLAIMED' and
             leakage['exact_overlap'] == manifest['exact_overlap'], 'leakage audit binding differs')
    return {'manifest': manifest, 'eligible': eligible, 'excluded': excluded, 'groups': groups,
            'labels': labels, 'leakage': leakage, 'receipt': {
                'manifest_id': MANIFEST_ID, 'logical_manifest_path': LOGICAL_MANIFEST,
                'archive_root': root, 'manifest_body_sha256': body_hash,
                'manifest_file_sha256': sha256(raw), 'sidecar_file_sha256': sha256(sidecar),
                'supporting_sha256': hashes, 'archive_sha256': sha256(Path(path).read_bytes()),
                'eligibility_approved': True, 'collection_authorized': False,
                'recording_authorized': False, 'semantic_clearance': 'NOT_CLAIMED'}}


def verify_source_payloads(evidence, source_archive):
    """Join approved IDs to a separately supplied, hash-bound original source ZIP.

    The eligibility package alone does not contain a dispatch-ready input tuple.
    This does not select/serialize references or attest independent label truth.
    """
    with zipfile.ZipFile(source_archive) as archive:
        names = archive.namelist()
        def source_member(basename):
            matches = [n for n in names if PurePosixPath(n.replace('\\', '/')).name == basename]
            _require(len(matches) == 1, 'source member missing/ambiguous: ' + basename)
            return _member(archive, matches[0])
        manifest_raw = source_member('manifest.json'); source_manifest = json.loads(manifest_raw)
        _require(sha256(manifest_raw) == evidence['manifest']['source_manifest_sha256'], 'original source manifest differs')
        source = {}
        for name in ('development_candidates.jsonl', 'development_verifier_inputs.jsonl'):
            raw = source_member(name)
            _require(sha256(raw) == source_manifest['output_sha256'][name], 'original source output differs: ' + name)
            source[name] = [json.loads(line) for line in raw.decode().splitlines() if line]
    originals = {r['candidate_id']: r for r in source['development_candidates.jsonl']}
    inputs = {r['candidate_id']: r for r in source['development_verifier_inputs.jsonl']}
    _require(len(originals) == len(inputs) == 774, 'historical source inventory differs')
    labels = {r['candidate_id']: r for r in evidence['labels']}
    retained = []
    for row in evidence['eligible']:
        identity = row['candidate_id']; old = originals.get(identity); call = inputs.get(identity)
        _require(old is not None and call is not None, 'approved source payload missing: ' + identity)
        for field in ('benchmark', 'question_id', 'related_group_id', 'split_identity',
                      'label_class', 'label_protocol', 'label_source', 'label_method', 'human_verified'):
            _require(old[field] == row[field], 'original source identity/provenance differs: ' + field)
        _require(old['source']['research_v1_dataset_id'] == row['source_dataset_id'], 'source dataset identity differs')
        for field in ('question', 'candidate_answer', 'evidence_context'):
            _require(old[field] == call[field], 'original verifier input differs: ' + field)
        _require(labels[identity]['candidate_answer'] == old['candidate_answer'], 'validated answer differs from original')
        retained.append({'candidate_id': identity, 'source_content_identity': old['content_identity'],
                         'question_utf8_sha256': sha256(old['question'].encode()),
                         'answer_utf8_sha256': sha256(old['candidate_answer'].encode()),
                         'reference_context_present': bool(old['evidence_context']),
                         'outer_question_whitespace': old['question'] != old['question'].strip()})
    approved = {r['candidate_id'] for r in evidence['eligible']}
    removed = set(originals) - approved
    quarantined_ids = {r['candidate_id'] for r in evidence['excluded']
                       if r['exclusion_reason'] == 'shared_history_reference_context'}
    _require(removed == quarantined_ids and len(removed) == 30, 'source-to-approved population delta differs')
    return {'source_manifest_sha256': sha256(manifest_raw), 'approved_payloads_matched': 744,
            'missing_original_payloads_in_supplied_source': [], 'removed_candidate_count': 30,
            'retained_outer_whitespace_candidates': sum(r['outer_question_whitespace'] for r in retained),
            'input_tuples_transformed': False, 'independent_labels_attested': False,
            'reference_serialization_approved': False, 'payload_identity_index': retained}
