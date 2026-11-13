# Candidate adjudication manual-review pilot

## Sample

The pilot uses seed **20261101** and samples without replacement from candidates currently marked unresolved in `evaluation/datasets/adjudication/v1/`. Sampling is deterministic: each benchmark pool is sorted by stable `candidate_id` before `random.Random(seed).sample` is applied. It samples across the existing History, Development, and already exposed `final_test` files; partition counts are GSM8K 14/6/10 and HotpotQA 18/7/5 (History/Development/Final test).

- GSM8K: 30 unresolved `synthetic_numeric_perturbation` candidates. The exact 30 IDs are in [`pilot_manifest.json`](../datasets/adjudication/pilot_v1_seed_20261101/pilot_manifest.json).
- HotpotQA: 30 unresolved `synthetic_cross_example_answer` candidates. The exact 30 IDs are in [`pilot_manifest.json`](../datasets/adjudication/pilot_v1_seed_20261101/pilot_manifest.json).

The selected IDs and source hashes are recorded in `pilot_manifest.json`. The exact IDs are also the candidate IDs in the queues; this avoids duplicating a long ID list in this document. No candidate is pre-labeled by this pilot. All 60 start unresolved.

## Files

Pilot files are under `evaluation/datasets/adjudication/pilot_v1_seed_20261101/`:

- `gsm8k_review_queue.jsonl` — question, candidate, benchmark reference answer, and original worked solution as reference context. Reviewers should solve independently before consulting the solution.
- `hotpotqa_review_queue.jsonl` — question, candidate, benchmark reference answer, target context paragraphs, and supporting facts.
- `gsm8k_adjudications.jsonl` and `hotpotqa_adjudications.jsonl` — the 30 selected source records per benchmark, ready for the existing importer.
- `decisions_template.jsonl` — 60 blank decision records with two reviewer slots each.
- `statistics.json` — initial counts (all unresolved).
- `pilot_manifest.json` — seed, selected candidate IDs, and source hashes.

Framework predictions are not read or included. Queue entries have two `reviewer_decisions` slots with `reviewer_id`, `decision`, `evidence`, `evidence_provenance`, and `rationale`. Use only `verified_correct`, `verified_incorrect`, or `unresolved`. Keep evidence provenance specific, such as the GSM8K derivation/source solution or HotpotQA paragraph title and supporting-fact sentence. Do not use substring matching alone as proof.

## Recording and importing decisions

Reviewers may fill the two slots in the queue, then copy the corresponding reviewer decisions into `decisions_template.jsonl`. For each candidate, also set:

- `adjudication_status`: final status using the three permitted values.
- `adjudication_method`: `independent_arithmetic_solution`, `independent_factual_review`, or `third_party_adjudication`.
- `adjudication_provenance`: rubric/source references.
- `adjudication_rationale`: concise decision reasoning.
- `adjudication_evidence`: one or more non-empty evidence-reference strings.

If reviewers disagree, leave the status unresolved or record a third-party resolution with `adjudicator` and method `third_party_adjudication`. Do not infer missing decisions.

Save the completed JSONL separately, for example as `pilot_decisions.jsonl` in the pilot directory, then run:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\candidate_adjudication.py apply --output-dir evaluation\datasets\adjudication\pilot_v1_seed_20261101 --decisions evaluation\datasets\adjudication\pilot_v1_seed_20261101\pilot_decisions.jsonl
```

This updates only the pilot adjudication files and recomputes `statistics.json`. Existing full adjudication records, source datasets, experiment results, and splits are not changed. Re-running the pilot creator with the same seed reproduces the IDs, but it refuses to overwrite the non-empty pilot directory. No final splits are generated.
