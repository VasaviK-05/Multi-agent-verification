# Draft factual feasibility study — not approved or executable

**Publication boundary:** the JSON requests, reservations, labels, preflight receipts
and generated reports described here are local-only and excluded from Git. JSON
links refer to those local outputs. Reusable source/tests and this handoff are
shared; tests use public example text and synthetic reserved rows without private
files. Start local adapter configuration from `docs/verifier_project_adapter.template.json`.
Source publication does not approve this study or any inference run.


This proposal uses the existing ten question/answer/reference rows to exercise
the **four-verifier factual workflow**. It is a small known-corpus feasibility
pilot, not a confirmatory test of the project's full research claim. No new
collector, calibration method or policy builder is introduced. No expensive
execution is authorized by this document.

## What is prepared

- `roster.draft.json`: eight related-topic groups, deterministically assigned with
  seed **20261026**, without consulting benchmark flags or verifier outcomes.
- `preparation.draft.json` and `recording-request.draft.json`: **six actual
  preparation examples**, supplied references, actual heuristic analyzer outputs,
  builtin candidate descriptors and independent source-grounded **proposed** labels.
- `label-review.draft.json`: six source comparisons, short evidence excerpts,
  excerpt digests and null reviewer approvals. No framework verdict was used as truth.
- `producer-plans.json`: actual `collection_plan`, requirement and prerequisite
  outputs; unknown requirements/readiness remain unknown.
- `final-reservation.draft.json`: four **metadata-only** prospective final entries.
  No final labels, reports, timings, candidate payloads or outcome paths are included.
- Adapter, execution, recording, loss, dependency, attack and calibration files:
  actual known inputs are filled; genuinely unknown permission/resource/freeze fields
  remain null. No reputation snapshot or verifier report is invented.
- `validation.json`: current schema validation and resource preflight, with exact
  unresolved field locations. `resource-plan.json`: concrete proposed work.

The fixed preparation producer is `scripts/prepare_factual_study_draft.py`.
It allow-lists question/answer/context fields before proposing partitions and
ignores the benchmark flags. Content digests prevent changed preparation answers
from inheriting unrelated source labels. Its output directory must be new; never
regenerate a witnessed study or re-open candidate-source flags after custody freeze.

## Source, applicability and proposed labels

Source candidates: repository `data/test_benchmark.jsonl`. Retrieval/reference
corpus: `data/test_evidence_corpus.json`, SHA-256
`0170d64b697dab9bbeb91e2f935b6bcad862ae8bb55958beea712ccf1e424795`.
Intended scope: short capital lookups, software/AI definitions and a historical
scientific attribution, with supplied reference passages and the fixed tiny corpus.
This is reference-assisted factual QA; it says nothing about open-world retrieval,
unseen populations, adversarial evidence or general hallucination detection.

Proposed use is **local internal feasibility evaluation**, with no redistribution
approval inferred. No repository-root license file or preparation-use permission
was found. The dataset owner must confirm permitted use of these rows/reference
passages and witness the final reservation. Public availability is not a permission
record. The copies here are local review drafts, not an approved released dataset.

All six preparation candidates receive a proposed `true` label based on external
source comparison, not their original boolean flags:

- Germany: the [Berlin city government's portal](https://www.berlin.de/en/)
  identifies Berlin as Germany's capital.
- AI and ML: [IBM's AI definition](https://www.ibm.com/think/topics/artificial-intelligence)
  and [ML definition](https://www.ibm.com/think/topics/machine-learning) independently
  support the supplied broad descriptions. Human review should explicitly accept
  the proposed paraphrase/completeness rubric for definitions.
- Python: the [PSF executive summary](https://www.python.org/doc/essays/blurb/)
  identifies a high-level language; its [application list](https://www.python.org/about/)
  supports the general-purpose description.
- India: the [Delhi government tourism history](https://delhitourism.gov.in/aboutus/history_of_delhi.html)
  identifies New Delhi as the capital of India.
- Relativity: [NIST](https://www.nist.gov/atomic-clocks/a-powerful-tool-for-science/putting-einstein-test)
  attributes special and general relativity to Einstein.

These are **draft adjudications requiring approval**, not human-certified labels.
Some alternative source pages returned 403/502; the audit uses only successfully
inspected sources above. No independent sources were opened to label the proposed
final examples. The candidate inventory was already public/inspected before this
draft split; the prospective final reservation protects later fitting isolation,
not a claim that this is a previously unseen or independently administered test set.

The six proposed preparation labels are all positive. There is **no negative-answer
sample**, so false-accept behavior cannot be estimated from these preparation rows.
No incorrect answers or labels were manufactured to fix class balance. A credible
later study needs independently sourced incorrect candidates and more groups under
a new approved roster; all alternatives/paraphrases stay with their original group.

## Proposed grouping and allocation

The grouping keeps France/Paris together and AI/ML together; all other topic groups
are singletons. This is a concrete grouping proposal, not an authenticated grouping
protocol. The custodian reviews any additional related-question overlap before use.
Sorted group names are shuffled with `random.Random(20261026)` once, before external
label adjudication, then assigned 2/3/3 groups:

- History: Germany plus AI/ML — **2 groups, 3 examples**.
- Development: Python, India and relativity — **3 groups, 3 examples**.
- Final reservation: **3 groups, 4 metadata entries**; fitting inputs contain no
  final candidate payload or correctness data.

The 25%/37.5%/37.5% group allocation is a practical rounding for only eight groups;
it is not a statistical recommendation. Do not optimize it after viewing outcomes.
Final labels and any final execution belong to the custodian/evaluation workflow
after configuration freeze. `custody_record` is deliberately null today.

## Proposed settings, not approved defaults

One measured pass of all six preparation examples, **zero warmups and no repeats**.
Factory initialization is excluded by the existing timer; first-verify/lazy/cache
effects within each attempt are included. This avoids claiming a warmed model when
separate CLI processes would initialize different model instances. Six included
attempts per verifier are an engineering pilot estimate, with no tail guarantee.

Keep existing provider controls: five samples, temperature 0.8, 60-second timeout.
The split seed is not a provider seed: existing OllamaSampler uses seeds 0..4 per
call. Runtime/provider nondeterminism remains possible. No confidence labels are
injected through the reference context.

Proposed losses: false accept **1**, false reject **1**, uncertainty **0.2**;
Beta reputation prior **1/1**; decision threshold **0.55**; existing easy-question
execution floor **2**; retain both aggregations and every feasible team.
These are normative pilot choices for review, not empirically fitted settings.
`budget` and `resource_weight` remain null until actual millisecond costs are reviewed.

Attacks: existing `report_corruption_v1`, suppression `unavailable`, offline only.
Known shared embedding/NLI weights are declared. All four verifiers additionally
remain unresolved under the existing `shared_unknown` treatment, so the conservative
dependency graph has one connected group. This is an explicit proposed threat
assumption, not evidence of independence or an upstream model-poisoning experiment.

## Concrete index and collection work

No genuine build receipt was found for the old vectors. They are preserved.
The intended new index uses the actual **10-article, 216-word test corpus**, with
chunk size 500: **10 title/text chunks**, one local embedding pass, no downloads.
The adapter file records the observed local embedding snapshot and the cached NLI
snapshot, approximately 91.6 MB and 578.7 MB of files respectively. Preflight observed
16 logical CPUs and 16,876,888,064 bytes physical RAM; peak model/service RAM is unknown.
Saved Ollama metadata identifies version 0.40.5 and an actual model digest; factory
checks it live again. No model alias is treated as a version.

The small local preparation job below **completed successfully** in a new target
under `build/`, using the existing EvidenceRetriever and cached local embedding.
It created ten chunks/vectors and a genuine new-build receipt. Hash checks confirmed
the old index files were unchanged. No downloads or generation occurred. This
resolved index provenance without adopting study settings. Do not rerun against
the now-existing target; the command refuses overwrites:

```powershell
.venv/Scripts/python.exe -m app.benchmark.project_adapter prepare-index docs/studies/factual-feasibility-draft-v1/adapter.draft.json --output build/factual-feasibility-draft-v1/index-receipt.json
```

The single full recording run proposes **24 verifier attempts**, **up to 30 local
generation requests**, and **100 local metadata GET requests** including factory
checks. Before/after observations hash approximately **33.5 GB of model-file bytes**
logically across 50 passes; OS caching may reduce actual disk reads. This overhead
is outside the attempt timer and may affect cache state. The sum of the configured
generation-request timeouts is **1,800 seconds**, not expected elapsed runtime or a
global deadline; initialization, NLI and hashing are additional. Pricing is unknown;
no monetary estimate is inferred. The proposed generation/recording run still needs
explicit resource authorization; small index preparation is already complete.

No timing-only run is planned: reports and durations come from the **same attempts**
through the existing detached collector. Failed attempts remain included and missing
observations are never invented.

## What validation currently says

Adapter/dependency/attack and execution/recording configurations are structurally
valid. Actual resource IDs, expected setup and the v2 resource manifest have now been
populated from inspection of the new index and observed resources. Recording and
preparation drafts correctly still fail on `preparation_authorization` and reservation
`custody_record`. Calibration awaits measured attempts and a `freeze_record`. These
nulls are intentional; do not replace them with claims of approval. Source changes
after this snapshot require fresh read-only inspection and actual resource binding.

The index/receipt now exist and **resource-only preflight passes**, recorded in
`build/factual-feasibility-draft-v1/resource-preflight.json` and `validation.json`.
Index preparation initialized the local embedding model once; preflight itself
initializes no models. No NLI initialization, generation or verifier attempt ran.

Separate software limitations are preserved in `software-findings.json`:

- The evidence-contract probe reproduced **3 failures, 1 pass**. Directional
  evidence becomes public uncertainty; conflicting evidence reports
  `no_relevant_evidence` rather than `conflict`. The known readiness gate stays active.
- Actual heuristic outputs recognize `direct_fact` for only **Germany and India**
  among the six preparation rows. The other four retain unknown requirements.
- `export_training` requires matching analysis/difficulty/score/version/requirements
  within a captured context. The six rows do not form one exportable policy cohort.
  They can still be collected completely for diagnostics; no row is silently dropped.

A narrower **Germany-history/India-development factual cohort** is technically
homogeneous but has only two positive examples and still requires evidence repair.
Adopting it is an explicit scope amendment, not an automatic filter. An arithmetic
pilot is a different population. Separate arithmetic-pilot work present in the tree
is preserved and is not adopted as this factual proposal or proof of the full claim.
The contracts can support a separately approved rule/semantic arithmetic pilot;
none of these ten original questions is arithmetic, so that needs its own population
and approval rather than relabeling these rows or retaining evidence under a fake adapter.

## Correct order and exact recording commands

1. Review/approve the draft population, grouping, six proposed labels, settings and
   resource plan. Supply a real preparation permission and custody witness.
2. The separate ten-chunk index is built and inspected. Recheck after source/resource
   changes; populate fields only from actual setup. `execution_configuration_id` is
   **ResourceManifest.manifest_id**, not MeasurementSetup.fingerprint.
3. Copy reviewed drafts to `build/factual-feasibility-draft-v1/` as
   `preparation.approved.json` and `recording-request.approved.json`. Record actual
   approval/witness references. Set `expected_setup` and execution ID from the new
   observed setup; use the identical reservation everywhere. Preserve the draft files.
4. Preflight/validate, then execute **only if diagnostic collection is explicitly
   authorized despite the known fitting blockers**:

```powershell
.venv/Scripts/python.exe -m app.benchmark.project_adapter preflight docs/studies/factual-feasibility-draft-v1/adapter.draft.json --collection build/factual-feasibility-draft-v1/preparation.approved.json --output build/factual-feasibility-draft-v1/preflight-approved.json
.venv/Scripts/python.exe -m app.game.offline.collect validate build/factual-feasibility-draft-v1/recording-request.approved.json
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG = (Resolve-Path docs/studies/factual-feasibility-draft-v1/adapter.draft.json).Path
.venv/Scripts/python.exe -m app.game.offline.collect collect build/factual-feasibility-draft-v1/recording-request.approved.json --output-dir build/factual-feasibility-draft-v1/recordings
.venv/Scripts/python.exe -m app.game.offline.collect check build/factual-feasibility-draft-v1/recordings
```

5. Freeze the **measurement inputs** with a real witness and approved exclusion rule,
   then calculate costs. The current CalibrationRequest requires this witness before
   it will create a cost artifact; budget/penalty choices are not needed yet.

```powershell
.venv/Scripts/python.exe -m app.game.offline.calibration build/factual-feasibility-draft-v1/calibration-settings.approved.json --measurements build/factual-feasibility-draft-v1/recordings/measurements.json --output build/factual-feasibility-draft-v1/verifier-costs.json
```

6. Review those measured millisecond costs and choose budget/loss-per-ms settings.
   Resolve evidence defects and the explicit cohort contract/scope. Derive history
   reputation from actual directional attempts versus the independent labels using
   public in-memory ReputationManager update/statistics interfaces; then use the
   existing selector/capture_context. No framework verdict replaces ground truth.
7. Use public `export_training` for the **first** export from the immutable raw bundle,
   with public `apply_calibration` and `bind_evaluation` via the existing calibrated
   context helper. This avoids the cost/category cycle without rewriting old records.
   Existing already-exported categories cannot be silently rebound. Freeze the full
   fitting configuration before final release; fit/export/reload through the existing
   builder only after all gates pass.

Two freezes are required: witnessed data roles/measurement inputs before calibration,
then the final budget/loss/policy configuration before held-out evaluation. There is
no need to invent costs or ask for a final millisecond budget now.

Focused package checks: **10 passed**. The separate existing evidence probe reproduced
**3 failures and 1 pass**; these are software blockers, not new package-test failures
or measured model accuracy. Whitespace/compilation checks passed. No protected
production files were changed, committed or pushed by this preparation work.

## Approval checklist

- Approve or amend this **factual feasibility pilot**, grouped roster, six source-
  grounded proposed labels and internal-use permission/custody record.
- Approve the proposed one-pass/no-warmup plan, 1/1/0.2 losses, 1/1 prior and offline
  attack/dependency assumptions. Millisecond budget/penalty remain undecided.
- The ten-chunk index is complete. Decide whether to authorize **24 diagnostic
  verifier attempts/up to 30 local generations** before evidence/cohort repairs,
  or wait for those repairs first.

## Reusable preparation CLI

The initial custodian-only preparation command requires explicit inputs and a new
local output directory. Run before any final reservation freeze; it reads the
initial candidate inventory, not a fitting/evaluation payload:

```powershell
.venv/Scripts/python.exe -m scripts.prepare_factual_study_draft --candidate-input data/test_benchmark.jsonl --adapter-config build/adapter.local.json --index-dir build/factual-feasibility-draft-v1/index --index-receipt build/factual-feasibility-draft-v1/index-receipt.json --output-dir build/factual-feasibility-draft-v1
```

Do not rerun against existing/witnessed output. The diagnostic runner separately
requires `--study-dir`, a new `--output-dir`, and a nonblank
`--authorization-record` identifying explicit new permission. It cannot inherit
2026-10-26 authorization. It checks loopback endpoints, disables redirects, and
keeps the original fixed 24/30/100 execution/generation/metadata bounds.
