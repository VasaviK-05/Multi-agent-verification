# Experiment 3 synthetic readiness

Status: the synthetic aggregation-choice machinery can run. Empirical Experiment 3 is not ready and was not run.

Every file under `evaluation/experiments/experiment3/synthetic/` is labelled `SYNTHETIC`. The two-group dependency registry is a controlled assumption. It is not an empirically established dependency, and these numbers are not a robustness result.

## What is in place

- `shared_unknown_registry` preserves the existing Stage 1 treatment: every named verifier stays in one unresolved component. The pilot registry, `DependencyRegistry.groups`, and verifier voting are unchanged.
- `controlled_two_group_registry` builds two disjoint `Dependency` records. Both use the pathway `controlled_synthetic_assumption_not_empirically_established`. `unknown_treatment` remains `shared_unknown`, and `unresolved` is empty so the groups do not merge.
- `ExperimentSpecification.dependency_registry_kind` accepts that registry. `unknown_dependency_treatment` is still required and still only `shared_unknown`. A controlled registry is rejected when `evidence_kind` is `empirical`.
- Controlled fixtures cover all correct, one verifier failing independently, dependent verifiers failing together, a compromised dependency group, conflicting reports, missing reports, and execution failures.
- The synthetic runner scores `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group` on one shared report cube and one shared attack-column list per configuration. It runs the one-group and two-group registries separately. Attack columns differ between those configurations because the declared groups differ. The report digest of the recordings is the same: `f70b482ae88b…`.

Reproduce with:

```text
.venv\Scripts\python.exe evaluation\experiments\experiment3\synthetic_runner.py
```

Outputs:

- `evaluation/experiments/experiment3/synthetic/protocol.json`
- `evaluation/experiments/experiment3/synthetic/results.json`

## Synthetic fixture result

Recordings are a hand-built arithmetic fixture. Verifier `a` has one correct history update, `b` remains at the prior, and `c` has one correct history update. Development reports are all directional and correct. Complete Development attempts outside this fixture are 0. No Final Test labels were opened.

On team `(a, b)`, reputation aggregation is publicly `uncertain` because the neutral verifier is not a second log-odds contributor, while dependency aggregation is publicly `passed`. That is a controlled decision difference, not a measured dependence.

| Configuration | Attack targets | Joint worst-case loss | Fixed reputation worst-case loss | Fixed dependency worst-case loss |
| --- | --- | --- | --- | --- |
| `shared_unknown` | one target, members `(a, b, c)`; 5 columns | 0.4 | 0.4 | 1.2 |
| `controlled_synthetic_two_group` | `(a,)` and `(b, c)`; 9 columns | 0.4 | 0.4 | 0.4 |

Within the two-group configuration the clean losses still differ: fixed reputation 0.4 with coverage 0, and fixed dependency 0.2 with coverage 1. The joint action set contains both aggregations. On this fixture the numerical certificate places probability 1 on `reputation_weighted` in both configurations (`dependency_group` frequency 0). Fixed policies remain on their own aggregation with frequency 1. Inclusion frequencies in the saved file match those probability vectors. For example, shared-unknown fixed dependency includes `a` and `b` at frequency 1 and `c` at frequency 0.

`selective_risk` is null where coverage is 0, which is the existing metric rule for no decisive outcomes.

## Tests

- `tests/test_experiment3_synthetic.py` together with `test_development_matrix_hand_losses_cost_once_and_policy_final_test`, `test_fixed_full_registry_actions_project_same_column_without_retargeting`, `test_readiness_lists_actions_and_baseline_without_scoring`, and `test_stable_detached_specification_identity`: 13 passed.
- `tests/test_game_research.py`, `tests/test_dependency_aggregation.py`, and `tests/test_pilot_abstention_contract.py`: 124 passed.

The checked contracts are: two disjoint groups produce two attack targets; `shared_unknown` produces one target containing every verifier; the joint matrix contains both aggregations while each fixed policy stays on its own; policies differ when the aggregation loss rows differ; aggregation and verifier frequencies match the frozen probabilities; an empirical claim raises when complete Development attempts are zero.

## Still blocked

- No complete research Development recordings. An empirical claim is refused at a count of zero.
- No empirically established dependency registry. Real verifier names were not assigned a dependency.
- Loss weights, threshold, budget, and suppression remain the synthetic fixture settings.
- Confirmatory evaluation was not run, and Final Test v2 labels were not opened.
- Custody and evaluation authorization for Final Test v2 are unchanged.
