# Final Test manifest — provisional, disabled, NOT_AUTHORIZED

**Status:** a provisional Final Test partition exists and passed hash, composition, and exact-leakage validation. It is **disabled**, **NOT_AUTHORIZED**, and **not protected**: no independent custodian exists and the label directory inherits broad Windows read/modify ACLs. It must not be used for tuning, policy fitting, threshold selection, reputation estimation, or configuration decisions, and it is not yet approved for confirmatory evaluation.

The older `evaluation/datasets/unified/final_test.json` (2,000 rows) and `processed/final_test.json` (1,000 rows) are exposed development artifacts and are not this partition.

## Identity

| Field | Value (verified 2026-11-11 by `person1_validation`) |
|---|---|
| Dataset version | `research_v1_final_test_provisional_v1` |
| Generator | `evaluation/data_preparation/final_test_workflow.py`, `final_test_workflow_v2`, SHA-256 `1f1c1d03…598126` |
| Configuration | `evaluation/config/final_test_research_v1_provisional.yaml`, seed 20261107, SHA-256 `d5ebdb46…1df0d` |
| Sources | GSM8K `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866`, split `test`; HotpotQA `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab`, split `validation` |
| Source pools | GSM8K 1,319; HotpotQA 7,405 |
| Groups | GSM8K 1,319; HotpotQA 1,319 (2,638 total; one candidate per group) |
| Candidates | 2,638, all `benchmark_gold` (`benchmark_gold_only_v1`) |
| Aggregate label counts (manifest) | 2,638 verified correct, 0 verified incorrect, 0 unresolved; deterministic source-backed validation, no human adjudication claimed |
| Exclusions before sampling | 3,028 groups: 983 HotpotQA History/Development context overlaps, 308 supporting-fact overlaps, 200 each for group/question/source-ID overlap, 2,045 within-Final-Test shared contexts (one group can have several reasons) |
| Status fields | `status = NOT_AUTHORIZED`, `enabled = false`, `freeze_status = PROVISIONALLY_FROZEN_AFTER_HASH_AND_AUDIT` |

## Hashes

| Artifact | SHA-256 |
|---|---|
| Manifest (`manifest_sha256`, self-hash verified) | `cc186376c9d884ecadbfed342e9ea40773840cc305e11c2d7327f42e1db87e46` |
| `final_test_research_v1_eval_v1/manifest.json` file (identical custodian copy) | `1b379d653a15bfd733be2b76341aefd8eac4711faa5fc000273af125d8fd4426` |
| Evaluation roster | `5af06474035ec00d0009b9fd5b9e232120500fc236302637238c74ee98f823c4` |
| Question roster | `2845e24f45de71aaa1f7d4da5640f443d2731d2412c9ea469c903a55c92b448c` |
| Candidate roster | `913a806e040bf64b53081f37430598524c44e1932c54240d1ae6fbbfb4d46f48` |
| Custodian label payload (byte hash only; not parsed) | `22a6274ded455acbf4a13f0456b2c7a47c056249d9c32793bf2f84f7eb567b93` |
| Leakage audit | `1d32e0f685a4016f6a2a377175bd8bc7f84a07f43ced824bf253ee030e9f5bb0` |

All eight recorded source-file hashes match. Both integrity receipts are identical and match every file.

## Leakage against research_v1 History and Development

`person1_validation` reran `final_test_workflow.audit_leakage` on the evaluation roster (no labels) against the current History and Development candidate files. Every comparison is 0 and equals the frozen audit: candidate IDs, contexts, donor source IDs, donors, group IDs, question IDs, normalized questions, source IDs, supporting facts. No Development eligible-roster candidate appears in the Final Test. Semantic and paraphrase leakage is **not audited**.

## Label isolation

The validator never parses `custodian_labels.jsonl`; it compares only the file's byte hash. Aggregate label counts come from the manifest. The evaluation roster contains no label fields (`correctness_status`, `answer_is_correct`, `gold_answer`, `binary_label`, `expected_correct`, `label`).

**Limitation:** every roster candidate is the benchmark gold answer, so the roster's `candidate_answer` reveals the reference answer for every Final Test question. The roster is therefore not answer-blind. Developers must not read it for tuning; this rule is organisational, not technically enforced.

## Limitations and pending approvals

- No negative class: false acceptance cannot be estimated on this partition. Whether an all-gold Final Test is scientifically acceptable, and any negative-candidate policy, is pending (do not manufacture negatives).
- Sample size is an operational cap (GSM8K test pool size), not a power calculation.
- Independent custody and OS-level protection are not established; the Python authorization gate (`read_custodian_labels`) only controls callers of that function.
- License and citation terms are not recorded in the source `dataset_info.json` files.

See `final_test_custody_protocol.md` for the access workflow and `person1_approval_checklist.md` for owners of each pending decision.
