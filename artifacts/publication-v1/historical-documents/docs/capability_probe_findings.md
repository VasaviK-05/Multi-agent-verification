# Capability probes and owned handoff

Worktree: `<LOCAL_USER_HOME>/Multi-agent-verification/build/flexible-verifier-teams`;
branch `codex/flexible-verifier-teams`, base `0b3595e`. Existing work is preserved.
No applicable AGENTS.md was found in the repository or checked ancestors.

## What previous pairs established

Baseline selection used `DEFAULT_DIFFICULTY_RANGE` (easy 2–2, medium 2–3,
hard 3–4), then expected-coverage selection and ranking to fill the target.
The execution layer also retained a minimum-two floor for easy/medium.
See `app/selection/verifier_selector.py:79`, `:378`, `:391` and
`app/orchestration/validation_orchestrator.py:219`.

Those are historical count heuristics, not evidence that the system identified
separate answer components. Game mode instead enumerates feasible teams, chooses
one compatible fitted policy, samples its stored probabilities and executes the
complete selected team. Its loop still passes the whole question, answer and
context to each verifier (`app/game/execution.py:165`, `:172`).

Evidence does perform internal factual claim extraction and per-claim NLI
(`app/verifiers/evidence_verifier.py:2113`). It must not be described as incapable
of all compound text. But there is no shared component plan that extracts an
arithmetic subquestion/answer for Rule or binds coverage to all required fields.
Rule's binary arithmetic patterns fullmatch the whole question and parse the
whole answer as a number (`app/verifiers/rule_verifier.py:212`). Evidence's external
`context` argument is not used as a replacement retrieval corpus in this method;
synthetic references were not inserted into that corpus. Semantic explicitly
measures cosine resemblance, not logical equivalence (`semantic_verifier.py:1`).

## Fixed probe set and execution

The catalog was fixed and hashed before inference: 12 groups / 24 answer
examples / 96 existing-verifier attempts / 120 local generation requests.
Every group has one independently labelled correct and one deliberately incorrect
answer. Questions, references, labels, rationale, support status and legacy/owned
analysis are in `artifacts/capability-probes-v1/groups.json`.

Groups:

- Arithmetic: 37×19 (703 versus 693); word-form 25−17 (8 versus 42);
  17/4 (4.25 versus 4.2, which is wrong under the existing rounding policy).
- Factual: Bahrain area (765 versus 766); Belgium population
  (11941781 versus 11941718); Cuba currency (Cuban versus Mexican peso).
- Reference comparison: count change, negation, reversed lender/borrower roles,
  and reversed left/right relationship. Labels are independently reasoned
  equivalence labels, not cosine-similarity labels.
- Compound diagnostics: Bahrain area then +10, including a wrong calculation;
  Belgium population then +1000, including a wrong base fact with internally
  consistent arithmetic on that wrong base.

Factual references come from retained history-source facts and pinned structured
sources, not completed held-out outcomes. These are known-source diagnostics,
not unseen accuracy evidence. Related factual/compound groups share entities and
are not independent benchmark clusters. Longer wording is not labelled harder.
All four verifiers were eligible by prerequisites because each reference was
real fixed text and all observed local resources matched. Eligibility does not
promise relevant achieved coverage.

No context was rewritten, no examples replaced and no unsuccessful report
retried. Started/completed journals, report identities, timing links and resource
observations are retained in `collection/`. No models were downloaded, no index
rebuilt, and no corpus expanded. The original resource-compatible checkout
supplies unchanged verifier implementations; the feature worktree supplies the
owned analyzer and descriptive evaluation. No teammate algorithm was edited.

## Observed team results

Every eligible singleton, pair, triple and quad was evaluated with both existing
aggregations and the explicit minimum-one informative contract: 320 team/example
rows for 20 atomic examples. Four compound examples have no executable strategy.
These are descriptions of the recorded roster under frozen task-family history,
not fitted policies or certified training payoffs. History is unchanged and may
not calibrate the new operations, wordings or logical contrasts.

- Arithmetic: Rule alone correctly decides 6/6; all eligible supersets also 6/6.
  Decision loss 0. Additional names provide no observed decision improvement.
- Factual: Evidence alone correctly decides 6/6; all eligible supersets also 6/6.
  Decision loss 0. These facts were drawn from history inputs, so this is a
  mechanism probe, not an independent generalization claim.
- Reference comparisons: Semantic alone decides 0/8 under the informative guard;
  all eight remain uncertain, loss 0.2. Semantic+Confidence accepts all four
  correct answers, rejects the two incorrect role/spatial answers, and remains
  uncertain on the incorrect count/negation answers. Coverage 6/8=75%, false
  accepts 0, false rejects 0, selective risk 0/6, decision loss 0.05. Both
  aggregations agree on these public outcomes.
- Adding Rule or Evidence to that reference pair changes no verdict: they
  abstained on these synthetic reference frames. No triple/quad advantage was
  observed. No addition increased clean decision loss on this fixed set, but
  most additions did nothing while increasing estimated cost.

The 48 improving addition comparisons are only six distinct reference examples
repeated across two aggregations and four parent-team variants. They are not
48 independent successes. The other 432 comparisons have unchanged clean loss.
All are post-hoc diagnostics unavailable as a pre-dispatch oracle; no per-example
best-team policy or probability distribution was constructed.

### Why the reference pair helps, and what that does not prove

For the reversed role answer, Semantic reports SUPPORT with cosine 0.92749,
while Confidence reports REJECT with score 1. For reversed spatial direction,
Semantic reports SUPPORT with cosine 0.92872 while Confidence reports REJECT
with score 1. The pair correctly rejects both; Semantic alone remains uncertain.
It also resolves four correct paraphrases.

Crucially, Semantic's frozen task-family reputation is 0.5. It supplies completed
comparison-measurement coverage but **zero informative vote**. Confidence supplies
the one informative vote. Confidence alone lacks the required semantic-comparison
capability. This demonstrates complementary roles under the existing contract,
not two independent reliable confirmations or a new safe entailment verifier.
High cosine on changed number/negation/roles remains a known limitation, not a
violation of the stated resemblance-measurement contract. Both incorrect numeric
and negation cases remain unresolved. No team reaches 90% reference coverage on
these probes; the target was not lowered and no policy was fitted.

Individual states, scores, historical reputation/weights, informative status,
claim decisions, achieved checks and measured call durations are retained in
`individual-findings.json`. A high raw score on an UNSURE report never counts as
an informative vote. All detailed team reasons and costs are in
`team-outcomes.json` and `team-metrics.json`.

### Costs

Measured mean individual call times across all 24 examples are approximately
47.664 ms Semantic, 138.560 ms Evidence, 0.602 ms Rule and 15222.821 ms Confidence.
These include abstentions and exclude factory initialization and resource-observer
overhead. Historical reference-pair cost is 15820.463 ms; it is an estimate reused
unchanged, not measured singleton/pair deployment latency. Per-call data and p95
summaries are in `timings-summary.json`. No costs or budgets were refitted.

## Compound results: an actual interface/integration gap

Both whole compound questions caused Rule to return unsupported/UNSURE on both
answer variants. No report achieved arithmetic coverage. Merely containing Rule
and Evidence therefore does not make any pair/triple/quad a complete checker.

Evidence did split the Bahrain answer into two claims: it supported the base
765-area fact, but marked both the correct derived 775 statement and the incorrect
774 statement REJECT. The whole correct answer was therefore reported REJECT at
the raw verifier level. Its report did not qualify as complete direct-fact
coverage in the owned output guard. This is not a claimed qualified public verdict.

For Belgium's correct compound answer, Evidence supported the base fact and left
the derived calculation UNSURE (`partial_support`). On the incorrect answer it
correctly rejected the wrong base population, but still did not certify the
calculation. Confidence supported both population variants, including the wrong
one. Semantic supported all four compound variants. These negative findings were
retained; no result was rescued by changing references.

Thus the gap is not merely an absent evaluation or an inability to select pairs.
It includes whole-input formatting for Rule, missing component binding, and
unsupported arithmetic-as-factual-NLI semantics. Existing atomic Rule capability
could be reused through a future explicit component adapter; a general new
calculator algorithm is not automatically necessary. No such adapter or
component-qualified policy is claimed here.

## Implemented owned fixes

New opt-in module: `app/analysis/capability_probe_analyzer.py`.

1. Recognize the bounded word-difference template supported by Rule but missed
   by the old analyzer. The probe confirms Rule returns SUPPORT for 8 and REJECT
   for 42. The new question-rule version is `capability_probe_questions_v1`.
2. For the two explicitly recognized fact-plus-calculation templates, preserve
   arithmetic and factual requirements and add the unsupported
   `compound_component_binding_v1` obligation. Enumeration and routing fail
   closed rather than silently treating the request as only a fact.

This module does not choose team names or sizes, use answer correctness, change
thresholds or expand execution sequentially. Existing atomic analysis delegates
unchanged, and the default analyzer/API routes/allowlist remain untouched.
Other compound forms are not claimed recognized by this bounded opt-in grammar.
New recognition/versioning does not supply a fitted compatible policy.

Tests: 139 passed across analyzer, routing, selector and flexible-team suites.
They cover existing-analysis identity, parser-supported new wording, preserved
mixed requirements, failure to dispatch unsupported mixed questions, capability
union not bypassing a missing component contract, and ordinary sums containing
“and” not being misclassified as compound.

## Precise component/owner handoff

Proposed future protocol, **not executed or activated in this task**:

- Owned input/selection adapter: produce a question-derived check plan with stable
  component IDs and deterministic answer-field binding. For Bahrain, fields
  `area=765` and `area_plus_10=775` need separate coverage, not a single opaque vote.
- Evidence/retrieval owner: confirm fact-component question/claim handling and
  return coverage/evidence references scoped to that component. Do not treat a
  derived mathematical statement as an ordinary contradictory source fact.
- Rule/input-adapter owner: pass a legitimate standalone numeric input such as
  `What is 765 + 10?` with answer `775`, bound to the supplied base field. Existing
  Rule can parse that grammar; this extracted-call protocol was not tested here.
- Owned decision/execution owner: version component-aware completion and verdict
  rules. An unchecked field cannot be covered by an unrelated vote or agent name;
  a confirmed wrong required component must not be outvoted by correct unrelated
  components. Retain report identities, prerequisites, resource and contributor
  guards, and complete-team execution.
- If direct logical entailment against supplied reference text is desired, the
  verifier owner must define a separate trusted-reference input/coverage contract.
  Do not silently change Evidence's corpus semantics or relabel Semantic cosine
  resemblance as an entailment certificate.

Acceptance examples: correct 765/775 may be accepted only after both checks and
configured conditions pass; 765/774 must not be accepted (bad calculation);
766/776 must not be accepted (wrong base fact despite internally correct sum).
Missing/ambiguous fields, unsupported operations or missing component evidence
must prevent acceptance. New component contracts must be incompatible with the
old atomic policies; original artifacts must reload with unchanged identities.

## Smallest next study, not launched

For a feasibility fit, use two independently specified families: supported
standalone arithmetic as a control and reference-equivalence contrasts where a
pair showed diagnostic value. Use 30 fresh groups per family, split 10/10/10 into
history/development/test, with two independent answer labels per group: at most
120 examples, 480 four-verifier attempts and 600 local generation requests at n5.
This is a small exploratory study, not a deployment-grade power claim.

Define categories from question/reference structure (number preservation,
negation, relationship roles), never whether the supplied answer changed them.
Keep all related frames/entities/answer variants in one split. Derive reputations
only from fresh history, fit only on fresh development, freeze before new test.
Use the unchanged primary dependencies, thresholds, penalties, 90% development
coverage target and comparable budgets; never relax them to make a pair feasible.
Include best fixed team, existing greedy and question-conditioned policies under
matching contracts, with grouped uncertainty and cost accounting. Report equality
to a fixed team honestly. If coverage is infeasible or conditional routing adds no
value, retain that finding rather than forcing diversity.

Do not use completed held-out outcomes or these explored probe results as a fresh
untouched test set. Mixed-policy fitting stays gated on the component acceptance
criteria above. No three-verifier requirement or advantage is demonstrated here.

All frozen policies, reputation snapshots, historical bundles and held-out
results remain unchanged. No model download, index/corpus expansion, DB/frontend/
API/verifier-algorithm change, commit, push, merge or activation occurred.


## Reproduce the analysis without new inference

From the feature worktree, using the retained recording bundle:

```powershell
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m scripts.evaluate_capability_probes --source <LOCAL_USER_HOME>/Multi-agent-verification/build/multitask-policy42
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m pytest tests/test_capability_probe_analyzer.py tests/test_flexible_teams.py tests/test_game_task_conditioning.py tests/test_verifier_selector.py -q
```

These commands replay recorded reports and run synthetic software fixtures; they
do not launch fresh model inference or a new diagnostic collection. The preparation
and collection scripts are retained for audit and separately authorized future
runs; do not rerun this completed collection as a retry. The six new source files
and every generated artifact are listed with hashes in
`artifacts/capability-probes-v1/file-manifest.json`. `verification.json` records
exact attempt/generation counts, context equality within each answer pair,
unchanged old artifact hashes and test results.
