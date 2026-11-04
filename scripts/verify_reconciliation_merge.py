"""Audit the reviewed source overlay without rewriting publication fingerprints.

The canonical publication check intentionally reports modified source files in an
integration checkout. This separate check validates the exact reviewed overlay,
the unchanged remainder of the original inventory, and original resource pins.
"""
import hashlib
import json
from pathlib import Path

from scripts.verify_reconciliation_package import verify


def audit(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    review = json.loads((root / 'reconciliation/main-merge-review-v1.json').read_text(encoding='utf-8'))
    original = json.loads((root / 'artifacts/publication-v1/file-hashes-v3.json').read_text(encoding='utf-8'))
    overlays = review['publication_source_overlays']
    if set(overlays) != {'.gitattributes', 'app/game/execution.py', 'app/game/component_execution.py'}:
        raise ValueError('unreviewed publication overlay scope')
    differences = []
    for path, expected in original.items():
        observed = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if observed != expected['sha256']:
            differences.append(path)
            reviewed = overlays.get(path)
            if reviewed is None or reviewed['original_publication_sha256'] != expected['sha256'] or reviewed['merged_checkout_sha256'] != observed:
                raise ValueError('unreviewed publication difference: ' + path)
    if set(differences) != set(overlays):
        raise ValueError('overlay differs from the reviewed merge result')
    for path, expected in review['pinned_resource_contributors'].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError('resource contributor differs: ' + path)
    return dict(version='verified_reconciliation_merge_overlay_v1',
        main_commit=review['main_commit'], feature_parent=review['feature_parent'],
        original_publication_files=len(original), unchanged_original_files=len(original)-len(differences),
        canonical_whole_publication_unchanged=False, known_source_overlays=differences,
        frozen_publication_artifacts_unchanged=True, resource_fingerprint_pins_unchanged=True)


if __name__ == '__main__':
    result = audit()
    verify()  # Typed policies/certificates and pinned old/new implementation IDs.
    print(json.dumps(result, indent=2))
