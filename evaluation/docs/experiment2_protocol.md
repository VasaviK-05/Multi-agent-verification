# Experiment 2 protocol proposal

Status: `PENDING_PERSON2_COSTS_AND_APPROVAL`. Proposal ID `proposal:experiment2:research_protocol_v1`. Budget values are null. There is no frozen specification.

## Procedure

Person 2 measures attempt cost on Development under a declared model, prompt, corpus, hardware, warm-up, timeout, and cost-unit definition. Person 1 does not invent those measurements. From the measurements, the research lead and Person 2 choose about three budgets that change which teams are feasible, then approve them in a new settings record. Each approved budget gets its own fitted and frozen policy. The resource coefficient stays fixed across those budgets. `0.1 / budget` is not the proposal.

## Comparison

At each budget, compare only feasible matched baselines. Report strategy probabilities, verifier inclusion frequencies, clean and attacked loss, coverage, and estimated cost. A method that cannot meet the contributor minimum and expected coverage is reported infeasible. Guards are not relaxed. A baseline over the budget may be shown only as an unconstrained reference.

## Runtime

Actual execution cost and latency on a representative live subset belong to Experiment 4 and require Person 2 timing plus a Person 3 policy. They are not substituted for the estimated attempt cost.

## Data

Budget selection uses Development only. Final Test outcomes are not an input. Collection is not authorized.
