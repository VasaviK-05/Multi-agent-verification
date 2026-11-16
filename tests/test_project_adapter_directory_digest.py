"""Cross-platform ordering for local model snapshot fingerprints."""
import hashlib
import json
from pathlib import Path

import pytest

from app.benchmark import project_adapter
from app.game.models import content_id


def _entry(path, data):
    return path, hashlib.sha256(data).hexdigest()


def test_relative_path_order_is_independent_of_input_order():
    entries = [_entry('README.md', b'readme'), _entry('config.json', b'{}')]

    forward = project_adapter._sort_relative_path_entries(entries)
    reverse = project_adapter._sort_relative_path_entries(reversed(entries))

    assert forward == reverse
    assert [path for path, _ in forward] == ['config.json', 'README.md']
    assert content_id(forward) == content_id(reverse)


def test_original_relative_path_spelling_is_hashed():
    entries = [_entry('Config.json', b'{}'), _entry('README.md', b'readme')]
    ordered = project_adapter._sort_relative_path_entries(entries)

    assert [path for path, _ in ordered] == ['Config.json', 'README.md']
    assert content_id(ordered) != content_id([(path.lower(), digest) for path, digest in ordered])


def test_casefold_equivalent_paths_use_original_spelling_as_tiebreaker():
    entries = [_entry('a.txt', b'lower'), _entry('A.txt', b'upper')]

    forward = project_adapter._sort_relative_path_entries(entries)
    reverse = project_adapter._sort_relative_path_entries(reversed(entries))

    assert [path for path, _ in forward] == ['A.txt', 'a.txt']
    assert forward == reverse


def test_directory_digest_uses_normalized_casefolded_path_order(tmp_path):
    (tmp_path / 'README.md').write_bytes(b'readme')
    (tmp_path / 'config.json').write_bytes(b'{}')
    (tmp_path / 'model.safetensors').write_bytes(b'weights')
    (tmp_path / 'tokenizer.json').write_bytes(b'tokenizer')

    rows = [
        ('config.json', hashlib.sha256(b'{}').hexdigest()),
        ('model.safetensors', hashlib.sha256(b'weights').hexdigest()),
        ('README.md', hashlib.sha256(b'readme').hexdigest()),
        ('tokenizer.json', hashlib.sha256(b'tokenizer').hexdigest()),
    ]
    assert project_adapter.directory_digest(tmp_path)['sha256'] == content_id(rows)


def test_staged_embedding_snapshot_preserves_historical_digest_and_receipt_id():
    snapshot = Path('/home/tanmayee/e4-resource-staging/embedding-snapshot')
    receipt_path = project_adapter.ROOT / 'artifacts/compound-study-36-v1/portable-inputs/index-receipt.json'
    if not snapshot.is_dir() or not receipt_path.is_file():
        pytest.skip('staged embedding snapshot or historical receipt is unavailable')

    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))

    assert project_adapter.directory_digest(snapshot)['sha256'] == (
        '23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255'
    )
    assert receipt['embedding_sha256'] == (
        '23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255'
    )
    assert content_id(receipt) == (
        'e7d1ec0d88ee829b03ae82d790a61f52869729e08da5e6d84587d5789486492d'
    )
