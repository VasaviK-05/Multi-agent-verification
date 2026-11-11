# Dataset grouping, splitting, and final-test custody

## Partitions

| Partition | Purpose |
|---|---|
| History | Estimate verifier reputation using only history labels and outcomes allowed by the frozen update rule. |
| Development | Construct payoff matrices, fit/select policies, choose settings and baselines, perform candidate/data-quality decisions, and estimate Development-time feasibility. |
| Final test | Evaluate frozen methods once under the approved evaluation plan. |

No universal ratio or sample size is assumed. The available number of independent groups and the measured Development pilot cost should drive a recommendation, followed by team approval. The existing 2,000/500/500 records per benchmark are not a recommended ratio: grouping is absent, final-test identities are already exposed, and candidate construction has not been independently audited.

## Group before splitting

1. Preserve dataset name, dataset version, original split and original ID.
2. Assign stable group IDs using a documented hierarchy: same source question/claim; paraphrases or duplicates; all correct/incorrect candidate variants for that question; shared source passage or paired question set when relevant; then any manually identified related examples. Keep source-native group keys where available.
3. Normalize text only for duplicate detection; retain raw text. Store the normalization/version and every grouping edge or reason so groups are reproducible and reviewable.
4. Split whole connected groups, never individual candidate rows. Use a deterministic algorithm and explicit seed, record algorithm/version and the resulting group-to-partition ledger.
5. Validate unique IDs, valid labels, complete inclusion or reason-coded skips, group disjointness, duplicate/paraphrase leakage checks, and source-version consistency. Re-run validation after any change.

The current unified records have stable-looking IDs but no `group_id`. Exact IDs are disjoint between their current files; this is insufficient to rule out related-example leakage. Paired candidates are stored under one question row but must remain one group after expansion.

## Development versus held-out use

Development-time coverage constraints, if approved, guide policy selection on Development only. Held-out coverage is then measured as an outcome on Final test. Never filter final examples to meet a coverage target or retune against final coverage.

Freeze and hash policies, thresholds, aggregation/team rules, comparison methods, resource limits, scenario definitions, metric code, and analysis plan before final execution. Record the freeze receipt. Do not inspect final-test metric aggregates or per-example predictions during development. If iterative operational checks are necessary, expose only non-outcome integrity checks (such as file readability and run completion) through a custodian.

## Protected final-test custody

The current checkout already contains `unified/final_test.json` and `processed/final_test.json`; therefore those identities cannot be represented as newly protected or unseen. A valid held-out evaluation needs a newly reserved pool or an authorized custodian-controlled source. Reserve identities and custody metadata separately from model developers; restrict read access; record access events and hashes; provide a frozen method/configuration receipt before release; and release outcomes only after the locked run completes. A manifest may record counts and hashes without revealing labels or answers, but a hash does not make an already exposed file secret.

## Current research_v1 partitions (verified 2026-11-11)

The guidance above predates the current partitions. This section records what now exists. Counts and hashes were recomputed by `python -m evaluation.data_preparation.person1_validation validate` (17 PASS, 3 BLOCKED, 0 FAIL).

| Partition | Population | Groups | Candidates | Labels (correct / incorrect / unresolved) | Binary-labelled candidates |
|---|---|---:|---:|---|---:|
| History | research_v1, GSM8K train + HotpotQA train | 600 (300 + 300) | 1,240 | 577 / 124 / 539 | 701 |
| Development | research_v1, GSM8K train + HotpotQA train | 400 (200 + 200) | 810 | 387 / 91 / 332 | 478 |
| Final Test (provisional, disabled) | GSM8K test + HotpotQA validation | 2,638 (1,319 + 1,319) | 2,638 | manifest aggregate only: 2,638 / 0 / 0 | not opened |

- **Grouping:** `exact_normalized_question_with_source_id_preserved`; group ID = benchmark prefix + first 16 hex characters of SHA-256 of the lowercased alphanumeric question. Every stored group ID matches the recomputed value. Splits were made on whole groups.
- **History/Development disjointness:** 0 shared group IDs, dataset IDs, candidate IDs, raw or normalized questions, source IDs, or cross-partition donors for both benchmarks.
- **Known shared HotpotQA context (conditional pass):** 25 shared stored context hashes (15 History and 15 Development groups), 14 identical paragraph texts and 14 shared titles (9 groups per side), and 2 shared supporting facts (`Magic Dirt` sentence 0, `Tom Clancy` sentence 0). See `research_v1_group_leakage_audit.md`.
- **Final Test isolation:** every exact comparison against History and Development is 0 and matches the frozen audit; see `final_test_manifest.md`.
- **Semantic/paraphrase leakage:** not audited for any partition.

### Canonical Development identity

The canonical research Development partition is `evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl` (SHA-256 `2c6272ae…b55e3`) with its prepared binary view `offline_examples/research_v1/development_prepared.jsonl` (SHA-256 `323aaf32…cd7f`). The eligible rosters derived from it are in `evaluation/datasets/person1/research_v1_person1_v1/` and described in `research_v1_development_roster.md`.

Not research Development:

- `evaluation/datasets/unified/development.json` is the older 2,000-row unified file. research_v1 drew from it, and the earlier rule-verifier and baseline result files used it; it is not the research Development roster.
- `offline_examples/research_pilot/` (61 Development rows) and `v1_reconciled_candidates/` (59) are earlier pilot preparations.
- The 13 Development groups without any binary-labelled candidate are an eligibility gap (`development_ineligible_groups.jsonl`), not a rehearsal subset. No 13-candidate rehearsal artifact was found in datasets, results, docs, or the database; if one exists elsewhere, its owner must supply its path.

### Versioning rule

Any change to membership, IDs, labels, partitions, or hashes requires a new versioned output directory. `build_research_dataset.py`, `final_test_workflow.py`, and `person1_validation.py` all refuse to overwrite an existing output directory.

## Recommendation and approval gate

First use existing Development data for candidate adjudication and group discovery, with any label review blind to system outcomes. Then inventory the number of independent, eligible groups by population and estimate compute using a Development pilot. Propose partition sizes based on power/precision goals and budget. Team approval is required for the selected populations, group policy, sample sizes, seed, corpus condition, and final-test custody before any partition is used for confirmatory claims. The current History, Development, and provisional Final Test partitions exist but none of those approvals is recorded (`person1_approval_checklist.md`).
