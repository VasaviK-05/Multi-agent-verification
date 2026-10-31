# Task-conditioned offline policy study

This opt-in 2026-10-31 workflow separates subject domain, verification task and
the data establishing reliability. Legacy production analysis/reputation and all
previous artifacts/approvals remain unchanged. There is no DB/API integration.

## Owned contracts

`TaskQuestionAnalyzer` wraps the existing heuristic analyzer without changing its
default behavior. The explicit, question-only `explicit_task_questions_v1` rules
recognize a paraphrase instruction as `semantic_comparison`, and currency/area
questions as `direct_fact`. Existing arithmetic/population rules are reused.
Unknown requirements remain unknown. This identifies the required check, not
answerability or verifier reliability. Subject domain remains `general/unknown`
for all three prepared cohorts; it is never renamed to manufacture expertise.

`domain_requirements_task_v1` derives task identity from subject domain/status,
validated requirements and question-rule version, without labels or answers.
`task_isolated_history_v1` binds each snapshot to its own history partition digest
and dataset. The old manager/decision interface still stores subject-domain
statistics inside a snapshot; the effective opt-in key is the enclosing task ID
plus verifier. Each task gets a fresh Beta(1,1) manager. No global general-domain
manager, capital-fact history or cross-task pooled prior is used. Sparse history
retains the isolated prior and is reported with counts/variance; zero observations
do not become informative contributors.

Task-aware execution uses `offline_public_decision_v4` /
`task_output_contract_v2`, retaining `informative_history_influence_v1`, threshold
0.55 and all contributor, prerequisite, factual coverage and failure protections.
Its artifact/episode requires the task binding. Legacy v1/v2/v3 keep their old
coverage semantics. Optional context fields are omitted when absent so legacy
serialized identities remain stable.

The new coverage interpretation recognizes a completed directional reference-
similarity comparison only for an explicit semantic-comparison requirement with a
reference and full existing Semantic metadata (method, compared text, model,
raw similarity and score meaning). It never grants factual coverage. It is a
measurement witness, not a guarantee that two statements are equivalent or true.
Independent equivalence labels measure its usefulness. Zero confidence/abstention,
missing reference or bare checker identity/decision cannot supply coverage.
The collector's existing achieved-capability audit remains its factual-v1 audit;
the full retained reports allow the explicitly versioned v2 finalizer to interpret
semantic comparison later. Reports are not rewritten to add certificates.

General `consistency` remains unsupported by achieved-coverage interpretation:
Confidence's majority/agreement trace does not establish logical consistency or
factual truth of arbitrary text. A scoped consistency task needs its own precise
validation question and independent labels. No generic certificate was invented.

`TaskPolicyRouter` selects only explicit task/signature/budget episodes and has no
cross-task fallback. The offline runtime harness additionally scopes requests to
prepared question identities from training plus outcome-free reservation metadata
(`prepared_question_task_routes_v1`). This is a narrow pilot scope, not an open-
domain capability claim. Unknown requirements, absent/infeasible routes, changed
budgets and out-of-study questions fail safely before dispatch. Existing runtime
resource checks remain mandatory. Routing consumes no correctness labels.

## Frozen preparation

The study directory is ignored/local: `build/multitask-policy42/`.
There are sixty groups per cohort, twenty each in history/development/reservation,
seed 42; both candidates stay in their group. Each cohort has eighty collection
candidates and 320 planned attempts: **240 candidates / 960 attempts total**.
All four actual eligible adapters execute once per candidate, with existing public
capability descriptors. No verifier is duplicated or made eligible by fiat.

- Arithmetic: distinct three-digit integer-addition questions; exact integer
  labels, correct number versus off-by-one. This is addition, not evidence of
  reliability on every arithmetic operator. Canonical numeric references are
  explicitly trusted; their formatting is not tailored to a verifier's outcome.
- Semantic: sixty independent named predicate frames. Correct answers preserve
  predicate/arguments via active/passive voice; wrong answers change action,
  object and destination. These are constructed equivalence labels, not naturally
  occurring errors or real-world truth labels. The task question includes the
  reference it asks to paraphrase, and the same unaltered reference is supplied as
  context. Existing default `question_answer` Semantic mode is retained, not tuned
  after results. Its limits must be reported rather than patched in verifier code.
- Factual: source-snapshot population, currency and area values for sixty countries
  outside the prior capital-study selection. GeoNames countryInfo and pinned
  mledoze countries source files/usage terms are reused with exact file hashes.
  Currency codes agree across both sources; area/population are the explicitly
  declared source-snapshot values, not claims of current census precision.
  Incorrect values are predetermined structured changes. The first group of each
  split is omitted from retrieval corpus, retaining its independent labels and
  reference; missing-evidence observations are preserved. The binary correctness
  schema is not relabelled to fabricate an answerability ground truth.

The isolated corpus has 57 public source-fact documents. Its index-v2 receipt was
built using the observed installed embedding weights through the existing public
utility. It contains reference facts, not final candidate labels/reports. Source
files were already inspected during prior work: reservations are procedural and
do not establish blinded/unseen source knowledge. Prior capital ISO groups are
excluded; question-ID overlap with prior arithmetic/capital records and reserved
metadata is zero. Exact grouping/source/preparation digests and exclusions are in
`study-audit.json` and `preparation-freeze.json`. No final payload is read after
preparation and no final verification is collected.

Two rejected preparation attempts remain preserved separately. The first stopped
on an actor-list count check. The second was superseded to remove a potential
six-significant-digit area-formatting risk. Exact numeric representation and its
regression test were fixed before inference; no selection used verifier outcomes.

## Collection, recovery and cost boundaries

Existing collection CLI, real project factory and resource observer are reused.
Verifiers run sequentially per worker; independent cohorts overlap on the same
local CPU/Ollama service. `campaign-execution.json` declares that schedule.
Each cohort's costs are calibrated separately from its actual measurements;
shared-machine contention is included, not described as isolated latency. All
first/subsequent calls and failures are retained; initialization, pre/post resource
hashing and checkpoint overhead are outside `verify` timers. Units are summed
verifier-attempt wall milliseconds, not money/CPU time/guaranteed request latency.

Every call gets a flushed/fsynced start ledger plus the existing completed journal.
Recovery uses a new output directory and the exact same request/setup. Completed
returns, abstentions and failures are copied without re-execution. Only missing,
never-executed work can resume. An in-flight start with no completion is ambiguous
and blocks retry; unknown historic ledgers or changed resources/setup are rejected.
Original journals and incomplete observations are preserved. No silent recovery
can manufacture a timing/report for an interrupted call.

```powershell
.venv/Scripts/python.exe -m scripts.multitask_policy42 prepare --adapter-config PATH_TO_REVIEWED_ADAPTER.json
.venv/Scripts/python.exe -m app.benchmark.project_adapter prepare-index build/multitask-policy42/adapter.json --output build/multitask-policy42/index-receipt.json
.venv/Scripts/python.exe -m scripts.multitask_policy42 collect --cohort arithmetic
.venv/Scripts/python.exe -m scripts.multitask_policy42 collect --cohort semantic
.venv/Scripts/python.exe -m scripts.multitask_policy42 collect --cohort factual
```

The preparation command reflects the current explicit configuration interface;
the historical run copied its earlier campaign's reviewed adapter. That implicit
configuration dependency has been removed; see
[preparation configuration](preparation_configuration.md). Other historical data
inputs remain external and no campaign outputs have been regenerated.
These exclusive producer commands document the workflow; do not rerun them over
existing output directories. Supported recovery, only after inspecting ledgers:

```powershell
.venv/Scripts/python.exe -m app.game.offline.collect collect PATH_TO_ORIGINAL_REQUEST.json --resume-from PATH_TO_PRIOR_COLLECTION --output-dir PATH_TO_FRESH_COLLECTION
```

## Fits and descriptive budget sensitivity

The pipeline calls existing calibration/application, strategy enumeration, public
replay, reliability-first solver, artifact export/reload and certificate validators.
No parallel policy builder/optimizer is introduced. Each cohort's history is frozen
alone. Both aggregation methods and every feasible team remain represented.

Primary B is the sum of all eligible-roster measured means. Each distinct feasible
team-cost breakpoint is an explicitly descriptive sensitivity budget, with losses,
coverage 0.90, priors, threshold, dependency registry and epsilon fixed. The old
resource diagnostic coefficient remains 0.1/full-roster-B across sensitivities.
Cost is secondary after Stage A's validation-loss minimax, within 1e-8 loss.
The old cost-inclusive unconstrained objective is exported only as a labelled
within-cohort comparison. Historical original policies stay preserved and are not
misapplied to a different task's data.

Only the budget may differ when reusing finalized sensitivity cells: the owned
cache validates exact decision settings, source records/labels, execution contracts,
costs and strategy definitions. The coverage producer independently replays clean
source records before deriving Q/exporting a constrained policy. Infeasible 90%
budgets produce diagnostic maximum coverage and complete strategy reports, without
relaxation or a constrained artifact. No favorable budget is selected as a paper
result. Known shared embedding/NLI pathways and conservative shared-unknown
components are retained; contributor count is not independent-group count.

After all 960 calls finished, validation was tightened without changing reports or
valid decisions: v4 fitting requires its task binding before payoff construction,
task-history dataset identity must match provenance, task-isolated pooling rejects
explicitly, and reference checks share the analyzer's case/whitespace recognition.
The v4 public finalizer checks the complete bound execution contract. Legacy
v1/v2/v3 diagnostic replay retains its previous behavior, including explicit
failure-contract comparisons; its contributor binding check is unchanged.
The application-source digests for collection, resource validation and fitting are
recorded separately. These boundary changes do not invalidate recorded verifier
outputs or silently rebind their measured setup.

The existing seven fixed evidence software fixtures (four controlled and three
installed-NLI cases, using a controlled retriever) were validated against actual
stable resources. They are separate from the 240 study candidates / 960 collection
attempts, issue no LLM generations, and never enter reputation or calibration.
They validate software output semantics, not retrieval quality or held-out
accuracy. All cohort/budget fits require the existing research readiness checks;
no gate is bypassed. The receipts and readiness reports are retained locally.

Post-collection commands (pure fitting may resume only by verifying existing
outputs agree; differing outputs are preserved and cause failure):

```powershell
.venv/Scripts/python.exe -m scripts.multitask_policy42 validate-resources
.venv/Scripts/python.exe -m scripts.multitask_policy42 fit --cohort arithmetic
.venv/Scripts/python.exe -m scripts.multitask_policy42 fit --cohort semantic
.venv/Scripts/python.exe -m scripts.multitask_policy42 fit --cohort factual
.venv/Scripts/python.exe -m scripts.multitask_policy42 runtime
.venv/Scripts/python.exe -m scripts.multitask_policy42 report
```

The resource-validation phase checks exact completed journal/export equality,
unique start ledgers, frozen preparation hashes and linked measurement exports.
No final outcome path is an input. Payoffs are independently reconstructed twice,
then matrices/probabilities are compared with absolute tolerance 1e-12 and zero
relative tolerance; detached reputation records agree exactly. Code revision,
dirty application/producer digests, setup/configuration IDs, package/solver
versions and seeds are recorded apart from scientific outputs.

The campaign is complete; [results and owner handoff](multitask_policy_results.md)
record the actual outcomes. All three 90%-coverage primary problems are infeasible
(maximum clean coverage arithmetic 82.5%, semantic 0%, factual 37.5%). Only labelled
unconstrained diagnostic artifacts were produced, exported/reloaded and runtime-
validated. No primary policy or held-out superiority result is claimed. Detailed
local metrics, decisions and validation provenance remain under the study directory.
