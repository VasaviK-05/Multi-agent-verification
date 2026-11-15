# Prospective execution and publication runbook

This implementation extends `038779359aac0d13ee8c1e6e686893a34de125d3` in the isolated `codex/experiment1-prospective-game` worktree. No historical policy, recovered manifest, audit evidence, PR #37, collector, verifier, runtime or database code is changed. Historical recovery is closed; no trees/archives were searched again. This runbook is not an authorization or an empirical results report.

## Current decision and minimum inputs

| Stage | Bounded Arithmetic | Grounded direct Factual | Minimum acceptance evidence |
|---|---|---|---|
| Protocol/software | Implemented; reviewable | Implemented; reviewable | Pin reviewed source revision **and bytes**, Python/dependency environment and explicit study settings |
| Supported population and labels | Blocked | Blocked | Independent label records; outcome-free H/D/Final roster; whole related groups; reference/input eligibility and preserved quarantines |
| Four-verifier collection/reuse | Blocked | Blocked | Matching candidate/adapter/model/corpus/prompt/resources; actual factory/observer; complete terminal attempts; durable result receipt; collection-ID-specific authorization |
| New policy and matched baselines | Blocked | Blocked | Approved complete H/D TrainingManifest, task-conditioned History context, calibration, actual unconstrained PolicyBuildSpecification; protocol and fitting-ID approvals |
| Final Test | Blocked | Blocked | Independent untouched custody, frozen methods, exact manifest/reservation/payload SHA and external release |
| CSV/LaTeX/PNG/PDF export | Implemented; synthetic tests pass | Implemented; synthetic tests pass | Authenticated prospective aggregate report bytes; fresh private destination; empirical reports only for actual results |

The existing research_v1 eligibility approval (744 Development candidates / 372 pairs) is not revoked and need not be requested again. It establishes eligibility, not verifier support, independent correctness adjudication, collection permission or Final Test custody. Existing pilot reports and calibration remain evidence requiring authentication against this **new** protocol. No existing complete recording has been certified reusable for it. History has no complete approved four-verifier record set. Benchmark names do not establish Rule support for GSM8K or Evidence grounding for HotpotQA. Existing outcome-free Final reservation metadata does not establish untouched independent custody.

Smallest defensible collection: first choose genuinely supported direct tasks and independently label/partition them; record every required verifier once for each approved History and Development candidate lacking a matching authenticated complete recording. Reuse a terminal failed/abstaining attempt as that state, never as an inferred report. Preserve timing and attempt/resource identity. The nominal maximum is four calls per approved candidate for a four-verifier roster; subtract only exact verified completed calls. Missing History cannot be inferred from Development. No numerical sample size is authorized by this code: preparation/research must set precision/power and group counts before collection. At least two groups permits a bootstrap calculation but does not establish publication adequacy.

## Exact owner requests (not sent)

| Owner | Requested deliverable | Acceptance |
|---|---|---|
| Raunak | Versioned capability record for bounded direct arithmetic and grounded direct facts; exact Rule patterns/range, Evidence corpus+retrieval grounding, Semantic reference semantics, Confidence model/prompt/service; actual source/resource fingerprints and compatible cost-calibration provenance | Bind reviewed evidence to collection ID; no unsupported benchmark substitution or silent reference-assisted change; observed resources match declared manifest per attempt |
| Tanmayee | Exact RecordingRequest and prerequisite-aware zero-argument factory returning verifiers/setup/observer; platform and exception-boundary certificate; durable journal/restart test including crash after call and before acknowledgment, torn record and resource changes | Request preserves examples/questions/labels/roles/groups; observer snapshots actual resources; completed call never repeated; ambiguous start quarantined; recorded result durable before acknowledgment |
| Preparation/custody owner | Independently adjudicated label ledger, supported H/D rosters and grouping/quarantine ledger, source/input/reference hashes; outcome-free Final reservation plus independent exposure/custody record | No automated-label-to-human cast; no cross-split related groups, shared content or question IDs; do not release payload/outcomes before exact scoring approval |
| Vasavi (game/research) | Explicit selected/informative minima, coverage floor, budget, costs/units/coefficient, loss/objective, History priors, dependencies, fixed attacks and suppression semantics, solver tolerances and bootstrap seed/resamples; captured bound build specification | Exact protocol/collection/fitting identities and external approvals; fit new task-conditioned policies; freeze every feasible baseline/certificate and disclose unavailable/noncompliant methods |
| Samika | No database work required | Offline private files only; any later DB integration separately scoped |

Collector limitation observed at the pinned feature source: `collect.py` fsyncs `started.jsonl` but only flushes `attempts.jsonl`. It rejects resume when a start lacks completion; it does not retry ambiguous inference. Torn JSON records fail closed. Thus no duplicate-call guarantee is deliberately weakened, but crash-safe durable **completion** and complete recovery are not yet certified. The separate dirty active-worktree journal changes were neither copied nor modified. Tanmayee must supply/review the durable implementation and intended-platform tests before real execution. Re-pin source IDs/fingerprint/environment after any approved integration; stale approvals cannot be reused.

## Commands and order

Commands below are templates for reviewed **private** inputs, not instructions to run inference now. SHA variables must come from trusted review/custody, not an arbitrary unreviewed file. Use a finalized source checkout and pinned dependency environment. Real input files do not yet exist in an authorized complete package. Keep private paths and raw receipts out of public Git.

```sh
python3 -B -m app.game.research.experiment1.prospective readiness \
  "$PRIVATE/protocol.json" --sha256 "$PROTOCOL_SHA" \
  --authorizations "$PRIVATE/authorizations.json" --authorization-sha256 "$AUTH_SHA" \
  > "$PRIVATE/readiness.json"
```

Exit 2 is normal until **all** scoring gates pass; inspect the per-cohort stage needed for the intended action. Collection is permitted only when that cohort's `history_development_collection.ready` is true and the exact request/collector is approved. The collector itself is an existing lower-level API, not an approval gate. Do not use its command alone to bypass prospective readiness.

After that gate and Tanmayee's durable-collector acceptance, validate and collect History/Development requests separately (never a reserved Final request). `validate` does not construct a factory:

```sh
python3 -B -m app.game.offline.collect validate "$PRIVATE/history-request.json"
python3 -B -m app.game.offline.collect validate "$PRIVATE/development-request.json"
python3 -B -m app.game.offline.collect collect "$PRIVATE/history-request.json" --output-dir "$PRIVATE/history-run-001"
python3 -B -m app.game.offline.collect collect "$PRIVATE/development-request.json" --output-dir "$PRIVATE/development-run-001"
python3 -B -m app.game.offline.collect check "$PRIVATE/development-run-001"
# Resume only after a successful custody/journal check, using identical request/resources:
python3 -B -m app.game.offline.collect collect "$PRIVATE/development-request.json" \
  --resume-from "$PRIVATE/development-run-001" --output-dir "$PRIVATE/development-run-002"
python3 -B -m app.game.offline.collect export "$PRIVATE/approved-combined-recordings.json" \
  --context "$PRIVATE/planning-context.json" --output "$PRIVATE/training.json"
```

`export_training` requires the correctly combined approved H/D/reservation bundle, not merely a Development-only request. The export command above names the eventual combined complete bundle (a new validated RecordingBundle file); preparation must assemble/validate it with existing recording APIs before export. Do not concatenate unvalidated journals or replace a reservation. PlanningContext must bind task History through existing `bind_task_history` and complete offline evaluation through `bind_evaluation`; capture the actual resulting PolicyBuildSpecification. The prospective readiness checker verifies it, and does not synthesize it from a candidate roster.

After complete H/D and exact fitting approval, fit and freeze **one new cohort** explicitly. The execution CLI checks the gate before optimization. It uses existing full-game replay, clean-coverage/reliability preparation, solver/certificates and matched comparison implementation; no historical policy is an input. Genuine nonoptimal solver output yields matrix/certificate/status and exit 2, not a manufactured policy.

```sh
python3 -B -m app.game.research.experiment1.prospective.execute fit \
  "$PRIVATE/protocol.json" --sha256 "$PROTOCOL_SHA" \
  --authorizations "$PRIVATE/authorizations.json" --authorization-sha256 "$AUTH_SHA" \
  --cohort arithmetic --freeze-record "$REVIEWED_FREEZE_RECORD" --output "$PRIVATE/arithmetic-fit.json"
```

The fit output is an envelope; its `manifest` is the updated prospective manifest. Save it to a **new** private path for review:

```python
import json
from pathlib import Path
result = json.loads(Path('/reviewed/private/arithmetic-fit.json').read_text())
assert result['status'] == 'frozen'
with Path('/reviewed/private/frozen-arithmetic-manifest.json').open('x') as f:
    json.dump(result['manifest'], f, indent=2, sort_keys=True, allow_nan=False)
    f.write('\n')
```

Use its newly reviewed SHA as input to the same command with `--cohort factual` and a new output path. Extract/review the final two-cohort manifest. Fitting IDs remain bound to the approved unconstrained specification; only derived coverage/reliability overlays change. Already frozen cohorts cannot be refitted. Freeze cost/coverage/attacks/references/resources and all baseline selection before any held-out release. Unsupported or infeasible methods remain explicitly unavailable; uniform remains exactly 1/N even when its Development coverage violates the floor.

Development replay is separately labelled exploratory. It currently requires the `final_test_authorization_review` stage (including reviewed frozen comparison and independent custody); it does **not** require a Final payload release:

```sh
python3 -B -m app.game.research.experiment1.prospective.execute development \
  "$PRIVATE/frozen-manifest.json" --sha256 "$FROZEN_SHA" \
  --authorizations "$PRIVATE/authorizations.json" --authorization-sha256 "$AUTH_SHA" \
  --cohort arithmetic --output "$PRIVATE/arithmetic-development-report.json"
```

The custodian must also hold complete compatible Final verifier recordings. Any new Final recording requires its own explicit authorization and a blinded, reviewed collector operation; the History/Development approval and scoring release do not authorize new inference. No Final collection command is supplied or executed here. Only after independent custody and exact-manifest scoring release, replay the exact released Final bytes. The path is not opened until the gate passes; bytes must match the authorized payload hash and reservation. Release is external and is not created by any CLI here.

```sh
python3 -B -m app.game.research.experiment1.prospective.execute final \
  "$PRIVATE/frozen-manifest.json" --sha256 "$FROZEN_SHA" \
  --authorizations "$PRIVATE/final-authorizations.json" --authorization-sha256 "$FINAL_AUTH_SHA" \
  --cohort arithmetic --payload "$PRIVATE/released-arithmetic.json" --output "$PRIVATE/arithmetic-report.json"
# Repeat explicitly for factual with its released payload and a fresh report path.
python3 -B -m app.game.research.experiment1.prospective.export \
  --report "$PRIVATE/arithmetic-report.json" "$ARITHMETIC_REPORT_SHA" \
  --report "$PRIVATE/factual-report.json" "$FACTUAL_REPORT_SHA" \
  --output "$PRIVATE/results/experiment1/run-001"
```

Readiness and execute compute actual Git HEAD and source fingerprint themselves. CLI callers cannot override them. Every execution embeds and saves an adjacent receipt with command, source pins, authorization-file SHA and the result ID before receipt attachment; report data include exact source/environment/resources/datasets/configuration/policy/comparison/strategy/attack/statistical IDs. Final permission must refer to the final manifest after **both** freezes. No command dispatches collection automatically, discovers protected files or releases Final Test.

## Export and interpretation

Export creates all requested five metric CSVs, four PNG/PDF families plus their underlying CSVs, two LaTeX tables, complete aggregate JSON per cohort, a Markdown interpretation report and hashed reproducibility inventory. `manifests/` stores aggregate identity receipts; `policies/` stores exact probabilities; `recordings/` explains private custody rather than copying raw data. Strategy definitions and resource/configuration identities are retained in aggregate provenance. Inspect receipts for sensitive resource/path details before any publication.

Clean-v-worst plots show decision validation loss with available pointwise 95% intervals; LaTeX and baseline CSV include worst-loss intervals. CSV preserves every individual attack and dependency group, mean cost, cost-inclusive objective, FA/FR, coverage, risk, abstention/unresolved/failure states. The paired interval file includes point estimates for full-minus-baseline differences; confidence bounds are omitted when any group resample is undefined, and undefined fractions are explicit. Empty intervals retain a CSV header and an explicit reason in the aggregate JSON. Missing cohorts and unavailable methods are disclosed. Cohorts, splits and evidence kinds cannot be pooled within one bundle. Costs are estimated attempted-verifier costs in approved units; actual collection durations remain in private recordings and are not relabelled as strategy latency.

Risk/coverage and cost/loss figures are frozen operating points across attacks, not optimized or retuned curves. Exact mixed probabilities are integrated before the attack maximum; maxima are recomputed in every paired whole-group resample. No additional bootstrap or threshold selection occurs during export. Results concern offline report-level forced support/rejection, confidence inflation and suppression, not actual evidence poisoning. Preserve nulls, negative differences, noncompliant uniform coverage and infeasible methods.

Existing result destinations are rejected. Figures render in a temporary sibling; failed rendering leaves no result destination. A destination is then exclusively reserved; a publish-time I/O failure can leave an incomplete destination for inspection and must not be silently overwritten. Synthetic fixture export requires `--allow-synthetic` and visibly labels every table/figure/report. It is never empirical evidence.

The SHA check authenticates bytes against a caller-trusted digest; it does not replace resource, label, collector, custody or authority authentication. Export accepts only explicitly selected aggregate reports and does not reopen training or Final payloads. No generated empirical tables exist yet. No inference, real fit, Final scoring, push, merge or PR action was executed for this change.

Matplotlib is an export-only optional dependency: it is imported with the noninteractive Agg backend only after export validation. Tests used the pre-existing isolated `/private/tmp/evidence-phase1-matplotlib` installation, not a production environment change. The bundle records Python/platform/NumPy/Matplotlib versions; the execution report separately records the approved replay environment.
