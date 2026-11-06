# research_v1 sample size and compute plan

This note records the sample that exists, how a Development-only pilot should be run, and how a later sample size may be chosen. It does not calculate statistical power. It does not estimate runtime. No verifier Attempt was created for this note, and no dataset file was changed.

Counts below come from `evaluation/datasets/reconciled_candidates/research_v1/validation_summary.json` and `manifest.json`, with the allocation in `evaluation/config/research_dataset.yaml`. Metric and loss definitions stay in `evaluation/docs/evaluation_metrics.md` and `evaluation/docs/research_objective.md`. They are not restated as new formulas.

## Available sample

A question group is one source question. A candidate record is one answer attached to that question. A prepared binary-labelled candidate is a candidate that already has an approved verified label and was written into the offline preparation files. These three counts are not interchangeable.

| Unit | GSM8K | HotpotQA | Combined |
|---|---:|---:|---:|
| Question groups | 500 | 500 | 1,000 |
| History groups | 300 | 300 | 600 |
| Development groups | 200 | 200 | 400 |
| Candidate records | 1,000 | 1,050 | 2,050 |

Of the 2,050 candidate records, 1,179 are prepared binary-labelled candidates (964 verified correct and 215 verified incorrect). The other 871 are unresolved. They are excluded from binary offline examples. They are not incorrect answers.

The same summary records:

- `complete_verifier_attempt_records`: 0
- `complete_offline_examples`: 0
- `policy_fitting_ready`: false
- Final Test disabled (`final_test.enabled: false`, `source: null`). The manifest records that final-test records and identities were not accessed by this build.

The 1,000 groups are the largest research_v1 roster. They are a configuration allocation, not a power calculation. Larger YAML targets exist for later versions. Those files do not make research_v1 larger, and the protocol already says the 5,000-group option is an upper bound of the current History/Development pool, not a claim of adequate power.

History is the partition for reputation or other training that the approved protocol assigns to History. Development is the partition for feasibility, payoff, policy, and configuration choices. Confirmatory results need a new protected Final Test pool. The old Final Test partition is already exposed and is not that pool.

## What has not been measured

No research_v1 game-theoretic or four-verifier Attempt run has completed. `evaluation/docs/verifier_attempt_recording_protocol.md` records that `VERIFIER_COLLECTION_ADAPTER_CONFIG` is unset and that `evaluation/datasets/verifier_attempts/research_v1/` does not exist. The collection runner is not execution-ready until local model snapshots, a pinned corpus and index, and the loopback model service pass preflight.

`evaluation/docs/dataset_selection.md` notes that an older baseline file contains 1,232 completed records. That file shows that some baseline calls finished. It is not a measurement of research_v1 game-team cost, and it is not used here as a runtime estimate.

No confidence-interval width, variance, paired disagreement rate, or power target has been computed from research_v1 outcomes, because those outcomes do not exist yet.

## Development-only pilot

The pilot is a feasibility run. It is not method selection on Final Test, and it is not permission to edit research_v1.

Rules:

1. Use Development groups only. Do not read History labels into the pilot analysis. Do not open Final Test files or the old exposed test partition.
2. Do not add, delete, relabel, or reassign research_v1 rows. Skips and failures are written to a separate run directory.
3. Do not choose a threshold, loss weight, team, or aggregation because it looks best on Final Test. Development may inform a later freeze. Final Test, once a protected pool exists, is used only after that freeze.
4. Before the first call, record the environment: code revision, Python environment, `execution_manifest` fields required by the attempt runner, model and embedding names, corpus path and hash, index identity, adapter configuration hash, seeds, and resource settings. The current attempt runner refuses network downloads and refuses to start without that preflight.
5. Run the approved configuration on a predeclared Development subset. The subset size is a compute choice made before looking at outcomes. This note does not set that size.
6. Measure, rather than assume, wall-clock time per question and per verifier, attempt completion, execution failures, coverage, abstention, and unresolved output. Record estimated attempt cost only when the executed path supplies one, and keep it in a separate column from measured duration.
7. Retain failed, skipped, unavailable, and interrupted calls. A resume must not erase them. The attempt runner already keeps failed calls and requires a new output directory if the input or configuration changes.

The pilot report should include the group count, the candidate count, how many groups were scheduled, and how many produced a completed attempt. It should not convert those counts into a recommended full-sample size until the procedure in the next section is followed.

## Sample-size decision procedure

Do not treat 400 Development groups, 600 History groups, or 1,000 total groups as a statistically powered sample. Choose the analysis size only after all of the following are in hand:

1. Pilot measurements of runtime and cost on Development, using the same configuration intended for the study.
2. Observed outcome variance and paired disagreement between the methods being compared, computed on Development groups, not on candidate rows alone.
3. A statement of group-level dependence: multiple candidates share a question, and some HotpotQA passages are shared across partitions. The effective unit is the question group unless a later audit justifies a finer unit.
4. A numeric confidence-interval width or power target written down before the confirmatory run. Neither number exists yet. Writing the target is a team decision. It is not supplied by this note.
5. An available compute budget expressed in the same units as the pilot, such as wall-clock time and verifier calls, including failures and reruns.

If the target cannot be met inside the budget, report the achievable group count and the resulting limitation. Do not fill the gap with unresolved candidates, with the old Final Test partition, or with an invented variance.

Roles after the pilot:

- Development remains the planning and selection partition.
- History remains available for the training role the approved protocol assigns to it, such as reputation estimated from History only.
- A new custodian-controlled Final Test pool is required before any confirmatory claim. research_v1 does not contain one.

## Compute accounting

Two existing mechanisms record cost. They must not be merged into one number.

- `evaluation/data_preparation/run_verifier_attempts.py` times each direct verifier call with `TimedVerifier` and stores elapsed milliseconds beside the Attempt. Attempt states include `directional`, `abstention`, `unavailable`, `failed`, and `missing`. That elapsed time is a measurement, not a monetary cost and not the research loss.
- `app/game/execution.py` stores `estimated_attempt_cost` from the planning context's attempt-cost table. That estimate is the sum of predeclared per-verifier costs for the selected team. It is not the wall clock of the call.
- `app/database/verifier_cost_repository.py` can store `duration_ms` with outcomes `returned`, `failure`, `timeout`, and `interrupted`, and can summarize mean, median, and p95 duration. Those database outcomes are a different vocabulary from Attempt states. A report must name which vocabulary it used.

Accounting rules:

- Record time per question group and per verifier call.
- Count attempted, completed, failed, skipped, and unavailable calls separately. Skipped unresolved rows that have no prepared verifier input stay in `unresolved_not_attempted.jsonl`. They are not attempted calls.
- Keep measured duration separate from estimated attempt cost.
- Report total wall-clock time for the process and the resource settings recorded at preflight.
- Add reruns and failed attempts into the compute total. Do not report only successful calls.
- Do not describe latency as the research loss. The offline objective `mean decision loss + resource_weight × average estimated attempt cost` is a separate, still-unapproved formula. Use it only if the team explicitly approves those weights. Until then, publish time, attempt counts, and estimated cost as their own columns.

## Statistical reporting

Follow `evaluation/docs/evaluation_metrics.md`. In particular:

- Compare methods on the same groups and the same permitted context. Report paired differences.
- Resample whole question groups, not candidate rows. All candidates that belong to a group stay together in a draw. The interval's sample size is the number of groups.
- The interval level and the number of bootstrap draws are not set. They require approval before a confirmatory analysis. Do not pick them after seeing which choice looks tightest.
- Publish the confidence interval and the group count next to each main metric.
- Predeclare seeds. Do not keep the seed with the most favorable result.
- If a denominator is zero, the rate is undefined. Selective risk is undefined when there are no definitive decisions. HotpotQA false-acceptance rate is undefined on the current binary labels because that benchmark has no verified incorrect candidate. Do not replace an undefined rate with zero.
- Mark Development pilot results as exploratory. Mark results on a future protected Final Test, under a frozen configuration, as confirmatory. Do not present the pilot as confirmatory.

## Leakage and label caveats

These limits travel with any sample-size claim:

- The group-leakage audit is a conditional pass. Question IDs do not cross History and Development. HotpotQA still shares 14 identical paragraphs, and 15 groups on each side share provenance context hashes. Two supporting-fact passages, Magic Dirt sentence 0 and Tom Clancy sentence 0, appear in both partitions. See `evaluation/docs/research_v1_group_leakage_audit.md`.
- Semantic and paraphrase leakage is unverified. Exact normalization only strips case and punctuation.
- All 215 verified incorrect labels are GSM8K gold+1 discrete-count items. They are not a sample of natural wrong answers.
- HotpotQA has zero verified incorrect candidates, so a HotpotQA false-acceptance rate cannot be estimated from the current binary labels.
- `human_adjudication_claimed` is false. No reviewer workload has been completed.
- The 871 unresolved candidates stay unresolved. They must not be moved into the negative class to enlarge the sample.

Direct arithmetic is not a separate population in research_v1. GSM8K remains 500 word-problem groups.

## Remaining decisions

| Decision | Status |
|---|---|
| Research_v1 roster size | Recorded: 1,000 groups, not a powered sample |
| Development pilot subset size | Not chosen |
| Interval level and bootstrap draws | Not approved |
| Variance, disagreement, power, and per-example runtime | Not computed; no research_v1 Attempts exist |
| Loss weights and whether latency enters the loss | Unapproved; see the research objective |
| Evidence corpus and index for the pilot | Not bound to research_v1 |
| Shared HotpotQA context | Conditional-pass limitation; no rows removed |
| Protected Final Test | Not available |
| `policy_fitting_ready` | false |
