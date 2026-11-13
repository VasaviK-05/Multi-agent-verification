# Dataset custody and Final Test authorization audit

Date: 2026-11-13. Final Test labels were not opened. The Development corpus `development_evidence_corpus_v1` was not modified and remains `PROPOSAL_NOT_APPROVED`. No authorization was signed.

## 1. Executive summary

The 12 historical files named by the research_v1 manifest’s output hashes are on disk and match those hashes. They are `ORIGINAL_VERIFIED_IN_PLACE`. No execution-source custody ZIP was identified. Two label-custody ZIPs and two dataset ZIPs are present, intact, and were not unpacked into label files. Verifier configurations for the research cohorts are incomplete: attempt counts are zero, and model-weight snapshot hashes are unknown. The exact Final Test manifest is `research_v1_final_test_v2_exploratory_v1`. Authorization is `NOT_READY_FOR_AUTHORIZATION`.

## 2. The 12 historical files

The designation is the sentence in `evaluation/docs/research_v1_inventory_and_provenance.md`: the research_v1 manifest records 12 output hashes. Those hashes are `output_sha256` (7 files) plus `offline_output_sha256` (5 files). The 15 `source_sha256` inputs were recomputed and also match; they are a different list.

Manifest date on the file: 2026-11-02. Recorded manifest content hash: `8cc984bef54b1d7b9436524ffc9cd0d2081fbb9dc6f3c109cc7b5cc901a7c1d1`. The 12 blobs are not in Git history. Each working-tree file matches its recorded SHA-256, and the same bytes are inside `research_v1.zip` or `offline_examples/research_v1.zip`.

| # | Path | SHA-256 | Status |
|---|---|---|---|
| 1 | `evaluation/datasets/reconciled_candidates/research_v1/README.md` | `1bcfeef09527ab3f0c6edb681d7e2483f85ddc013d7edccd57f5276371c51a85` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 2 | `evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl` | `2c6272ae74a68e56ef9476716ce651c593dbe3ea5639ff0fde427cad926b55e3` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 3 | `evaluation/datasets/reconciled_candidates/research_v1/gsm8k_reconciled.jsonl` | `2a1f50ef275ebd6cd3873e567103bbe4b0a1a3f84a9e2d06f4f973bd6a1515f8` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 4 | `evaluation/datasets/reconciled_candidates/research_v1/history_candidates.jsonl` | `5896b6d0559b7e48e96be19251bf9a44265bf429f83729bdf5bb423261788bd2` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 5 | `evaluation/datasets/reconciled_candidates/research_v1/hotpotqa_reconciled.jsonl` | `5ffba24efbfaf4108198e6d19f95560f902e5f3406b42ea125b87af07091154d` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 6 | `evaluation/datasets/reconciled_candidates/research_v1/unresolved_candidates.jsonl` | `55585950511518ccd2ee1a4dba070b6a928f33e65084b4c6c0601ac8a78c2c3e` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 7 | `evaluation/datasets/reconciled_candidates/research_v1/validation_summary.json` | `0a043b22c956840e17f2fd38976e979846e24670653c658061a9a58e10009174` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 8 | `evaluation/datasets/offline_examples/research_v1/README.md` | `fbe4c51ec4ca7cf75595a1877c85291f50a25ed4be3ac67e7eea3213befc610d` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 9 | `evaluation/datasets/offline_examples/research_v1/development_prepared.jsonl` | `323aaf326f07ae5d999bb3db46e5d761f418e9bc22615d4b5ddd25102ab8cd7f` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 10 | `evaluation/datasets/offline_examples/research_v1/excluded_unresolved.jsonl` | `19744b4138033d321a3a4b6359c348c7815a5be13d31c04bf7030a97b7200ff3` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 11 | `evaluation/datasets/offline_examples/research_v1/history_prepared.jsonl` | `651f10b54ba2f59674a17e2abcf2ccfded468e5dbb908f4a16307a440e261cb4` | `ORIGINAL_VERIFIED_IN_PLACE` |
| 12 | `evaluation/datasets/offline_examples/research_v1/validation_summary.json` | `cb65e27e09b6472264064803282d3c4ff6997d10d32837ca533f9af421af2dfb` | `ORIGINAL_VERIFIED_IN_PLACE` |

Cohort: `research_v1` History and Development. Machine-readable copy: `evaluation/artifacts/person1/historical_evidence_recovery_v1/twelve_original_files_inventory.json`.

## 3. Execution-source custody ZIP

No path, document, or Git object names an execution-source custody ZIP. Status: `NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE`. A recovery archive was not created, because there is no identified set of original execution records that belonged to a missing ZIP. Research_v1 records 0 complete verifier attempts.

Archives that do exist, hashed and checked with `testzip` without extracting label members:

| Archive | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `evaluation/datasets/reconciled_candidates/research_v1.zip` | 5,367,650 | `3b04d48494f63e3b6087fd05c3256dd2f436a431070fa3f5eb1e668907b8d807` | The 7 reconciled outputs. Members match. |
| `evaluation/datasets/offline_examples/research_v1.zip` | 3,411,901 | `c8a94af66e747ca446b7f678ab98322c307915a2e98440ee8aeef47b48745493` | The 5 offline outputs. Members match. |
| `evaluation/datasets/_custodian.zip` | 438,079 | `721fe430d9056fc2b4d0fa78591a42e21b0baebd554a10a6a965a0c4245757ee` | Retired v1 label custody archive. Labels not extracted. |
| `evaluation/datasets/_custodian (2).zip` | 625,809 | `71c59c07fe69cca6920b9c77105245ecc2c9c3bdd3040651974a075a6574f421` | v1 and v2 label member names. Labels not extracted. |

These are not the missing execution-source ZIP.

## 4. Verifier configuration recovery

Matrix: `evaluation/artifacts/person1/historical_evidence_recovery_v1/verifier_configuration_recovery.json`.

| Cohort | What is original | What is unknown |
|---|---|---|
| `research_v1` | No verifier run. Corpus unbound. | Model, prompt, threshold, adapter |
| `research_v1_exploratory_v1` | No verifier run. | Same |
| Baseline on unified Development | Corpus path `data/articles_13083.json`, index `idx-6d28c9c49dac`, seed 0, default constructors | Weight snapshot, prompt hash, numeric threshold, hardware, source revision |
| Five-example Evidence Verifier run | Verifier name, dataset path, top_k 3, per-example HotpotQA context policy | Shared-corpus hash, weight snapshot, prompt hash, source revision |
| Rule Verifier GSM8K run | Verifier name, 500 examples | Rule-version hash, source revision |
| Experiment 3 synthetic | Labelled `SYNTHETIC`, not an empirical verifier config | Not used as a historical production config |
| Current source defaults | Recorded only as current code | Not back-filled into historical rows |

No configuration was reconstructed by substituting today’s defaults. No collection adapter was recovered.

## 5. Protocols, baselines, and authorization

Baseline protocol text is the existing `evaluation/docs/baseline_evaluation.md`. It is an original document, not a reconstruction. Final Test evaluation authorization is `NOT_FOUND`. The appointment file records evaluation pending, label release not authorized, protocol freeze pending, and operating-system protection false. That appointment was not rewritten and is not an approval.

## 6. Source revision and provenance

GSM8K source pin: `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866`. HotpotQA source pin: `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab`. All 15 manifest source hashes match the files on disk, including both HotpotQA train arrow shards, the GSM8K train shard, unified History and Development, and the prior `reconciled_candidates/v1` inputs. The 12 outputs are not in Git, so an exact creating commit is `UNKNOWN`. The manifest’s own date is 2026-11-02.

## 7. Exact Final Test manifest

The intended manifest is the v2 exploratory manifest, not the retired provisional Final Test.

| Field | Value |
|---|---|
| ID | `research_v1_final_test_v2_exploratory_v1` |
| Path | `evaluation/datasets/final_test_research_v1_eval_v2/manifest.json` |
| Content hash recorded in the file | `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` |
| File SHA-256 | `58c55bf8d10f9f5a1ba847de93eccfde2f3edd87b79417f87c22bb9bb429bb69` |
| Groups / candidates | 600 / 1200 |
| Status | `NOT_AUTHORIZED`, enabled false |
| Custody | Designated dataset creator, `NOT_INDEPENDENT` |

The leakage audit method `final_test_v2_identity_disjointness_v1` records `passed: true`. Counted overlaps with research_v1 History and Development, the exploratory snapshot, and the retired v1 roster are 0 on the audited identity fields. Within-test duplicate questions, shared paragraphs, and shared supporting facts are 0. Semantic leakage is not claimed. Candidate identifiers were not copied out. The roster and the label files were not opened.

## 8. Authorization readiness

Decision: `NOT_READY_FOR_AUTHORIZATION`. No approval record exists. The package under `evaluation/artifacts/person1/final_test_authorization_v1/` holds metadata, the provenance counts, the prerequisite checklist, and a template whose status is `NOT_AN_APPROVAL` with approver null. It does not release labels or authorize collection.

Blockers: pending evaluation authorization, label release not authorized, confirmatory use not authorized, custody not independent, protocol freeze pending, operating-system protection false, human approval deferred, research settings unfrozen, collection adapter missing, and the Development evidence corpus still unapproved.

## 9. Responsibility audit

| Responsibility | Evidence | Completion |
|---|---|---|
| research_v1 source provenance | 15 source hashes match | Verified for those files |
| 12 historical outputs | Hashes and ZIP members match | Verified in place |
| Execution-source custody ZIP | Not identified | Outstanding |
| Original verifier configurations | Partial documents only | Outstanding |
| Group integrity for research_v1 | Manifest overlap report is 0 between History and Development | Recorded; not a new semantic audit |
| Exploratory eligibility | Approved manifest remains in place | Eligibility only |
| Development evidence corpus | Unchanged, `PROPOSAL_NOT_APPROVED` | Not frozen |
| Historical verifier recordings for this protocol | Attempt count 0 | Outstanding |
| Final Test custody | Designated, not independent; labels sealed | Not complete as protected custody |
| Final Test authorization | `NOT_READY_FOR_AUTHORIZATION` | Outstanding |
| Protocol freeze and experiment run authorization | Settings still proposed | Outstanding |

## 10. Remaining work

A research lead can close authorization only after the blockers in section 8 are resolved in a new signed record. Person 2 still owes measured costs and attempts. Person 3 still owes policy fitting. The one HotpotQA retrieval miss and the 0.78-gate gap in the Development corpus stay unresolved and were not edited.

## 11. Original, recovered, reconstructed, missing

Original and verified in place: the 12 outputs, the 15 sources, both evidence corpora and their indexes, the two dataset ZIPs, and the two label-custody ZIPs. Recovered from Git earlier: the misnamed `articles_13083_index`, which indexes the test corpus. Reconstructed this round: nothing. Missing: the execution-source custody ZIP, a reviewed collection adapter, historical weight-snapshot hashes, and a Final Test approval.

## 12. Labels

Final Test v2 labels and the retired v1 label file stayed sealed. ZIP listings used entry names only. This audit did not score, fit, or collect.
