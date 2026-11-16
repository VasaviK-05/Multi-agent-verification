# Research status

Branch `raunak-exp-3`. The frozen Experiment 3 commit is `22dbf42fcb8e75f5255a64c95248e75fedd57f55`, and that commit matches `origin/raunak-exp-3`. Later documentation edits and the Experiment 1 replay are separate uncommitted files. This note is a status summary. It is not an approval, and it does not replace the experiment documents.

`evaluation/docs/research_objective.md` still says the planned experiments have not been run and that no verifier attempts exist for `research_v1`. That sentence is current for Experiments 2 and 4. It is not current for Experiment 3, or for the Experiment 1 offline replay, which reuses the Experiment 3 reports and does not make a new verifier call.

## Completed components

- Development eligibility manifest for 372 groups and 744 candidates. Collection and Final Test flags in that manifest remain false. Experiment 3 ran under a separate research-lead authorization.
- Frozen Development cost calibration `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. The freeze records millisecond means. It does not authorize policy fitting or budget selection.
- Experiment 3 Development collection: 15,624 complete empirical cells, evidence and rule selected by all three methods, paired difference 0 with interval [0, 0]. Hashes and the reproduction check are in `experiment3_reproducibility.md`.
- Experiment 3 policy diagnosis from the stored reports: 14 feasible strategies, unique best team, no observed aggregation disagreement, cold-start explanation, and a labeled counterfactual coefficient sweep.
- Experiment 3 empirical figures, marked `EMPIRICAL`, separate from the synthetic figures.
- A synthetic resource-sensitivity grid. It concludes that a coefficient cannot be derived from that grid. It is not an empirical finding.

## Experiment 3 status

Development execution for the aggregation comparison is complete. The scientific result is a negative finding on method separation under the cold-start prior, plus a positive finding that evidence + rule is the unique minimax team among the feasible teams. The run does not establish general equivalence, an optimized resource setting, a measured dependency structure, or a result on sealed Final Test data.

## Baselines and sensitivity

The baseline protocol in `baseline_evaluation.md` has a smoke run of 8 instances. `evaluation/results/baseline/baseline_summary.json` is not present, so the full baseline has no measured summary. That smoke set includes FEVER and is not the Experiment 3 comparison.

Experiment 1 now has an offline Development replay from the frozen Experiment 3 reports. It compares full minimax, the predeclared worst-column fixed strategy, uniform feasible selection, and coverage-greedy selection. It is documented in `experiment1_offline_replay.md`. The proposal file itself remains `PENDING_APPROVAL`; this replay did not change that file and did not collect new verifier calls. Experiment 2, the multi-budget comparison, is still waiting on an approved budget set and has not been collected. Experiment 4, live runtime validation, has not been run. The sensitivity experiment that does exist is the synthetic configuration grid, not a second empirical budget study.

## Current evidence

The project can support a Development paper section on Experiment 3: what was asked, how the 15,624 cells were built, the identical method outcomes, the team ranking, the verifier failure modes, and the resource caveats. `experiment3_paper_integration.md` is that section. The Experiment 1 replay scores the other selectors on the same reports. On this Development matrix the fixed worst-column rule matches full minimax, uniform has higher expected decision loss, and greedy is infeasible for 234 candidates. That replay still cannot support a confirmatory Final Test claim.

## Remaining work

- The Experiment 1 offline replay is scored and has not been committed. A follow-up that changes the selector's resource model, or admits the 234 infeasible greedy teams, needs its own protocol before any new run.
- Decide whether any approved reputation history will ever exist. Without it, a non-cold-start aggregation comparison cannot be run, and the present tie is tied to the `Beta(1, 1)` prior.
- Experiment 2 still needs an explicit budget set if the paper claims budget sensitivity. One selected budget does not answer that question.
- Experiment 4 still needs a runtime check if the paper claims live execution matches the offline policy.
- Final Test remains sealed. It is not the next data source for exploration.
- Model-weight hashes are still unknown.
- `research_objective.md` should be revised when the protocol status is next edited, so it no longer says that no `research_v1` verifier attempts exist.

## Is there enough evidence for a complete paper?

No. Experiment 3 is complete as a Development aggregation study. The project is not complete. A paper that claims an improvement from joint game-theoretic selection, a resource-optimized policy, measured verifier dependence, or Final Test performance would go beyond the evidence.

## Are further experiments necessary?

Yes, for a claim beyond this Development replay. The matched baseline comparison now exists as the Experiment 1 offline replay. A further reputation-informed rerun is not possible until approved observations exist. Changing the budget or the selector so that the infeasible greedy team becomes feasible would be a new experiment, and it has not been started. A Final Test confirmation is a later step and is not authorized by either run.
