# Research conclusions and limitations

## Conclusions supported by the recorded Development evidence

1. Under the cold-start prior, this budget, this loss, and these reports, the three Experiment 3 aggregation methods select evidence + rule and make the same decision on every one of the 15,624 cells.
2. Evidence + rule is the unique minimax team among the 14 feasible strategies. Its worst augmented loss is 0.29096372230211043. Rule + semantic is next, at 0.2979886195303902.
3. Pooled one-method decision loss is 0.2533026113671275 on 5,208 rows. Coverage is 1237/5208. Selective risk is 525/1237. False acceptance is 110/696. False rejection is 415/541. Uncertainty is the majority outcome.
4. Forced support of the model component is the worst attack column, with decision loss 0.2895161290322581 and false acceptance 103/104.
5. On the same recordings, the predeclared fixed-team rule selects the same strategy as full minimax. The paired difference is 0.0.
6. Uniform feasible selection has higher expected decision loss than full minimax on all 372 groups. The paired interval is [0.0036756638139126413, 0.02456756089532584].
7. Coverage-greedy selection is infeasible for 117 groups. On the other 255 groups, its paired decision loss is higher than full minimax. The interval is [0.004593837535014006, 0.045829131652661045].

## Boundaries

These statements describe the completed Development replay. They do not establish a result on sealed Final Test data, a new population, a different budget, or a reputation prior with approved observations.

The [0.0, 0.0] aggregation intervals do not show that the three aggregation methods are equivalent in general. They show that this paired sample contains only zeros. A synthetic control can separate the two aggregations. That control is not an empirical result, and no synthetic figure is included in this package.

Experiment 1 does not independently establish that one aggregation is better than the other. The selection comparison and the aggregation comparison answer different questions. See `03_experiment3_vs_baselines.md`.

## Limitations

- Development rows were used both to fit the game policies and to score them. There is no held-out Development split.
- Final Test labels were not accessed.
- Incorrect candidates are `SYNTHETIC_INCORRECT`. No human-verified incorrect candidate is in the approved population.
- Reputation is a `Beta(1, 1)` cold start with zero approved historical observations.
- Dependency groups are a structural assumption. They were not independently measured.
- The loss coefficient and the budget were selected. They were not empirically optimized.
- Feasibility uses frozen calibration means. The sum of this run's recorded mean times is under the budget, so confidence + evidence would have been feasible on recorded times. The experiment did not substitute those times.
- The participant floor of 2 and the uniform capability label are configuration assumptions.
- Attacks transform stored reports. They do not demonstrate a model or corpus compromise.
- Model-weight snapshot hashes remain unknown.
- GSM8K semantic inputs have empty context, and the rule verifier abstains on 742 of 744 candidates. GSM8K rates that rest on 11 or 19 classified candidates are unstable.
- Greedy uses the keyword heuristic and the selector's dimensionless costs. Its comparison excludes 117 groups.
- Uniform reports expected counts under a mixture, not integer decisions.
- Independent human approval and other contributors' signatures were not obtained. No signature was fabricated.

## Evidence classes in this package

| Class | What it is here |
| --- | --- |
| Empirical | Experiment 3 metrics, bootstrap, and copied empirical figures; Experiment 1 replay metrics, bootstrap, and copied baseline figure |
| Policy analysis | Why the cold-start weights make the aggregations unweighted, and why the budget leaves 14 feasible strategies |
| Synthetic control | Mentioned only as a boundary: the two aggregations can disagree on a constructed example. No synthetic plot is in this folder |
| Unverified hypothesis | That joint selection improves validation on Final Test, under another budget, or after reputation leaves the cold start |
