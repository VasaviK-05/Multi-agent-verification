# Experiment 1 protocol

Status: `PENDING_APPROVAL`. This document is not a frozen specification and collection is not authorized.

Machine-readable proposal: `evaluation/config/experiments/experiment1_proposal.json`. Shared configuration pointers: `evaluation/config/research_v1/protocol_index.json`.

## Question and hypothesis

On the approved Development roster, compare the joint team-and-aggregation policy with the declared baselines under clean reports and report-corruption attacks. The hypothesis is that the comparison is estimable. It does not assert that the joint policy is better.

## Population

`research_v1_exploratory_eligibility_approved_v1`, body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. That roster has 372 groups: GSM8K 187 and HotpotQA 185 after the shared-context quarantine. The pre-quarantine HotpotQA count of 200 is not this roster. FEVER and MultiNLI are out of scope. History is for reputation only. Final Test is prohibited.

Eligibility approval does not authorize this run. Synthetic incorrect labels stay `SYNTHETIC_INCORRECT`. Unresolved labels stay unresolved.

## Conditions

Clean reports, forced support, forced rejection, confidence inflation, and suppression. Suppression remains `unavailable` until a research lead approves an implemented suppression mode. Attacks transform reports. They do not compromise models or the corpus.

## Methods

`full_minimax`, `coverage_aware_greedy`, `deterministic_minimax`, `clean_development`, `uniform`, `fixed_reputation_weighted`, and `fixed_dependency_group`. Verifier and resource identities are the pending files `evaluation/config/research_v1/verifier_config.json` and `evaluation/config/research_v1/resource_config.json`.

## Analysis

Pair on `related_group_id` and attack. Report false acceptance, false rejection, coverage, uncertainty, and validation loss. Do not impute missing runs. Bootstrap settings are pending in the shared settings proposal. No seed is chosen because it looks favorable.

## Stop

Do not collect recordings and do not score Final Test until the separate authorization records are signed.
