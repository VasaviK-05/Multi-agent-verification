# Experiment 2 — Budget Sensitivity Results

## 1. Scope and evaluation boundary

This report records the existing Development-only budget sensitivity analysis.
It reuses previously collected Development outcomes. No new verifier executions
were performed, and no Final Test data was accessed.

The evaluated budget levels are:
- B1: 50% = 8,297.39 ms
- B2: 75% = 12,446.09 ms
- B3: 100% = 16,594.78 ms

The minimax reports record 800 reused Development outcomes for B1 and B2,
and 1,600 for B3.

## 2. Preliminary baseline comparison

The preliminary baseline evaluated 20 Development examples across five scenarios.

| Policy | Clean coverage | Clean decision loss | Estimated resource cost |
|---|---:|---:|---:|
| coverage_aware_greedy | 80.00% | 0.0400 | 16,530.81 ms |
| development_best_fixed | 80.00% | 0.0400 | 16,530.81 ms |
| policy | 66.67% | 0.0667 | 13,792.69 ms |

`coverage_aware_greedy` and `development_best_fixed` produced identical
reported metrics.

For `coverage_aware_greedy`:
- Clean: 80% coverage, 0 false accepts, 0 false rejects.
- Confidence inflation: same reported metrics as clean.
- Forced support: 6 false accepts; decision coverage 80%.
- Forced rejection: 10 false rejects; decision coverage 80%.
- Suppression: 0% decision coverage; all 20 examples uncertain and unresolved.

The preliminary `policy` had lower clean coverage (66.67%) and higher clean
decision loss (0.0667). Under forced support it produced 5 false accepts;
under forced rejection it produced 8.33 false rejects. Under suppression,
coverage fell to zero.

These are preliminary single-budget Development results, not a complete
three-budget baseline comparison.

## 3. Minimax optimization results

All three budget levels selected the same strategy with probability 1.0:
- Verifier: semantic
- Aggregation: reputation_weighted
- Estimated strategy cost: 102.0714 ms
- Confidence, Evidence and Rule verifier inclusion probabilities: 0.0

| Budget | Budget limit (ms) | Game value | Worst-case Development loss | Expected estimated cost (ms) |
|---|---:|---:|---:|---:|
| B1 | 8,297.39 | 0.200615 | 0.2 | 102.0714 |
| B2 | 12,446.09 | 0.200615 | 0.2 | 102.0714 |
| B3 | 16,594.78 | 0.200615 | 0.2 | 102.0714 |

### Scenario-level results

Each scenario contains 20 Development examples.

| Budget | Scenario | Coverage | Uncertain | False accepts | False rejects | Mean loss |
|---|---|---:|---:|---:|---:|---:|
| B1 | Clean | 0% | 20 | 0 | 0 | 0.200615 |
| B1 | Forced support | 0% | 20 | 0 | 0 | 0.200615 |
| B1 | Forced rejection | 0% | 20 | 0 | 0 | 0.200615 |
| B1 | Confidence inflation | 0% | 20 | 0 | 0 | 0.200615 |
| B1 | Suppression | 0% | 20 | 0 | 0 | 0.200615 |
| B2 | Clean | 0% | 20 | 0 | 0 | 0.200615 |
| B2 | Forced support | 0% | 20 | 0 | 0 | 0.200615 |
| B2 | Forced rejection | 0% | 20 | 0 | 0 | 0.200615 |
| B2 | Confidence inflation | 0% | 20 | 0 | 0 | 0.200615 |
| B2 | Suppression | 0% | 20 | 0 | 0 | 0.200615 |
| B3 | Clean | 0% | 20 | 0 | 0 | 0.200615 |
| B3 | Forced support | 0% | 20 | 0 | 0 | 0.200615 |
| B3 | Forced rejection | 0% | 20 | 0 | 0 | 0.200615 |
| B3 | Confidence inflation | 0% | 20 | 0 | 0 | 0.200615 |
| B3 | Suppression | 0% | 20 | 0 | 0 | 0.200615 |

The minimax solver reports an optimal solution, zero primal-dual gap, zero
normalization residual, and identical repeated solves. These establish
optimization consistency for the encoded game; they do not establish
operational usefulness of the selected policy.

The selected strategy abstains on every example in every scenario. Its zero
false-accept and false-reject counts therefore must not be interpreted as
successful adversarial classification.

## 4. Coverage feasibility finding

The reliability-first analysis imposed a minimum clean decision coverage
requirement of 90%.

The maximum observed clean coverage among the available strategies was:
- B1: 0%
- B2: 0%
- B3: 60%

No available strategy met the 90% requirement at any budget. The
reliability-first constrained optimization is therefore infeasible on the
currently evaluated Development outcomes.

This finding does not justify silently lowering the coverage requirement,
changing reputation values, modifying contributor rules, or altering
historical outcomes.

## 5. Interpretation

The preliminary baseline demonstrates useful clean decision coverage but
shows substantial vulnerability to forced-support and forced-rejection
scenarios.

The unconstrained minimax solution avoids false decisions by abstaining on
all examples. Its strategy selection and game value do not change as the
budget increases from B1 to B3. Thus, the current minimax formulation does
not demonstrate meaningful budget sensitivity in operational decision
coverage.

The reliability-first 90% coverage target is infeasible with the currently
available strategy outcomes. These results should be reported as a
feasibility limitation, not as a successful constrained policy.

Cost figures from the preliminary baseline and minimax reports use
different estimation contexts. They must not be presented as a direct
cost-efficiency comparison without establishing compatible cost
measurement definitions.

## 6. Reproducibility and limitations

The minimax reports record:
- Repeated solve identical: true.
- Final Test accessed: false.
- New verifier executions: zero.
- Development outcomes reused: 800 for B1 and B2; 1,600 for B3.

The available evidence does not by itself establish a complete formal
three-cohort Experiment 2 provenance chain. Historical source-manifest,
evaluation, and recording-compatibility gaps remain documented in the
evidence audit.

Accordingly, this report describes the current Development-only analysis.
It does not claim Final Test validation or formal completion of any
missing provenance requirements.
