# Experiment 3 statistical analysis

No empirical interval was computed. Bootstrap settings remain `PENDING_APPROVAL` in the specification. The proposed settings, which are not approved, are 2,000 resamples, confidence 0.95, and seed 20261113.

## Estimand that the code implements

For an ablation method, the contrast is that method's validation loss minus `full_minimax` loss. Pairs share `related_group_id`, attack condition, dependency model, and benchmark. The bootstrap resamples `related_group_id` and keeps every paired attack difference inside the drawn groups. The experimental unit is the question group, not a verifier report. A pair missing either side is counted and is not imputed. Unresolved and unauthorized gold labels are excluded from binary rates. Failed executions are counted and are not given a decision.

One related group is not enough for an interval. The reason recorded by the code is `at_least_two_related_groups_required`. The synthetic fixture is one hand-built cube, so it is not a 372-group paired sample.

Attack and benchmark splits are available only when result rows carry those fields. No such Development rows exist. Thresholds, losses, and policies were not tuned, and Final Test data was not used.
