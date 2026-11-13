# Experiment 3 protocol proposal

Status: `PENDING_APPROVAL`. Proposal ID `proposal:experiment3:research_protocol_v1`. There is no frozen empirical specification. The synthetic runner under `evaluation/experiments/experiment3/synthetic/` is a controlled fixture, not this experiment's empirical result.

## Question 1 — aggregation choice

Compare `full_minimax`, `fixed_reputation_weighted`, and `fixed_dependency_group` on the same reports, questions, reputation snapshot, budget, loss, and coverage rules. A tie that assigns probability to one of two equal strategies is not evidence that the aggregation is better.

## Question 2 — dependency model

An empirical claim requires a documented dependency model and a stated alternative, with individual failures separated from correlated failures at comparable severity. The repository has no such empirical evidence. `shared_unknown` puts every unresolved verifier in one component. The two-group registry is a controlled synthetic assumption. Synthetic output must be labelled `SYNTHETIC`. It must not be described as a real verifier dependency or as a robustness improvement.

## Outputs

Loss, false acceptance, false rejection, coverage, uncertainty, selective risk, cost, worst-case expected loss, aggregation frequencies, and verifier inclusion frequencies. Final Test is prohibited. Collection is not authorized.
