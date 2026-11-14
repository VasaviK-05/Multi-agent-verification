# Experiment 2 — Evidence and Pipeline Validation Audit

Audit date: 14 November 2026
Branch: experiment-2-budget-sensitivity
Latest commit: b0b0233
Status: Historical Development pipeline validation only

## 1. Work completed

- Pipeline-validation notebook created, executed, committed and pushed.
- Source inputs were taken from reference-50-v1.
- Evaluation role: development.
- Input manifest ID:
  b4279d31ebc6a490bc3a576aa37094880f314b63ed9e1ce294d4632027536a2a
- Compatibility ID:
  1fc178efc13e8862934fc09b2b60abcacddbfe96332e51075e6f91800ee46a17
- Input SHA-256 hashes recorded in input-hashes.csv.
- No original source inputs were modified.

## 2. Cache-projection validation

| Budget | Fraction | Budget (ms) | Feasible strategies | Attacks | Outcomes | Metrics |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 0.50 | 8297.392291 | 8 | 5 | 800 | 40 |
| B2 | 0.75 | 12446.088437 | 8 | 5 | 800 | 40 |
| B3 | 1.00 | 16594.784582 | 16 | 5 | 1600 | 80 |

All three projections previously returned cache_projection_passed.

## 3. Scope limitations

- Policy optimization was not performed.
- Verifier execution was not repeated.
- Final Test was not evaluated.
- Latency distribution was unavailable.
- Strategy probabilities and policy-dependent plots were not generated as formal Experiment 2 results.
- Budget projections are cache-based historical Development validation, not fresh experimental measurements.

## 4. Provenance findings

- Recorded source revision b03ace7d5c71a775eadc5812d4bb5ff01211b863 exists in Git.
- Recorded application-source digest 583fa4f909def95fc78784993793ce0da7bc94909ba164eed3cdcbbda77c7714 could not be reproduced from that commit or the current working tree.
- Original execution-source custody archive was not located.
- The flexible-teams source manifest matched six of six available code files at its identified Git snapshot; one documentation file was unavailable.
- The available shared Development manifest/evaluation pair was byte-identical across reference-50-v1 and reference-current-v1 copies.
- Independent category-specific Arithmetic and Factual Development manifests/evaluations were not located.
- Final Test labels were not inspected.

## 5. Approval metadata discrepancy

The user reports that the team lead has already granted the required approvals. However, run-metadata.json still records budget_levels_require_team_approval as true. This field requires reconciliation with the approval record; it should not be interpreted as proof that approval is outstanding.

## 6. Overall conclusion

The notebook demonstrates successful historical Development cache-projection validation at three provisional budget levels.

It does not establish completion of formal Experiment 2. The original execution-source custody archive and application-source digest remain unreconciled, and the required independent provenance evidence has not been fully established.

No claims about fresh verifier performance, policy optimization, Final Test performance, or experimental superiority are supported by this validation.

## 7. Preserved safeguards

- Main branch was not modified.
- Work remains on experiment-2-budget-sensitivity.
- Unrelated untracked files were preserved.
- Protected Final Test labels were not inspected.

## Additional verification: run-metadata input hashes

**Audit date:** 14 November 2026

The three input files declared in
`build/experiment-2-budget-sensitivity-pipeline-validation/run-metadata.json`
were independently checked against their recorded SHA-256 values.

| Input | Recorded SHA-256 | Result |
|---|---|---|
| `context.json` | `8a914b779b458ef2b3387c0ef0f53260f63539e9fc7beb40c259725aaf4be907` | MATCH |
| `training-manifest.json` | `38ea06bdf2797cb8e0bf0230f63ad08f7ba1120d81f006211392d809e2a63e8f` | MATCH |
| `development-evaluation.json` | `4d20b75699e20044377e9fc99afa0469fc30c82a71b75e7e0d3503a662584376` | MATCH |

The files were checked in:

`artifacts/remaining-category-studies-v1/reference-50-v1/fit/`

The `context.json` file was absent from the `Experiment2_Complete_Evidence` archive, but was found at its original repository path. Its size was 13,565 bytes, matching the publication-v1 inventory, and its SHA-256 matched both the inventory and run metadata.

The training manifest and development evaluation also matched their corresponding run-metadata hashes. The publication-v1 inventory independently records the context file's hash and size.

**Conclusion:** All three declared run-metadata input files have verified byte-level integrity against their recorded hashes. This strengthens the input-file integrity evidence for the historical Development pipeline validation.

**Limitations:** Hash agreement does not independently establish the original collection environment, execution-source custody, authorization history, or the unresolved application-source digest. It also does not establish a direct internal identifier link between the training manifest and development evaluation. No historical metadata or source artifacts were modified during these checks.

## Development budget feasibility finding

A read-only feasibility analysis was performed using the existing
`reference-50-v1` Development evaluation. No new verifier executions
were performed and no Final Test data was accessed.

The execution contract uses:
- Contributor version: `informative_history_influence_v1`
- Coverage version: `task_output_contract_v2`
- Minimum informative contributors: 1

The informative contributor rule requires a positively influential
report with reputation strictly greater than 0.5.

The historical reputation snapshot showed:
- Semantic: reputation 0.5, 20 observations
- Evidence: reputation 0.5, 0 observations
- Rule: reputation 0.5, 0 observations
- Confidence: reputation approximately 0.866667, 13 observations

The estimated confidence-verifier attempt cost was approximately
16,428.737 ms.

Maximum achievable clean Development decision coverage:

| Budget | Budget (ms) | Maximum clean coverage | 90% feasible |
|---|---:|---:|---|
| B1 (50%) | 8,297.392 | 0.00 | No |
| B2 (75%) | 12,446.088 | 0.00 | No |
| B3 (100%) | 16,594.785 | 0.60 | No |

Consequently, the 90% reliability-first coverage constraint is
infeasible at all three tested budget levels on this historical
Development evaluation.

The unconstrained minimax results are degenerate and select
abstention. They must not be presented as successful budget-sensitive
decision policies.

These findings are historical Development pipeline diagnostics,
not completed formal Experiment 2 results. The original provenance
and calibration limitations remain unresolved.

No reputation values, contributor rules, thresholds, historical
outcomes, or Final Test data were modified.