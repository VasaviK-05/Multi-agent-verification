# Experiment 3 corpus provenance reconciliation

Status: LF bytes restored from the verified Git blob. The corpus is not approved and not frozen. Empirical Experiment 3 was not run, and no verifier recordings were collected. The approved eligibility manifest was not modified.

## Root cause

The working-tree file and the recorded corpus are the same JSON value. The byte difference is newline encoding.

`evaluation/data_preparation/development_evidence_corpus.py` writes `corpus.json` with `canonical_bytes`: UTF-8 JSON, `sort_keys`, indent 2, a final LF, and no carriage returns. That write produced the recorded file. `EvidenceRetriever` then built the index from those bytes and stored their SHA-256, size, and index id in `evidence_index/corpus/manifest.json`.

The file is tracked. `core.autocrlf` is `true`, and this path has no overriding `.gitattributes` rule. Commit `d2c7d790da5306f43c8a24f42757744c0e02deaf` (`checkpoint 7`, 2026-11-13 15:16:21 +0530) stores the original LF bytes. The working tree checked those bytes out as CRLF. `git diff` is empty because Git compares the LF-normalized form. The raw working-tree SHA-256 is therefore different, while the parsed JSON is not.

The index manifest still records the generation timestamp `2026-11-13T09:28:22Z`, size 1,345,040, and the LF hash. The working-tree directory timestamps are `2026-11-13T09:58:45Z`. No article, field, or ordering change was found.

## Exact hashes

| Artifact | Bytes | SHA-256 | Matches preparation record |
|---|---:|---|---|
| Git blob `f3ad50e1c5b4aeb91a572ece3de91bcbf1cccf21` for `corpus.json` | 1,345,040 LF | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` | Yes |
| Working tree `corpus.json` | 1,356,106 CRLF | `dd91e1e99385a2cb19aee0095eab3689204ef38661febd226ee23a09a254dd26` | No |
| LF normalization of the working tree, and canonical re-serialization | 1,345,040 LF | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` | Yes |

The same split holds for the other text files written with binary LF output. Their Git blobs match the preparation hashes, and their working copies are those bytes plus CR on each newline:

| File | Recorded SHA-256, present in the Git blob |
|---|---|
| `source_manifest.json` | `72bbcf728e68bf185e1208937f1705e91885241af221acd0d8586b01068a8b85` |
| `source_provenance.jsonl` | `397f23a0519ba3bda0800cf7891c721747b50634ca041afec41391048e3c20bb` |
| `coverage_new_corpus.jsonl` | `f467dd6d16864a0e0fcfda6d14d692b995fbf246e17772616fa9db8224a65221` |
| `coverage_articles_13083.jsonl` | `2952371fba18853e6ce8cbfa68811c687991436e4ce4156b0f6b1c961501b25d` |
| `coverage_evidence_corpus_500.jsonl` | `c953ad686dbd0f0432ef157940bad3f776488c1f6021657b3e7e8f7ba36331a1` |
| `leakage_audit.json` | `fa7a77736cd6e6d64514b2b3bc5a855dfc056a1e5cdf3e6db20348e5f1812585` |

`chunks.json` and `evidence_index/corpus/manifest.json` were written by `EvidenceRetriever` in text mode, so their preparation hashes already include CRLF. Those working-tree files still match `1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7` and `2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521`. Their Git blobs are LF-normalized and do not match those recorded hashes. `faiss.index` is unchanged in Git and in the working tree: `037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8`.

Recomputing the index id from `sha256:f76c6ce1…`, chunk size 500, and `all-MiniLM-L6-v2` returns `idx-c1dc6980912b`. The same formula on the CRLF hash returns `idx-f235b11230bd`. The saved index is bound to the recorded LF corpus.

## Original corpus

The original corpus is recoverable. It is the Git blob above, and it is also the working-tree file with every CRLF reduced to LF. No second loose copy of the 1,345,040-byte file was found under `evaluation/artifacts`. A separate reconstruction file was not written.

## Match to the 1,844-article preparation

The working-tree JSON matches that preparation:

- 1,844 articles, 1,844 unique ids, ids sorted.
- Every article has exactly `id`, `text`, `title`, and `url`, in that order.
- `source_provenance.jsonl` has 1,850 rows, 1,844 article ids, and 185 question ids. The article-id set equals the corpus id set.
- Canonical serialization of the parsed working tree is byte-identical to the recorded file.

No content, field, or ordering discrepancy remains.

## Restoration

The Git blob was checked before any write. Blob `f3ad50e1c5b4aeb91a572ece3de91bcbf1cccf21` was 1,345,040 bytes, contained no CR, and hashed to `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. Those exact bytes were written to `corpus.json`. The same check-then-write restored the other LF preparation files from their Git blobs:

| File | Restored SHA-256 |
|---|---|
| `corpus.json` | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |
| `source_manifest.json` | `72bbcf728e68bf185e1208937f1705e91885241af221acd0d8586b01068a8b85` |
| `source_provenance.jsonl` | `397f23a0519ba3bda0800cf7891c721747b50634ca041afec41391048e3c20bb` |
| `coverage_new_corpus.jsonl` | `f467dd6d16864a0e0fcfda6d14d692b995fbf246e17772616fa9db8224a65221` |
| `coverage_articles_13083.jsonl` | `2952371fba18853e6ce8cbfa68811c687991436e4ce4156b0f6b1c961501b25d` |
| `coverage_evidence_corpus_500.jsonl` | `c953ad686dbd0f0432ef157940bad3f776488c1f6021657b3e7e8f7ba36331a1` |
| `leakage_audit.json` | `fa7a77736cd6e6d64514b2b3bc5a855dfc056a1e5cdf3e6db20348e5f1812585` |
| `preparation_summary.json` | `e5f17167b78fe9a3e8930039ca16a6dabf40a2621a5c8cf7bdf7a535efc11b45` |

After the write, `corpus.json` has 1,844 unique sorted ids and only the fields `id`, `text`, `title`, and `url`. The index manifest still says `idx-c1dc6980912b`, corpus SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`, and size 1,345,040. `manifest.json`, `chunks.json`, and `faiss.index` were not rewritten; their working-tree hashes remain `2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521`, `1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7`, and `037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8`. The eligibility manifest was not modified. Freeze stays `approved: false` and `collection_authorized: false`.

`.gitattributes` and `.git/info/attributes` set `text eol=lf` on these restored paths. `git check-attr` reports `eol: lf` and `text: set` for `corpus.json`. `git ls-files --eol` reports `i/lf`, `w/lf`, and `attr/text eol=lf`. A `git checkout-index` of the corpus into a temporary directory produced 1,345,040 bytes, zero CR bytes, and SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. The index files were left without `eol=lf` because their recorded bytes already contain CRLF.

The attribute in `.gitattributes` protects checkouts once that file is committed. `.git/info/attributes` applies on this clone immediately and takes precedence over an older committed attributes file. `core.autocrlf` was not changed.

## Approval

The byte conflict is resolved. Corpus approval is still not granted. Freeze, collection authorization, and the other `PENDING_APPROVAL` protocol fields remain open. The approval package records `RESTORED_MATCHES_PREPARATION_RECORD` and stays `approved: false`.
