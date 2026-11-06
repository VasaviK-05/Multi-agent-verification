# Final Test leakage audit record

## Executed audit

The audit was run as part of generating `research_v1_final_test_provisional_v1` on 2026-11-06 UTC using the fresh local source snapshots and frozen `research_v1` History/Development candidate files. It passed, and was rerun during artifact validation against the current History and Development records. The machine-readable result is `evaluation/datasets/final_test_research_v1_eval_v1/leakage_audit.json` (SHA-256 `1d32e0f685a4016f6a2a377175bd8bc7f84a07f43ced824bf253ee030e9f5bb0`). The exposed unified `final_test.json` was not opened or used.

### Partition and sources

- GSM8K test: 1,319 source groups available and selected.
- HotpotQA validation: 7,405 source groups available before filtering; 1,319 selected after exclusions.
- Final Test: 1,319 groups and 1,319 benchmark-gold candidates per benchmark (2,638 total).
- Source revisions: GSM8K `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866`; HotpotQA `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab`.
- Source file SHA-256 values, row/group/candidate ID rosters, configuration and generator hashes are included in the manifest.

### History/Development overlap results

| Exact comparison | Overlap count |
|---|---:|
| Question IDs | 0 |
| Dataset/source IDs | 0 |
| Group IDs | 0 |
| Candidate IDs | 0 |
| Normalized question text | 0 |
| Exact context hashes | 0 |
| HotpotQA supporting facts | 0 |
| Donor IDs / donor source IDs | 0 |
| Cross-partition groups | 0 |

The source exclusion ledger records 983 HotpotQA groups excluded for History/Development provenance overlap (question/source/group/context/supporting-fact reasons can overlap), plus 2,045 additional HotpotQA groups excluded for within-Final-Test exact context reuse. GSM8K had no such exclusions. These counts are exclusion-reason counts and must not be summed as unique overlap groups. Final Test has zero exact within-partition shared-context and supporting-fact groups.

The audit found that 100 borrowed candidate records in prior History/Development inputs lack donor IDs. Those rows could not be assigned an unknown donor identity; this is a limitation in the reference partition provenance, not evidence of zero possible donor reuse.

## Checks implemented

The workflow requires stable source/question/group/candidate identifiers and source version; checks unique group and candidate identities and normalized questions; compares question, source, group, candidate, normalized question, context/source hashes, HotpotQA supporting facts, donors and donor source IDs to History and Development; and checks within-partition exact context/supporting-fact reuse. Missing required identity/provenance and detected leakage fail closed. Candidate splitting is prohibited by group-level selection. The manifest binds source hashes, all roster IDs, label provenance, configuration, audit, and artifact hashes.

Labels are constructed only from benchmark-gold source answers. GSM8K uses extraction of the `####` answer and deterministic numeric parsing. HotpotQA retains the benchmark answer and validates supporting-fact title/sentence references against the supplied context. Unverifiable records remain unresolved; none were silently converted to negatives. No human adjudication is claimed. The generated partition currently has only verified-correct gold candidates (2,638); it has no verified-incorrect class.

## Limits and acceptance

Normalized-question matching is exact after canonical normalization. Semantic similarity, paraphrases, translation, entity-level duplication, and transformed/partial evidence are not assessed. `semantic_paraphrase_leakage` is `NOT AUDITED`. Exact context hashes do not prove independent evidence origins. Supporting-fact comparison uses exact source title/sentence references. Donor checks are limited by missing donor metadata in prior inputs. The audit therefore passes exact identity/provenance checks but does not establish broad semantic independence or statistical independence.

Final Test remains disabled and unauthorized. The passing audit is necessary, not sufficient, for confirmatory use. Review source license/citation, benchmark and label-policy approval, semantic leakage limitations, sample-size rationale, and custody separately.
