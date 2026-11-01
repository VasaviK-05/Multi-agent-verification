# Evaluate a frozen policy against altered evidence

For explicitly new collectors when the historical source cannot be recovered,
use the separate [frozen-policy transfer contract](upstream_transfer_evaluation.md).
It requires fresh clean **and** altered reports and explicitly makes no collector
equivalence claim. The strict workflow on this page remains unchanged in meaning.

This is **evaluation only**, separate from the upstream minimax fitter. It accepts
the original `PolicyArtifact`, including existing clean-coverage-constrained and
reliability-first artifacts. It validates their original objective/version bindings
and numerical certificates; it never calls a fitter, optimizer or sampler. It
does not change policy bytes, IDs, probabilities, reputation, thresholds, costs,
minimum contributors, achieved coverage or failure protections.

The original certificate applies **only to the original fitted problem**. New
scenario losses are measured outcomes under frozen probabilities, not a new game
optimum, poisoning-aware policy or guarantee of robustness. The original clean
development coverage floor is recorded for context; it is **not** imposed on
altered-scenario coverage. Per-example guards remain fully active.

## Supported interfaces

`app.game.offline.upstream_evaluation` provides:

- `FrozenUpstreamEvaluationInput(artifact, clean, report_attacks, scenarios)`:
  `artifact` is the original validated `PolicyArtifact`; `clean` is the complete
  original `RecordingBundle` containing history/development plus reservation
  metadata; `report_attacks` is its original `AttackSpecification`; each scenario
  is the existing `ScenarioRecording(intervention, bundle, evidence_validation)`.
- `evaluate_frozen_upstream(inputs) -> FrozenUpstreamEvaluation`: exact enumeration
  of **every** original strategy, including zero-probability strategies, with
  expected metrics weighted by the unchanged probabilities. There is no draw,
  probability floor, renormalization, pruning or new payoff matrix/certificate.

The clean bundle is re-exported to a detached training manifest solely to verify
its **exact original training binding**, history-only statistics, grouping,
references, example identities and final-test reservation. No new reputation is
learned from development. This proves membership in the original development set;
standalone artifacts cannot silently authorize unseen questions. The package CLI
additionally enforces the original prototype's allowed question hashes and task.
Historical arithmetic and factual collection bundles were checked read-only and
both reproduce their original packaged artifact training bindings.

The evaluator uses the existing public replay and shared runtime finalization.
Its temporary replay context carries the appropriate altered resource manifest
and execution configuration, but has **no evaluated offline binding**. It cannot
construct a `DeploymentEpisode`. Only policy-level optimization obligations are
omitted in this temporary view; all per-example decision semantics and frozen
planning/statistical inputs remain. The returned object is an evaluation report,
not a `PolicyArtifact`; there is no altered-resource deployment export interface.
Production resource checks are unchanged: altered bytes observed under the
original deployment episode still cause `provenance_incompatible` uncertainty
before dispatch; detected post-dispatch drift also forces uncertainty.

The ordinary upstream fitter remains unpooled minimax only. Its existing rejection
of clean-coverage, reliability-first and pooled fitting objectives is unchanged.
Evaluation supports the first two existing variants, but **pooled multi-context
policies remain unsupported** without a separate evaluation contract.

## Required inputs and custody

Reuse the declaration, isolated resource preparation and collector in
[upstream evidence experiments](upstream_evidence_experiments.md). There is no new
collection framework and no clean-report substitution, even for unaffected
verifiers. Every scenario must contain fresh full-roster development recordings
with distinct execution IDs, complete pre/post resource observations, actual
reports, declared failures, timing records and prerequisites. Missing, duplicate,
cross-split, relabelled, changed-reference, incompatible-resource or incomplete
records reject. Existing scenario-specific team-independent reuse attestations,
explicit affected/shared resources and configuration checks also apply.

For empirical Evidence-bearing scenarios, retain the existing resource-bound
`EvidenceValidation` proof for the altered setup; a clean-resource proof cannot
stand in for it. These are software-contract/readiness probes, not proof of
independent corroboration or evidence truth. No new clean fitting specification is
required for frozen evaluation: the original artifact and exact training binding
are verified, rather than running a fresh fitting-readiness workflow.

The attacker commits its fixed alteration before collection/team sampling and
does not receive independent correctness labels, final-test outcomes or the
sampled team. The evaluator sees independent development labels to score the
frozen policy; that is not permission to provide them to the attacker producer.
All final-test records remain inaccessible; only reservation metadata is accepted.

**Verified collection limitation:** clean and altered recordings must have the
same recorded code revision, application-source digest, dependencies, environment,
factory and randomness controls, as required by the upstream contract. Only
declared resource/configuration-path differences are allowed. For historical
prototypes, the collection owner must reproduce the original collection code and
environment for the new altered runs, using the existing collector at that frozen
revision. Running the current checkout and changing old setup fingerprints is
forbidden. A reviewed cross-revision bridge is not implemented here. Actual
algorithm/model changes also fail the intervention resource checks. Artifact
certificate validation is not a substitute for these compatibility conditions.

### Actual compatibility audit and current readiness

Both original bundles record Git SHA
`17b695373f935dc1f5fd09c37cf8917969367f7a` and application digest
`47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`.
The tracked application tree at that Git SHA **does not match** the recorded
digest (neither LF blob bytes nor normal CRLF checkout bytes). The inspected saved
source exports also did not match. The recorded working tree included code beyond
that commit; the SHA alone is not a recoverable source snapshot. In particular,
that commit does not contain `scripts/factual_policy42.py` or the newer proof schema.

**The real experiment is currently blocked by the missing exact collection-source
snapshot.** A plain checkout of that SHA is not ready, and current evaluator code
must not be copied into the collector's `app/` tree to work around it. Matching
model resources alone cannot satisfy this source check. The following is a
supported workflow **conditional on recovering and verifying that snapshot**;
it is not a claim that the available inputs can run a real campaign today.

The existing adapter records these distinct identities:

- `MeasurementSetup.code_revision`: actual `git rev-parse HEAD` at the adapter root.
- `application_source_digest`: `content_id` of the sorted relative `app/**/*.py`
  paths and SHA-256 of their actual bytes, including dirty/untracked source files
  and line endings. Scripts/tests outside `app/` are not part of this digest.
- `dependency_versions`: installed package versions and Python, including the
  recorded optional SentencePiece state. `environment` includes platform,
  architecture, hashed host identity, processor/CPU/memory, runtime, thread settings,
  device and initialization/concurrency declarations.
- `resources.manifest_id`: per-verifier implementation, configuration, model,
  corpus, index, prompt and service fingerprints; `execution_configuration_id`
  equals this ID. Corpus/index paths affect all project configuration entries.
- `MeasurementSetup.fingerprint`: digest of the whole setup, bound to request and
  individual timing records. Resource observations occur before/after calls.

`validate_scenario_links` compares clean/altered recorded code revision, application
digest, dependencies, environment, evidence kind, factory and randomness exactly.
`ScenarioRecording` separately verifies the altered request, complete records and
observations; `EvidenceIntervention` permits only declared isolated resource/path
changes. The **evaluator checkout's own** Git revision/source/environment are not
compared to those recordings. Therefore original-source collection and newer
evaluation are supported without rebinding any old recording or changing a guard.

If the snapshot cannot be recovered, stop. The smallest separately reviewed
alternative is an explicit versioned source-transition contract, not deleting
these equality checks: retain both actual setups, require an audited old/new source
manifest identifying collector/verifier execution components, unchanged protected
implementation/model semantics, and resource-bound contract probes, and bind that
transition into evaluation provenance. A global hash alone cannot establish which
old components were unchanged. Such a bridge is **not implemented or approved**
here; it must not be inferred from passing synthetic tests or edited provenance.

The dataset/resource owner supplies the matching original bundle, exact scenario
scope, independent labels, isolated corpus/index receipts, installed model/service
resources, live observations and reuse attestations. The study owner approves
altered text, attacker knowledge/timing and bounded collection before outcomes are
examined. No real run or new scientific setting is approved by this implementation.

## Later real collection and evaluation commands

Do not rerun clean collection, recalibration or fitting. Retain the supplied ZIP
and original artifact bytes. Extract a copy using the documented package layout.
The local original bundles are:

```text
build/multitask-policy42/arithmetic/collection/recordings.json
build/multitask-policy42/factual/collection/recordings.json
```

### Two-root procedure and hard stop before real work

The commands in this subsection are a future owner handoff. Only the source audit
was exercised on real local metadata in this change; **no** model probes, index
build or collection command below was run. Start in the new evaluator checkout:

```powershell
$EvalRoot = (Get-Location).Path
$CollectorRoot = 'PATH_TO_NEW_RESTORED_COLLECTION_WORKTREE'
$OriginalPython = 'PATH_TO_MATCHING_ORIGINAL_ENVIRONMENT/python.exe'
$CleanBundle = Join-Path $EvalRoot 'build/multitask-policy42/arithmetic/collection/recordings.json'
# Source/recovery owner, only in a fresh worktree; do not alter the active checkout:
git -C $EvalRoot worktree add --detach $CollectorRoot 17b695373f935dc1f5fd09c37cf8917969367f7a
# STOP: restore the authentic archived app/ working-tree bytes, including previously
# untracked files and original line endings. This archive has NOT been found.
# Do not infer it by editing files until a digest happens to match.
$RunRoot = Join-Path $CollectorRoot 'build/FROZEN_EVAL_NEW'
New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment audit-collector --clean-bundle $CleanBundle --collector-root $CollectorRoot --output "$RunRoot/source-audit.json"
if ($LASTEXITCODE -ne 0) { throw 'Collection source is incompatible; no model initialization is authorized' }
```

`audit-collector` compares the real worktree root, HEAD and actual application-file
bytes without importing the candidate app, constructing a verifier, reading model
weights or making a network request. It emits a private per-file source manifest,
required dependency/environment values and explicit gaps. Even a passing source
audit says `ready_for_real_collection=false`: resources and authorization remain
to be checked. The current checkout audit correctly fails both revision and source
digest checks. Do not commit these machine-specific audit files.

The resource owner must then preserve original **canonical paths**, not just file
bytes. The original corpus/index/receipt/service paths are relative configuration
strings, while the clean index manifest binds the resolved absolute corpus path,
size and mtime. Copying that index into a different root and editing its manifest
would change its identity and is not supported. One supported same-host mapping is
to expose only the original clean corpus file and index directory through narrow
read-only links, with metadata receipts copied byte-for-byte. For this campaign:

```powershell
$Mirror = Join-Path $CollectorRoot 'build/multitask-policy42'
$OriginalStudy = Join-Path $EvalRoot 'build/multitask-policy42'
New-Item -ItemType Directory -Path $Mirror -ErrorAction Stop
# Resource owner supplies link privileges and read-only access; never link custody/.
New-Item -ItemType SymbolicLink -Path "$Mirror/corpus.json" -Target "$OriginalStudy/corpus.json" -ErrorAction Stop
New-Item -ItemType Junction -Path "$Mirror/index-v2" -Target "$OriginalStudy/index-v2" -ErrorAction Stop
foreach ($name in @('index-receipt.json','service-observation.json')) {
    if (Test-Path "$Mirror/$name") { throw 'Refusing to overwrite a resource receipt' }
    Copy-Item -LiteralPath "$OriginalStudy/$name" -Destination "$Mirror/$name" -ErrorAction Stop
}
```

Do not expose final-test custody directories. Keep the original adapter JSON
unchanged; its model snapshot paths are already absolute. If canonical-path
resolution or the original environment cannot be reproduced, the next preflight
must fail. Do not patch fingerprints, corpus mtimes, receipt contents or the clean
index manifest to make it pass. File-link privileges/resources are producer inputs,
not a reason to weaken compatibility.

Create altered resources with the new preparer, **outside** the frozen app tree:

```powershell
$CleanAdapter = Join-Path $OriginalStudy 'adapter.json'
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment prepare --clean-adapter $CleanAdapter --alterations REVIEWED_ALTERATIONS.json --output-dir "$RunRoot/altered"
Set-Location $CollectorRoot
& $OriginalPython -m app.benchmark.project_adapter prepare-index "$RunRoot/altered/adapter.json" --output "$RunRoot/altered/index-receipt.json"
& $OriginalPython -m app.benchmark.project_adapter observe-service "$RunRoot/altered/adapter.json" --output "$RunRoot/altered/service-observation.json"
```

The resource owner runs the **old** `inspect_setup` for both configurations and
persists `CLEAN_PREFLIGHT.json` / `ALTERED_PREFLIGHT.json` with their `observed_setup`.
It hashes installed files and saved service metadata without inference. Require
the clean setup to equal the original bundle setup in full. Require the altered
code revision, app digest, environment, dependencies and evidence kind to equal
the original, while resource differences must validate as `EvidenceIntervention`.
The factory later requires its observed setup to equal the request's expected setup.
For example, execute this with the original Python in the collector worktree
(the environment variables here identify input/output files, not scientific settings):

```powershell
$env:FROZEN_CLEAN_BUNDLE=$CleanBundle
$env:FROZEN_CLEAN_ADAPTER=$CleanAdapter
$env:FROZEN_ALTERED_ADAPTER="$RunRoot/altered/adapter.json"
$env:FROZEN_PREFLIGHT_DIR=$RunRoot
@'
import json, os
from pathlib import Path
from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup
expected=json.loads(Path(os.environ['FROZEN_CLEAN_BUNDLE']).read_text())['observed_setup']
for name,key in [('clean','FROZEN_CLEAN_ADAPTER'),('altered','FROZEN_ALTERED_ADAPTER')]:
    report=inspect_setup(AdapterConfiguration.model_validate(json.loads(Path(os.environ[key]).read_text())))
    assert report['ready'], report['blockers']
    actual=report['observed_setup']
    assert all(actual[k]==expected[k] for k in ('code_revision','application_source_digest','environment','dependency_versions','evidence_kind'))
    if name=='clean': assert actual==expected, 'clean resource identities changed'
    with (Path(os.environ['FROZEN_PREFLIGHT_DIR'])/(name+'-preflight.json')).open('x') as f: json.dump(report,f,indent=2)
'@ | & $OriginalPython -
if ($LASTEXITCODE -ne 0) { throw 'Incompatible original environment/resources' }
```

Now the existing `scenario_request`/`EvidenceIntervention` example in the upstream
guide runs in the **new evaluator checkout**, using those actual preflights and the
original request. It writes `ALTERED_REQUEST.json` and `DECLARATION.json` outside
`app/`, with predeclared replacements, original independent labels, fresh run IDs,
the entire roster and new authorization. Preserve original factory/randomness;
never copy or flip clean reports. Store the declaration before any verifier calls.

### Producing the required Evidence proof without changing frozen app source

The old campaign-wide `validate-resources` phase is **not** the right command: it
requires three complete original 320-attempt cohorts. `scripts/frozen_evidence_probes.py`
is instead an external, bounded adapter around the existing project factory and
the same seven fixed Evidence software cases. It stays in the evaluator checkout
and imports the restored collector's `app` first. It rechecks actual source/setup,
blocks all generation and nonlocal endpoints, caps metadata at 30 requests, and
executes four controlled cases plus three installed-NLI cases. It never reads study
candidates or runs the collector. It emits plain proof JSON, so the historical app
does **not** need the newer `EvidenceValidation` schema installed into `app/`.
The external runner/test-helper/network-guard hashes are recorded separately.

After specific authorization for local model initialization and these three NLI
checks, run with the **old environment**, then validate with the **new schema**:

```powershell
Set-Location $CollectorRoot
& $OriginalPython "$EvalRoot/scripts/frozen_evidence_probes.py" --collector-root $CollectorRoot --clean-bundle $CleanBundle --adapter-config "$RunRoot/altered/adapter.json" --source-audit "$RunRoot/source-audit.json" --authorization-record NEW_SOFTWARE_PROBE_AUTHORITY --output-dir "$RunRoot/probes"
if ($LASTEXITCODE -ne 0) { throw 'Evidence software rehearsal failed; no full collection' }
Set-Location $EvalRoot
& "$EvalRoot/.venv/Scripts/python.exe" -c "import sys; from pathlib import Path; from app.game.research.evidence_validation import EvidenceValidation; from app.game.offline.calibration import read_json,MeasurementSetup; p=EvidenceValidation.model_validate_json(Path(sys.argv[1]).read_text()); p.require_resources(MeasurementSetup.model_validate(read_json(sys.argv[2])['observed_setup']).resources); print(p.validation_id)" "$RunRoot/probes/evidence-validation.json" "$RunRoot/altered-preflight.json"
if ($LASTEXITCODE -ne 0) { throw 'Invalid or resource-mismatched Evidence proof' }
```

Outputs are `authorization.json`, `network.jsonl`, `evidence-validation.json` and
`scope.json`; a failure after initialization retains `probe-error.json`/the journal.
This proof concerns public output semantics under the observed resource binding;
controlled retrieval fixtures do not establish poisoned-corpus retrieval quality,
source truth or immunity. No paid inference or downloads are allowed.

### Small campaign rehearsal and safe resume

Each prototype has 40 development candidate answers (20 groups, paired answers)
and four captured candidates: **160 candidate outcomes per scenario per task**,
or 320 for one scenario evaluated on both tasks. No history/final-test collection
is added. With the unchanged five-sample Confidence setting, at most 200 local
generation requests per task/scenario are planned. These counts are a proposed
bounded authorization, not permission to run; ordinary prerequisite exclusions and
failures remain genuine recorded outcomes.

Before the full campaign, propose at most eight actual verifier calls (the first
predeclared paired group/full roster), at most ten Confidence generations and
128 loopback metadata requests. Use the **full unchanged scenario request** and a
fresh journal. The external runner's `--operation collect` mode forwards to the
**existing** collector CLI, with the existing `on_start` callback stopping before
the ninth start is written. It does not add a recording format or collector loop.
It validates the actual old-source preflight against the full request before
dispatch, enforces explicit network ceilings and records its external helper hashes:

```powershell
Set-Location $CollectorRoot
& $OriginalPython "$EvalRoot/scripts/frozen_evidence_probes.py" --operation collect --collector-root $CollectorRoot --clean-bundle $CleanBundle --adapter-config "$RunRoot/altered/adapter.json" --source-audit "$RunRoot/source-audit.json" --authorization-record NEW_EIGHT_CALL_REHEARSAL_AUTHORITY --request "$RunRoot/ALTERED_REQUEST.json" --stop-after 8 --generation-limit 10 --metadata-limit 128 --output-dir "$RunRoot/rehearsal"
```

Status 130 (`KeyboardInterrupt`) at the deliberate boundary is expected under the
existing collector contract; this is partial collection, not
an eight-call evaluation dataset. Use `load_bundle` to recover flushed attempts and
review `started.jsonl`: every started ID must have a retained executed completion,
no duplicates, no issues requiring adapter review and no resource drift. The full
evaluator correctly rejects an incomplete bundle. Never evaluate just the favorable
completed subset. Retain all outcomes/timings, including failures.

The collection owner verifies the restored CLI supports `--resume-from` and its
public `collect(..., on_start=...)` callback before any calls. Resume only known
unattempted work, in another new output directory with the identical full request
and setup; do not retry failures or guess what an ambiguous in-flight call did:

```powershell
Set-Location $CollectorRoot
# Example remaining generation ceiling only after confirming ten requests were used.
# Otherwise set it to 200 minus the ACTUAL rehearsal generation count in the audit.
& $OriginalPython "$EvalRoot/scripts/frozen_evidence_probes.py" --operation collect --collector-root $CollectorRoot --clean-bundle $CleanBundle --adapter-config "$RunRoot/altered/adapter.json" --source-audit "$RunRoot/source-audit.json" --authorization-record NEW_REMAINING_CAMPAIGN_AUTHORITY --request "$RunRoot/ALTERED_REQUEST.json" --resume-from "$RunRoot/rehearsal" --generation-limit 190 --metadata-limit 1000 --output-dir "$RunRoot/completed"
& $OriginalPython -m app.game.offline.collect check "$RunRoot/completed"
```

Apply the existing loopback `NetworkBudget` around the resumed CLI too, with the
remaining **approved** generation allowance; never reset the campaign allowance
as though the rehearsal had not happened. The wrapper stores authorization,
network counts/ceilings and planned-stop information in a fresh sibling
`rehearsal-runner-audit/` or `completed-runner-audit/`; normal collector files remain
in the requested output directory. Inspect `planned_stop` as well as exit status:
an unplanned failure is not the successful eight-call rehearsal. The 1000-request
resume metadata ceiling is a proposed bound, not automatic approval. A complete request has 160 outcomes,
actual setup unchanged and the original examples/labels. The new evaluator then
uses the command below with `--scenario DECLARATION.json "$RunRoot/completed"`
and `--scenario-evidence-validation DECLARATION.json "$RunRoot/probes/evidence-validation.json"`.

Under a separately approved run, use the preparation/request/declaration example
in `upstream_evidence_experiments.md`, substituting the **matching original
collection revision/environment**. Build a new experimental index only; never
modify original resource paths. A scenario request contains development examples
only and explicit new collection authority. Validate the declaration before calls.
For K scenarios, D original development examples and V candidates, collection
plans **K × D × V** candidate outcomes; legitimate unavailable candidates are
recorded without fabricated calls. Internal generation calls also need an explicit
ceiling based on the approved adapter sampling settings. No history/final-test
collection is added. Preserve failures and use only supported unattempted resume.

Commands below are a later handoff, **not commands executed by this change**:

```powershell
# In the matching original collection environment, after isolated index/resource readiness:
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG='build/FROZEN_EVAL_NEW/altered/adapter.json'
.venv/Scripts/python.exe -m app.game.offline.collect validate ALTERED_REQUEST.json
.venv/Scripts/python.exe -m app.game.offline.collect collect ALTERED_REQUEST.json --output-dir build/FROZEN_EVAL_NEW/altered-recordings
.venv/Scripts/python.exe -m app.game.offline.collect check build/FROZEN_EVAL_NEW/altered-recordings

# Current evaluation checkout; retained reports only, no inference or fitting:
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment evaluate --prototype-bundle build/multitask-prototype42-v1 --task arithmetic --clean-bundle build/multitask-policy42/arithmetic/collection/recordings.json --report-attacks ORIGINAL_REPORT_ATTACKS.json --scenario DECLARATION.json build/FROZEN_EVAL_NEW/altered-recordings --scenario-evidence-validation DECLARATION.json ALTERED_EVIDENCE_VALIDATION.json --output build/FROZEN_EVAL_NEW/arithmetic-evaluation.json
```

Use `--task factual` with the factual clean bundle for the experimental factual
prototype. `--prototype-bundle` fully checks the extracted manifest, hashes,
artifact IDs and original scope. `--task` is required with this mode. Alternatively:

```powershell
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment evaluate --policy ORIGINAL_POLICY.json --clean-bundle ORIGINAL_RECORDINGS.json --report-attacks ORIGINAL_REPORT_ATTACKS.json --scenario DECLARATION.json ALTERED_RECORDINGS.json --output NEW_EVALUATION.json
```

`ORIGINAL_REPORT_ATTACKS.json` must contain the original specification, e.g.
`{"version":"report_corruption_v1","suppression":"unavailable"}` for the two
completed prototypes. Its digest and original attack axes are checked, not guessed.
Repeat `--scenario DECLARATION RECORDINGS` for the predeclared set, and
`--scenario-evidence-validation DECLARATION VALIDATION` for each applicable proof.
No report-corruption actions are applied during this evaluation: it compares clean
replay with the supplied fresh upstream recordings. Report corruption and poisoning
are not implicitly composed. All inputs/configuration paths remain explicit.

The output parent must exist; the output file must be new (`open('x')`). Missing or
invalid inputs return status 2 and no evaluation report/policy. The original policy
file is opened only for reading, its byte SHA-256 is reported, and byte stability is
checked before writing the report. No `policy.json`, fitted artifact or certificate
is written. Retain the original input bundles/declarations for audit.

## Output: `frozen_upstream_development_evaluation_v1`

The report records original artifact/policy/context IDs, objective version,
reputation snapshot, threshold, minimum participants, cost units/resource weight,
all exact strategy definitions and probabilities, original clean coverage floor,
byte hash and optional prototype bundle ID. It explicitly states:

```json
{
  "evidence_role": "prepared_development_only",
  "original_certificate_scope": "original_fitted_problem_only",
  "original_certificate_validated": true,
  "new_scenario_optimality_claim": false
}
```

`scenario_metrics` starts with `clean`, then each declared scenario ID. Entries
bind actual resource manifest, request and scientific recording IDs and include:

- `metrics`: expected correct/false acceptance/rejection and uncertainty counts,
  example count, decision coverage, selective risk, unresolved count, configured
  estimated attempt cost and the existing cost-inclusive `mean_loss` diagnostic.
  Counts are sums across examples; divide by `metrics.examples` for fractions of
  all evaluated examples. Selective risk is errors/decisive decisions and stays
  JSON `null` when no decisions are made.
- `validation_loss` and `uncertainty_rate` separately from
  `configured_cost_inclusive_diagnostic`. The latter is validation loss plus the
  original configured resource weight times frozen estimated cost. It is **not**
  a newly optimized objective, nor the reliability-first certificate game value.
  Timings are retained in the source bundles; no costs are recalibrated.
- Expected failed/unavailable attempt counts and unresolved requirements per
  example; weighted reason counts across examples; per-strategy metrics,
  validation losses and integer reason counts, including zero-probability plans.

`outcomes` contains every strategy/example/scenario public finalization, numerical
score/status, truth label, contributors, required/achieved/unresolved capabilities,
execution states and reason codes. Aggregate scores remain agreement/signed vote
scores, not calibrated correctness probabilities. No clean coverage promise is
extended to poisoning; changed coverage is measured even when it is zero.

All metrics are **prepared development diagnostics**, not final-test evidence or
held-out generalization. The prototype remains reference-assisted and restricted
to its original prepared questions. Synthetic test outcomes demonstrate software
contracts only; neither certificates nor these tests establish poisoning resistance.

Focused regression command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_upstream_evaluation.py tests/test_game_upstream_evidence.py tests/test_game_clean_coverage.py tests/test_game_reliability_first.py tests/test_game_runtime.py tests/test_game_prototype_bundle.py -q
```
