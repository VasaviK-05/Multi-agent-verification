# Research objective and evaluation protocol

## Research topic

**Game-Theoretic Multi-Agent Framework for Adaptive AI Answer Validation using Dynamic Reputation and Strategic Verifier Selection**

## Central research question

> Does jointly selecting a verifier team and an aggregation strategy through a reputation-aware game-theoretic framework improve AI answer validation under declared resource constraints and adversarial report manipulation, while maintaining acceptable performance on clean inputs?

This is an empirical question, not an assumption that the game policy must beat every baseline. “Improve” must be interpreted from the declared loss, coverage, cost, clean-input performance, and attack results together. Comparisons must use compatible inputs, resource limits, labels, and evaluation rules.

Evaluate and report:

- Correct acceptance and correct rejection.
- False acceptance and false rejection.
- Uncertainty and decision coverage.
- Verification loss.
- Estimated verifier-attempt cost.
- Robustness under the declared attack scenarios.
- Execution failures and unresolved coverage, so an abstention or failed run is not hidden inside an accuracy figure.

## Existing offline loss formulation

### Decision loss

`app/game/models.py:LossConfiguration` stores nonnegative `false_accept`, `false_reject`, `uncertain`, and `resource_weight` values plus a cost unit and version. It does not provide scientifically calibrated constants.

In `app/game/offline/evaluation.py:outcome_loss`, a passed result has zero loss when the answer is correct and the false-accept penalty when it is incorrect; a failed result has zero loss when the answer is incorrect and the false-reject penalty when it is correct. Any non-definitive public status receives the uncertainty penalty. `Metrics.validation_loss` computes the mean of these decision penalties over examples.

### Overall offline objective

`app/game/offline/evaluation.py:summarize` computes the objective used for payoff cells:

```text
mean decision loss + resource_weight × average estimated attempt cost
```

The estimated cost is the average strategy attempt cost recorded by offline replay. The `mean_loss` value used in the payoff matrix includes the resource term. `Metrics.validation_loss` reports decision loss without that term. Thus the code exposes both the decision-only validation loss and the cost-augmented game objective; reports should label them distinctly.

The offline fitting path (`construct_payoffs`, then `fit_policy`) evaluates candidate team/aggregation strategies across the declared attacks on Development data. `build_policy` consumes the resulting payoff matrix. Mixed-policy outcome summaries weight strategy outcomes by the policy probabilities; they do not select the best outcome after seeing a test example.

### Repository pilot proposal values — unapproved

`app/game/offline/pilot_proposal.py:propose` writes a fitting proposal explicitly marked unapproved and does not create a policy. Its proposed values are:

| Parameter | Proposed value | Status |
|---|---:|---|
| False-accept penalty | 1.0 | Unapproved proposal; not calibrated or finalized |
| False-reject penalty | 1.0 | Unapproved proposal; not calibrated or finalized |
| Uncertainty penalty | 0.2 | Unapproved proposal; not calibrated or finalized |
| Resource weight | `0.1 / budget` | Unapproved proposal; not calibrated or finalized |

In that pilot code, `budget` is the measured total attempt-cost budget in milliseconds and the cost unit is `ms`. The proposal records `approval_status='UNAPPROVED; fitting must wait for user decision'` and `policy_created=False`. These values are not approved research settings.

**Budget comparability issue:** `0.1 / budget` changes the coefficient whenever the budget changes. This also changes the relative contribution of resource cost to decision loss, making budget-sensitivity comparisons difficult to interpret. The research team must decide whether to use a fixed resource coefficient and one consistent cost scale across budget conditions. Do not change the proposal or silently substitute a value before that decision.

### Offline versus live runtime

The loss is used by offline evaluation and policy-related code, including `app/game/offline/evaluation.py`, `app/game/offline/build.py`, and `app/game/research/comparison.py`. The live game path in `app/game/execution.py` selects and executes a team, calls `app/game/finalization.py:finalize_decision`, and records estimated attempt cost and outcomes. It does not calculate the above loss while validating an answer. The baseline experiment is a separate `execution_mode="baseline"` path and does not optimize this loss. Do not describe the baseline as optimizing the game objective.

The current loss has no separate parameter for execution failure or unresolved coverage. Their treatment in the primary research loss needs explicit approval. At present, a non-definitive outcome is charged the uncertainty penalty; reports should still show failures and unresolved outcomes separately.

## Decision threshold

`app/game/execution_contract.py:ExecutionContract.threshold` stores a required threshold in each execution contract. `app/decision/decision_engine.py:DecisionEngine` defaults to `ABSTAIN_ABOVE = 0.55`; game finalization passes the contract's value explicitly to the engine.

The score is an uncalibrated signed score in `[-1, 1]`, not a probability. In `app/decision/decision_engine.py:_status`:

- A raw score greater than the positive threshold produces `passed`.
- A raw score less than the negative threshold produces `failed`.
- A score between those strict bounds, including equality at either bound, produces `uncertain`.

The pilot proposal uses 0.55, but it is part of an unapproved proposal. **0.55 is an implementation default, not automatically an approved experimental setting.** The team must decide whether to freeze it before final evaluation or select a value using Development data and then freeze it.

## Minimum contributors and coverage

These three concepts have different meanings in code and must be reported separately.

### 1. Minimum contributors required for the selected team

`app/selection/verifier_selector.py:DEFAULT_DIFFICULTY_RANGE` currently defines minimum/maximum selected counts as easy `(2, 2)`, medium `(2, 3)`, and hard `(3, 4)`. `VerifierSelector.minimum_count` captures the minimum in the selection plan. `app/game/models.py:PlanningContext.minimum_participant_count` uses that count for hard questions and at least two for other difficulty bands. `app/game/strategies.py:enumerate_strategies` rejects a proposed team smaller than this value.

The runtime baseline uses the plan minimum and applies `max(2, minimum)` outside the hard band in `app/orchestration/validation_orchestrator.py:ValidationOrchestrator.validate`. In contrast, the unapproved pilot proposal explicitly overrides the difficulty range to `(2, 2)` for easy, medium, **and hard**. Therefore, the hard-question requirement depends on the selected configuration. The research team must confirm and record the rule that applies to each experiment; do not report the pilot override as the production default.

### 2. Actual contributors after execution

Selected team size is not the number of actual contributors. Abstentions, unavailable verifiers, failed executions, zero-confidence reports, and reports excluded from an aggregation can reduce actual contribution. `app/game/finalization.py:finalize_decision` checks the usable contributors after all selected-team outcomes are recorded. If the count falls below `PlanningContext.minimum_participant_count`, the public status is forced to `uncertain` with reason `minimum_contributors`.

The same finalization can force uncertainty for unresolved or unachieved factual requirements. When the execution contract requires all selected verifiers to return, a failed or unavailable selected verifier also causes `selected_execution_incomplete`. The non-game baseline orchestration has corresponding contributor and achieved-coverage guards in `app/orchestration/validation_orchestrator.py`.

### 3. Coverage requirements during planning and evaluation

The game does not define a universal minimum coverage percentage. Instead, `enumerate_strategies` checks that the union of selected candidates’ **expected capabilities** covers every known requirement and that the team satisfies the minimum size and budget. This is a team-feasibility rule, not observed coverage.

After execution, `finalize_decision` derives **achieved coverage** from usable verifier reports via `app/decision/coverage.py:factual_capabilities` and checks whether required capabilities were actually achieved. Unknown, invalid, unsupported, or missing requirements can prevent a definitive result. These expected-capability, achieved-report, and contributor checks are not interchangeable. Any proposed minimum percentage coverage constraint for fitting or evaluation is not explicit in the inspected loss/configuration code and remains pending team confirmation.

## Planned research experiments

All experiments below are plans, not completed results. Freeze the protocol and compare methods under matched information, resource accounting, and eligible examples.

### Experiment 1 — Clean and attacked performance

Evaluate clean inputs and the declared report-corruption scenarios: forced support, forced rejection, confidence inflation, and verifier suppression. Compare the full joint game policy against compatible greedy, fixed-team, uniform, and aggregation-restricted baselines. Report decision and cost-augmented loss, false acceptance/rejection, coverage, uncertainty, selective risk, estimated attempt cost, execution failures, unresolved coverage, and worst-case expected loss across the frozen scenarios.

### Experiment 2 — Budget sensitivity

Use Development data to select approximately three budget levels, then freeze them. Compare only strategies that are feasible and appropriately matched at each level. Report verifier inclusion frequencies, strategy probabilities, decision loss, cost-augmented loss, coverage, and estimated cost. Keep the resource coefficient and cost scale consistent across conditions unless the team explicitly approves another design; resolve the `0.1 / budget` comparability issue first.

### Experiment 3 — Aggregation and dependency ablation

Compare:

1. Joint verifier-team and aggregation game.
2. Team-selection game restricted to reputation aggregation.
3. Team-selection game restricted to dependency-group aggregation.

Keep data, budgets, attacks, policies’ training information, thresholds, and evaluation rules matched. This separates the contribution of choosing aggregation from the contribution of dependency modelling. Repository aggregation identifiers are `reputation_weighted` and `dependency_group` (`app/game/models.py:AGGREGATIONS`).

### Experiment 4 — Live runtime validation

Test representative supported examples using the actual game runtime. Verify policy loading, selected team, aggregation, complete execution records, replay parity, resource/provenance failures, and latency. Report **estimated verifier-attempt cost** separately from **measured wall-clock latency**; these are different quantities.

## Threat model and assumptions

### Attack scenarios

The current offline attack implementation is report-level corruption (`app/game/offline/attacks.py:AttackSpecification`, `enumerate_attacks`, and `transform`):

- **Clean:** no report transformation.
- **Forced support:** targeted eligible directional reports are transformed to a full-confidence support report.
- **Forced rejection:** targeted eligible directional reports are transformed to a full-confidence rejection report.
- **Confidence inflation:** preserve a directional report's direction and raise its normalized report confidence to the maximum.
- **Verifier suppression:** turn a targeted report into either unavailable or abstention, depending on the declared specification. The pilot proposal currently sets suppression to unavailable.

The existing attack enumerator targets a configured dependency/failure group and applies transformations only where a compatible report exists; it preserves already abstaining reports. This is not a model compromise, evidence-source compromise, or proof of robustness to arbitrary attacks. Attack strength, attack implementation, targeted reports/groups, suppression behavior, applicability, and severity must be specified and frozen using Development data before final testing. Report all declared attacks, not only favorable ones.

### Dependency assumptions

`app/game/dependencies.py:DependencyRegistry` records configured shared resources/compromise pathways and unresolved verifiers. It forms connected failure components across the registry. `app/decision/dependency_aggregation.py:aggregate_dependency_groups` aggregates within each component and then combines groups, using the highest active member reliability as the group influence; it has unweighted fallbacks when reliability weights are zero.

The repository does not establish empirically which verifiers share evidence sources, models, prompts, data, or failure modes. The pilot proposal declares no known dependency pathways and places all verifier names in `unresolved` with `unknown_treatment='shared_unknown'`, which conservatively treats them as one unknown group. This is an explicit proposal assumption, not verified dependence evidence. The team must document which components may be shared, how evidence supports those assignments, how unknowns are grouped, and whether these assumptions remain fixed for each comparison. Do not claim robustness beyond these declared report-level scenarios and dependency assumptions.

## Research protocol decisions

| Decision | Current repository status | Research status |
|---|---|---|
| Loss weights | `pilot_proposal.py` proposes false acceptance 1.0, false rejection 1.0, uncertainty 0.2; explicitly unapproved | Pending team approval; not calibrated/final |
| Resource cost coefficient | Proposed `0.1 / budget` in milliseconds; varies with budget | Pending decision; budget-comparability concern. Evaluate a fixed coefficient and consistent cost scale |
| Decision threshold | `ExecutionContract.threshold`; engine default and pilot proposal are 0.55 on an uncalibrated signed score | Pending freeze; Development selection only if approved |
| Minimum contributors | Default difficulty minima are easy 2, medium 2, hard 3; pilot proposal overrides all bands to 2 | Pending confirmation and documentation for the chosen experimental contract |
| Minimum coverage | No minimum percentage found. Strategy legality uses expected capability coverage; finalization checks achieved capability coverage | Pending confirmation if an additional percentage constraint is intended |
| Budget levels | No final research budget set by the reviewed code | Select approximately three feasible levels using Development data, then freeze |
| Attack strengths | Code defines full-direction/full-confidence report transformations and suppression modes; no approved research severity schedule | Calibrate/apply using Development data, then freeze before final testing |
| Dependency assumptions | Registry supports known pathways and shared unknown groups; pilot proposal groups all names as unresolved | Document evidence and assumptions, then freeze; current relationships are not verified |
| Failure and unresolved loss | No dedicated penalty field; non-definitive public results receive uncertainty loss in offline evaluation | Decide whether additional failure/unresolved treatment is needed; keep supporting counts visible |
| Scenario aggregation | Offline fitting forms one payoff column per enumerated attack and solves the game; final reporting rule still needs a declared estimand | Confirm worst-case versus weighted-scenario reporting and how policy randomization enters it |

## Research integrity and data separation

- Use **History** only to estimate verifier reputation.
- Use **Development** for payoff construction, policy fitting, baseline selection, and configuration decisions.
- Keep **Final test** out of tuning, threshold selection, model/policy selection, and baseline selection.
- Freeze the protocol, code/configuration versions, estimands, comparison rules, and analysis before final testing.
- Report every declared clean and attacked scenario, not only favorable outcomes.
- Report undefined metrics honestly. Selective risk is undefined when decision coverage is zero.
- Do not fabricate missing metrics or infer results from incomplete execution.

The current repository audit documentation records that `evaluation/datasets/unified/final_test.json` and some of its candidate/reference information were previously inspected during candidate-answer auditing and pilot preparation. It therefore cannot be described as an unseen protected holdout retroactively. Preserve and disclose that exposure; use a custodian-controlled unseen holdout if the capstone requires a protected confirmatory final evaluation.

## Repository references inspected

- Loss schema: `app/game/models.py:LossConfiguration`.
- Offline loss and payoff fitting: `app/game/offline/evaluation.py:outcome_loss`, `summarize`, `construct_payoffs`, `fit_policy`; `app/game/offline/build.py:development_diagnostics`.
- Unapproved pilot settings: `app/game/offline/pilot_proposal.py:propose`.
- Threshold contract and decision: `app/game/execution_contract.py:ExecutionContract`; `app/decision/decision_engine.py:DecisionEngine`, `ABSTAIN_ABOVE`, `_status`.
- Team legality and contributors: `app/game/models.py:PlanningContext.minimum_participant_count`; `app/game/strategies.py:enumerate_strategies`; `app/game/finalization.py:finalize_decision`; `app/selection/verifier_selector.py:DEFAULT_DIFFICULTY_RANGE`, `VerifierSelector.minimum_count`.
- Runtime coverage and uncertainty guards: `app/orchestration/validation_orchestrator.py:ValidationOrchestrator.validate`; `app/decision/coverage.py:factual_capabilities`.
- Attack/dependency definitions: `app/game/offline/attacks.py`; `app/game/dependencies.py:DependencyRegistry`; `app/decision/dependency_aggregation.py:aggregate_dependency_groups`.
- Prior dataset and holdout audit: `evaluation/docs/dataset_audit.md`, `evaluation/docs/candidate_answer_validation_audit.md`, and `evaluation/docs/existing_split_research_readiness.md`.
