# Three-outcome prototype tradeoffs (2026-10-31)

Uncertainty is an intended public decision, not a failed binary classification.
The earlier 90% exploratory constraint is preserved as an infeasibility result,
not a universal product acceptance gate. This follow-up varies only expected
clean-development coverage at 0, 0.25, 0.50, 0.75 and 0.90. Existing losses
(1/1/0.2), threshold 0.55, Beta(1,1) history, minimum informative contributors,
achieved coverage, failure/dependency assumptions, full-roster budgets and measured
costs stay fixed. The reliability-first solver is reused without redesign.

Expected policy coverage averages finalized outcomes over the development
population and strategy distribution. It is not runtime confidence, a guarantee
on one request, or a request-specific routing rule. Correct/incorrect labels are
unchanged when the system abstains; reference agreement, answer truth and evidence
sufficiency remain distinct. No third ground-truth class was invented.

## Reference eligibility and the verified construction gap

The selector's existing prerequisite contract makes Semantic ineligible for absent,
blank or judgment-list context, and eligible for nonblank prose. It neither checks
relevance nor certifies that the reference is true or sufficient. Evidence does
not require user reference. Planning captures reference availability and includes
it in compatibility; changed resource/configuration identities still require their
exact existing provenance binding. Task-conditioned snapshots remain history-only.

Runtime planning/resolution is already lazy and excludes Semantic before resolving
or executing it when its prerequisite is absent. Abstaining, unavailable and
nonparticipating attempts are excluded from history reputation learning; they are
not negative observations.

One owned offline entry-point gap was verified: the known project/arithmetic
zero-argument factories eagerly construct Semantic before the collector's
per-example eligibility check. `validate_factory_prerequisites` now rejects those
factory requests before import/construction when any example lacks usable reference.
It reports every affected example together. Existing reference-present requests
and legacy zero-argument factory APIs retain their behavior. No constructor,
verifier algorithm, model resource fingerprint or calibration was changed.

This conservative block is explicitly a **factory limitation**, not an Evidence
prerequisite. No-reference Evidence collection through the eager full-roster factory
is blocked until the adapter owner provides a prerequisite-aware partial-roster
constructor. A compatible dedicated factory can preserve Evidence eligibility.
The collector still skips ineligible calls; no new collection was run here.

## Why references did not make Semantic informative

`semantic-reference-audit.json` retains the first grouped correct/incorrect pair in
each history/development partition, including actual question/answer/reference,
independent-label meaning, raw report metadata, normalized abstention/strength and
task-conditioned history counts. The prior `decision-diagnostics.json` retains
their aggregation votes and final decisions. These are existing recordings; no
embedding, verifier or generation call was rerun.

Semantic's documented output is cosine resemblance to supplied context, not
probability of truth. Its explicit SUPPORT/REJECT/UNSURE decision determines
direction/abstention; the existing normalizer uses the documented clipped score
as uncalibrated vote strength. It does not convert low similarity to high rejection
confidence or treat UNSURE as a negative vote. No verified interpretation defect
was found, and no score normalization/threshold was changed.

The default public `question_answer` mode compares the question concatenated with
the candidate against the reference. Semantic-equivalence questions themselves
contain that reference. All 40 history candidates received SUPPORT (20 correct,
20 incorrect), yielding Beta(21,21), mean 0.5 and zero effective influence. Only
Confidence is informative, so every semantic strategy correctly remains uncertain
under minimum two. The arithmetic task has different history (23 directional
observations, mean 16/25); factual Semantic is also at 0.5. No cross-task borrowing
was applied. Reference presence alone cannot establish usefulness.

Verifier-owner handoff: inspect `SemanticVerifier.comparison_text`, its retained
`comparison_method`, `compared_text`, raw similarities and independent paired labels.
Review whether the existing comparison mode matches reference-equivalence intent.
An answer-only mode is an available public interface, but testing it requires a
separate reviewed configuration and fresh grouped recordings. No change was made
to teammate code or reference text, and improved performance is not assumed.

## Reading uncertainty and error metrics

Reports separate false acceptance/rejection from uncertainty. Selective risk is
errors divided by decided cases, undefined when no decisions occur. Zero errors
with zero (or numerically negligible) coverage is not successful verification.
Conversely, one correct guard-driven abstention is not a defect merely because it
reduces aggregate coverage.

Reason counts distinguish minimum contributors, missing achieved coverage,
execution incompleteness and weak/conflicting score-band signals. Guard counts can
overlap. Policy mass on zero-coverage strategies is reported separately: a solver
may deliberately choose abstention under the approved uncertainty/attack objective.
None of these categories changes the independent correctness label.

Outputs are local and ignored under `build/multitask-uncertainty-sweep42/`.
Each feasible cohort/target has `policy.json` and `report.json`; infeasible targets
have reports without policies. All fourteen strategies, including zero and tiny
positive probabilities, are retained. The epsilon=1e-8 loss cap can permit tiny
positive masses at target zero; these must not be rounded into evidence of useful
coverage or forcibly pruned. No deployment or publication setting is selected.

```powershell
.venv/Scripts/python.exe -m scripts.multitask_uncertainty_sweep
.venv/Scripts/python.exe -m pytest tests/test_game_three_outcomes.py tests/test_game_collection.py tests/test_game_task_conditioning.py tests/test_game_reliability_first.py tests/test_verifier_selector.py -q
```

The producer requires a fresh output directory. It independently reconstructs and
matches the frozen development evaluation, repeats each feasible fit, validates
certificates/serialization and compares scientific outputs at absolute tolerance
1e-12. Source calibration, context, manifest, recordings and old policy bytes are
preserved. Fitting has an open-audit guard against custody payloads and never
initializes real verifier factories. No fresh inference, calibration, final-test
access, production writes, Git publication or activation is authorized by this run.

## Completed sweep and prototype review

Seven policies were exported/reloaded, certificate-validated and repeat-checked;
eight target/cohort combinations remain explicitly infeasible. All strategies
remain present. `comparison.json` and the complete readable `comparison.md` contain
every positive probability, clean/per-attack coverage, uncertainty, FA/FR,
selective risk, validation loss, estimated cost, separate old cost-inclusive
diagnostic and uncertainty reasons. No source scientific setting was changed.

- Arithmetic target 0: achieved coverage 2.317073168e-8 (fraction, effectively
  abstention), uncertainty 0.999999976829; loss 0.199999995366; cost 91.130919 ms;
  worst validation loss 0.200000010. The tiny nonzero mass is epsilon-permitted,
  not useful verification. Selective risk is formally zero for that tiny decided
  mass; it does not establish reliability.
- Arithmetic target 25%: achieved coverage 25%, uncertainty 75%, clean FA/FR zero,
  selective risk zero, validation loss 0.15, cost 6468.750048 ms, worst loss
  0.286363646; always-abstaining strategy probability 0.696969593266.
- Arithmetic target 50%: achieved coverage 50%, uncertainty 50%, clean FA/FR zero,
  selective risk zero, validation loss 0.10, cost 12846.372147 ms, worst loss
  0.372727283; always-abstaining probability 0.393939290236.
- Arithmetic target 75%: achieved coverage 75%, uncertainty 25%, clean FA/FR zero,
  selective risk zero, validation loss 0.05, cost 19223.994247 ms, worst loss
  0.459090919; always-abstaining probability 0.0909089872054. Target 90% remains
  infeasible (maximum finalized clean coverage 82.5%).
- Semantic target 0: all uncertainty, loss 0.2, cost 42.432737 ms, selective risk
  undefined, always-abstaining probability one. All positive targets are infeasible.
- Factual target 0: all uncertainty, loss 0.2, cost 188.903554 ms, selective risk
  undefined, always-abstaining probability one.
- Factual target 25%: coverage 25%, uncertainty 75%, clean FA/FR zero, selective risk
  zero, loss 0.15, cost 10677.138030 ms, worst loss 0.32. Probability 2/3 is on
  reputation-weighted Evidence+Confidence and 1/3 on reputation-weighted
  Evidence+Rule (zero clean coverage). Targets 50/75/90% are infeasible; maximum is
  37.5%. Under forced support/rejection, coverage is 31.6667%, false acceptance/
  rejection expected counts are respectively 5.3333/7.3333 of 40, selective risks
  0.421053/0.578947, and validation losses 0.27/0.32. Suppression safely abstains
  everywhere. A clean zero-error result is not a robustness claim.

Arithmetic target 50% positive probabilities are Rule+Confidence/weighted
0.6060604653198649, Evidence+Rule/weighted 0.3939392902356899, and
Rule+Semantic/grouped 2.444444452815835e-7. These unedited solver probabilities
illustrate the normative choice: about half-population useful clean coverage costs
more and has higher attacked loss than the 25% variant. The tiny Semantic mass is
not evidence of material usefulness or aggregation superiority. All other positive
allocations, including tiny masses at the other targets, are in the comparison.

**Recommendation for review:** arithmetic `arithmetic/coverage-50/policy.json` is a
reasonable bounded engineering prototype for these constructed integer additions
with the recorded trusted-reference/context assumptions. It balances useful clean
decisions against cost while preserving half-population uncertainty. The 25% option
is preferable if minimizing cost/adverse-model loss dominates usefulness; 75% buys
more decisions at greater cost/risk. This is a normative review choice, not a
universal optimum or autonomous acceptance recommendation.

For the source-snapshot population/currency/area scope, consider
`factual/coverage-25/policy.json` only as a shadow/human-reviewed prototype. Its
observed clean usefulness is limited and its shared-dependency attack risks are
substantial. If that threat model is credible for autonomous actions, the data do
not justify automatic factual acceptance; retaining uncertainty is defensible.
No useful semantic-equivalence prototype exists under these recordings and guards.

All candidate paths above are relative to `build/multitask-uncertainty-sweep42/`.
No policy is activated. Shared embedding/NLI plus conservative unknown treatment
connect the informative roster into one compromise group; no coverage target creates
independent evidence. These are 20-group, 40-candidate constructed development sets,
with source-known procedural reservations, not independent held-out evidence.

Representative retained history pairs show the Semantic limitation directly:

- Arithmetic reference `864`: correct answer `864` raw similarity 0.530877950,
  incorrect `865` 0.512855537; both SUPPORT, both normalized directional.
- Semantic reference `Bailey brought a basket to the station.`: correct passive
  paraphrase 0.896601086, incorrect bicycle-repair sentence 0.817192284; both SUPPORT.
- Factual reference population of Belgium 11941781: correct sentence 0.961614888,
  constructed incorrect population 11954126 scores 0.949776176; both SUPPORT.

These scores measure resemblance, not equality of numeric facts or truth. Full
reference text, independent labels, compared text and development pairs are retained
in the audit. Missing a reference is not what caused these supported-but-uninformative
votes. The constructor fix addresses a separate entry-point defect and does not
change any empirical payoff or reputation.

## Validation, changed files and separate owners

The new explicitly synthetic tests demonstrate acceptance/rejection, insufficient
coverage, conflicting signals, abstention, failed execution, missing-reference
construction/dispatch protection and absence of negative reputation updates.
Existing task/reference routing, version/certificate, final-input isolation and
legacy behavior tests remain intact. Focused tests passed 188/188 and broader
affected tests passed 220/220. The only initial failure was a new synthetic history
fixture with a development execution ID; correcting its identity resolved it.
There are no reproduced baseline failures in these runs. No assertion was weakened.

Thirty actual analyzer/task-router/provider/finalizer checks across every positive
strategy in all seven variants match retained replay on correct/incorrect examples.
They use a **recorded-resource observer simulation**, not new live resource
validation. They issue zero network/generation calls. Each variant is an explicitly
selected episode; runtime never routes by desired coverage or correctness labels.
The previous live-resource retained-report validation remains preserved separately.

Exact current-turn changed/new files:

```text
app/game/offline/collect.py
scripts/multitask_uncertainty_sweep.py
scripts/multitask_uncertainty_report.py
scripts/validate_uncertainty_sweep.py
tests/test_game_three_outcomes.py
docs/game_policy_build.md
docs/multitask_uncertainty_tradeoffs.md
```

All earlier dirty work and artifacts are preserved. No verifier/retrieval/generation,
DB, API, frontend or unrelated orchestration files changed.

Verifier/adapter-owner tasks: review Semantic's public comparison intent against
the retained paired reproducer; expose prerequisite-aware partial-roster construction
in the eager full-project adapter without changing Evidence's prerequisites;
review retained Confidence numeric disagreements rather than changing our guards.
Integration/study-owner tasks: review the proposed bounded prototype target and
adverse-model risks, retain explicit question/task/reference/resource compatibility,
define the user reference contract and human review behavior, and separately
authorize any future data collection, held-out evaluation or activation. No such
integration or new experiment was performed here.

Additional reproducible commands:

```powershell
.venv/Scripts/python.exe -m scripts.validate_uncertainty_sweep
.venv/Scripts/python.exe -m scripts.multitask_uncertainty_report
.venv/Scripts/python.exe -m pytest tests/test_game_clean_coverage.py tests/test_game_runtime.py tests/test_game_offline.py tests/test_reputation_manager.py tests/test_game_completion.py -q
git diff --check
```
