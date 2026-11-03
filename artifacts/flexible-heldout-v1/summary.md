# Held-out results: frozen flexible verifier teams

Completed the authorized 80 examples / 320 verifier attempts / 400 local model generations. All start/completion ledgers are exact, integrity gaps are zero, all generation requests returned HTTP 200, and frozen candidates, original study inputs and historical bundles remain unchanged.

Freeze ID: `bcba68b5bd2857246fb3c4d9248f0eb2af4fd891b5b694335799826942ae519e`. Exact policy/context/resource IDs and versions are in `freeze-manifest.json`; per-call integrity and scope checks are in `final-verification.json`.

Each cohort has 20 paired groups, 20 correct and 20 incorrect examples. Rates use all 40 examples unless explicitly conditional on the 20 correct/incorrect cases. No policy was refitted and no reputation or threshold updated.

## Arithmetic

Frozen rule singleton: 20 accepts, 20 rejects, 0 uncertainties; coverage 100.0%; false accepts 0/40 and false rejects 0/40; decision loss 0.000; selective risk 0.000%. No selected execution failures.
Conditional false acceptance: 0/20 incorrect cases; conditional false rejection: 0/20 correct cases.
The development-best fixed strategy is identical and ties exactly; there is no demonstrated game-theory advantage over that baseline.
Existing greedy complete-team baseline: 15 accepts, 20 rejects, 5 uncertainties; coverage 87.5%; false accepts 0, false rejects 0; decision loss 0.025; selective risk 0.000%.
95% paired-group bootstrap interval for flexible-minus-greedy coverage: [5.0%, 22.5%]. Flexible coverage interval: [100.0%, 100.0%]; selective-risk interval: [0.000%, 0.000%]. 10000 paired cluster resamples, seed20261102.
The separately reported minimum-two fixed-greedy-team ablation has 85.0% coverage. No minimum-two fit was feasible and no minimum-two policy/probabilities were invented.
Singleton selection probability is 1; sizes 2–4 remain 0. Offline replay selects the singleton on all 40 examples. Physical collection executed all four verifiers per example, not a singleton deployment.
Measured individual rule call mean: 0.222 ms; historical selected-team estimate: 9.678 ms. Neither is measured singleton end-to-end deployment latency.
Uncertainty reasons: {}.

Report-level attack results:

- confidence_inflation: coverage 100.0%; false accepts 0, false rejects 0, uncertainties 0; decision loss 0.000; selective risk 0.000%.
- forced_rejection: coverage 100.0%; false accepts 0, false rejects 20, uncertainties 0; decision loss 0.500; selective risk 50.000%.
- forced_support: coverage 100.0%; false accepts 20, false rejects 0, uncertainties 0; decision loss 0.500; selective risk 50.000%.
- suppression: coverage 0.0%; false accepts 0, false rejects 0, uncertainties 40; decision loss 0.200; selective risk undefined.

## Factual

Frozen evidence singleton: 19 accepts, 20 rejects, 1 uncertainties; coverage 97.5%; false accepts 0/40 and false rejects 1/40; decision loss 0.030; selective risk 2.564%. No selected execution failures.
Conditional false acceptance: 0/20 incorrect cases; conditional false rejection: 1/20 correct cases.
The development-best fixed strategy is identical and ties exactly; there is no demonstrated game-theory advantage over that baseline.
Existing greedy complete-team baseline: 16 accepts, 20 rejects, 4 uncertainties; coverage 90.0%; false accepts 0, false rejects 1; decision loss 0.045; selective risk 2.778%.
95% paired-group bootstrap interval for flexible-minus-greedy coverage: [0.0%, 15.0%]. Flexible coverage interval: [92.5%, 100.0%]; selective-risk interval: [0.000%, 7.895%]. 10000 paired cluster resamples, seed20261102.
The separately reported minimum-two fixed-greedy-team ablation has 42.5% coverage. No minimum-two fit was feasible and no minimum-two policy/probabilities were invented.
Singleton selection probability is 1; sizes 2–4 remain 0. Offline replay selects the singleton on all 40 examples. Physical collection executed all four verifiers per example, not a singleton deployment.
Measured individual evidence call mean: 194.093 ms; historical selected-team estimate: 188.799 ms. Neither is measured singleton end-to-end deployment latency.
Uncertainty reasons: {'decision_threshold': 1, 'minimum_contributors': 1, 'missing_achieved_coverage': 1}.

Report-level attack results:

- confidence_inflation: coverage 97.5%; false accepts 0, false rejects 1, uncertainties 1; decision loss 0.030; selective risk 2.564%.
- forced_rejection: coverage 97.5%; false accepts 0, false rejects 20, uncertainties 1; decision loss 0.505; selective risk 51.282%.
- forced_support: coverage 97.5%; false accepts 19, false rejects 0, uncertainties 1; decision loss 0.480; selective risk 48.718%.
- suppression: coverage 0.0%; false accepts 0, false rejects 0, uncertainties 40; decision loss 0.200; selective risk undefined.

## Interpretation

The clean headline results repeat development performance on these reserved groups. They support minimum-one as a narrowly scoped offline candidate, not broad adoption or activation. Collect more independently grouped, source-independent evidence and assess independent failure paths before broader use. Retaining a minimum-two contributor guard is a separate abstention contract; its infeasible fit supplies no deployable policy.

These reservations were procedural and source-known, not blinded. The prepared corpus contains most test facts, and permitted references were fixed beforehand. This does not establish unseen-source, unseen-document, reference-free or broad domain/difficulty generalization. Twenty groups per cohort leave substantial uncertainty; zero-error bootstrap intervals can degenerate and do not establish zero population risk.

Greedy retains the original selector ranking, relative-cost heuristics and target-count defaults; only contributor/coverage finalization and resource settings match the flexible candidate. This is the existing complete-team selection baseline, not the legacy adaptive early-stopping pipeline or an otherwise identical optimizer.

The declared shared-failure group may corrupt every selected verifier. Simulated report corruption remains damaging and is not a real upstream compromise experiment. More verifiers do not automatically create independent protection. The 90% development coverage constraint was not treated as a guaranteed test result.

The full report and machine-readable outcomes are `report.md`, `heldout-results.json`, and each cohort’s `replay-outcomes.json`. Original evaluation seals and code copies were preserved; `evaluation-code-correction-v2.diff` documents only the Windows path gate and explicit correction-chain handling. No policy setting or metric definition changed.

Later integration: use the arithmetic/factual frozen `policy.json`, `context.json`, `contract.json` together, with `flexible_team_requirements_v1` minima (1,1). Verify exact actual resource identities and review this limited evidence before a separate activation decision. Do not refit on these test outcomes; changed policies require new reserved evaluation groups.

No semantic test cohort was collected. Semantic was merely one verifier in the authorized full-roster arithmetic/factual recordings. No algorithms, DB, frontend or API routing changed; no commit, push, merge or activation occurred.
