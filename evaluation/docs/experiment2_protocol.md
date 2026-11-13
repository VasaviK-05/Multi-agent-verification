# Experiment 2 protocol

Status: `PENDING_PERSON2_COSTS_AND_APPROVAL`. Budget values are null. Collection is not authorized.

## Question and hypothesis

Isolate the contribution of reputation by comparing the same feasible teams with and without reputation weights, at approved budgets. A difference is attributable to reputation only when reports, costs, loss, threshold, attacks, and the roster stay matched.

## Population

The same approved Development roster as Experiment 1: 372 groups, GSM8K 187, HotpotQA 185. History may supply reputation observations after collection is authorized. Final Test is prohibited. The pre-quarantine HotpotQA count of 200 is not the roster.

## Conditions

Person 2 measures attempt cost on Development under the declared verifier configuration, including model, prompt, corpus hash, hardware, warm-up, timeout, and cost unit. Those fields are still `UNKNOWN` or null. No coefficient is invented here. About three budgets are chosen only after those measurements exist, in a new settings record. `0.1 / budget` is not the proposal.

## Methods

At each approved budget, compare feasible matched baselines, including a no-reputation baseline and the reputation-weighted policy. A method that cannot meet the contributor minimum is reported infeasible. Guards are not relaxed.

## Analysis and stop

Report strategy probabilities, verifier inclusion, clean and attacked loss, coverage, and estimated cost. Strategy probabilities are not superiority. Do not run this experiment, and do not score Final Test, until costs exist and collection is authorized.
