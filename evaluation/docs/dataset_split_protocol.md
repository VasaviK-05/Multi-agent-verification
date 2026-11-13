# Dataset grouping, splitting, and final-test custody

Partition roles for this protocol, not yet an approved freeze:

- **History** estimates reputation only. It does not select policies or evaluate the Final Test.
- **Development** is the only partition for eligibility, payoff matrices, fitting, baseline selection, and budget selection.
- **Final Test** is held out. Final Test v2 identities stay reserved. Custody is designated and not independent. Evaluation authorization and label release stay pending. The retired provisional Final Test is not a held-out set and is not relabelled or reused.

Exact History/Development identity overlap on `research_v1_exploratory_v1` was recomputed for the approved eligibility manifest: group, candidate, question, content identity, normalized question, and source dataset ID overlap are 0. Paragraph-hash overlap is 50, covering 15 History groups and 15 Development groups. None of those pairs share a question ID. They are distinct HotpotQA questions that reuse reference paragraphs. Supporting-fact overlap is 2 (`Magic Dirt` sentence 0; `Tom Clancy` sentence 0), and both Development groups are inside the same 15. Those 15 Development groups, 30 candidates, are quarantined from the approved roster. The semantic audit compares each Development question with same-benchmark History questions using token Jaccard and `difflib.SequenceMatcher` ratio on normalized question text (`normalized_token_jaccard_and_sequence_ratio_v1`; duplicate thresholds 0.80 and 0.85). Zero pairs met either threshold. The maximum sequence ratio was 0.6813. The two pairs at or above 0.65 are HotpotQA comparison templates with different named entities and were adjudicated as not paraphrases. Pairs below the thresholds were not all read, so semantic clearance is `NOT_CLAIMED`. The `research_v1` roster of 478 candidates is a different population. The approved roster is 744 candidates in 372 groups.

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
- **Final Test isolation:** every exact comparison against research_v1 History and Development is 0 and matches the frozen audit. The content-level audit against all exposed files failed (807 groups), and the provisional Final Test is retired; see `final_test_contamination_audit.md`.
- **Semantic/paraphrase leakage:** not audited for the `research_v1` partitions. The exploratory History/Development audit is recorded in `research_v1_exploratory_eligibility_approved_v1` and does not claim semantic clearance.

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
