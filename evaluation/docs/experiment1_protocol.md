# Experiment 1 protocol proposal

Status: `PENDING_APPROVAL`. Proposal ID `proposal:experiment1:research_protocol_v1`. There is no frozen specification ID. The machine-readable proposal is `evaluation/config/experiments/experiment1_proposal.json`.

## Question

On matched eligible Development examples, compare the joint team-and-aggregation policy with the declared baselines under clean reports and the declared report-corruption attacks. This does not assert that the joint policy is better.

## Methods

`full_minimax`, `coverage_aware_greedy`, `deterministic_minimax`, `clean_development`, `uniform`, `fixed_reputation_weighted`, and `fixed_dependency_group`. Mixed policies use the fitted probabilities. No seed is chosen because it looks favorable.

## Scenarios

Clean, forced support, forced rejection, confidence inflation, and suppression. Suppression is proposed as `unavailable` and is not approved. Attacks are report transformations, not model or evidence compromise.

## Reported outcomes

For every method and scenario: correct acceptance and rejection, false acceptance, false rejection, coverage, uncertainty, selective risk (undefined at coverage 0), decision-only loss, cost-augmented loss, estimated attempt cost, execution failures, and unresolved coverage. Also report worst-case expected cost-augmented loss, which is the proposed primary outcome and is not approved.

## Data

Development fitting may use only an approved eligibility manifest. The current exploratory audit is provisional and does not authorize this run. History is for reputation only. Final Test is prohibited. Collection is not authorized.
