# Real verifier collection and preparation

The completed, separately authorized local cost campaign is described in
[verifier_cost_results.md](verifier_cost_results.md). Its empirical files remain
local. The examples below are preparation instructions, not execution permission.
Optional runtime dependencies are listed in `requirements-verifier-collection.txt`;
installing dependencies or provisioning models requires separate authorization.

The concrete factory is `app.benchmark.project_adapter:create_verifiers`. It
returns the pair required by the existing timing collector. Set
`VERIFIER_COLLECTION_ADAPTER_CONFIG` to the reviewed adapter JSON. The optional
`create_recording_verifiers` factory returns the triple required by the separate
detached recording producer: verifier instances, observed setup and resource observer.
Neither factory calls `verify` or generates answers. Only explicit collection does.

The adapter uses the existing SemanticVerifier, EvidenceRetriever/EvidenceVerifier,
RuleVerifier, OllamaSampler/SelfConsistencyJudge/AgreementLabeler and ConfidenceVerifier
constructors. Embedding and NLI objects are shared, matching their configured use;
CPU execution and eager initialization are recorded in the environment. Constructors
receive local snapshot paths and `local_files_only=True`. Thresholds, prompts,
claim construction, retrieval and verifier judgments retain their implementations.
Factory metadata checks re-observe the Ollama version/model digest before and after
initialization. The service owner must keep that model binding stable throughout
timing collection; the recording observer additionally checks before/after attempts.

## Inspect before collection

The generated local configuration is `build/verifier-collection/adapter.local.json`.
The reusable starting template is `docs/verifier_project_adapter.template.json`.
All paths in that configuration are local; relative resource paths resolve against
the repository root. The example template's test corpus is a resource candidate,
not approval to use it for a scientific study. Select the intended corpus explicitly.

```powershell
.venv/Scripts/python.exe -m app.benchmark.project_adapter preflight build/verifier-collection/adapter.local.json --collection build/approved-preparation.json --output build/verifier-collection/preflight-reviewed.json
```

Preflight reads/hashes files and dependency metadata. It performs no model loads,
downloads, `verify` calls, generation or provider requests. It reports local model
bytes, corpus/index hashes, missing resources, hardware, unresolved provenance,
counts when a valid preparation roster exists, and setup/fingerprint when complete.
Readiness covers local inputs; the factory checks the live service independently.
It cannot determine peak RAM or service availability without initialization/probing.
No approved monetary prices are available; pricing remains null. Values are never
inferred from timing or a model name.

Local observations found an approximately 91.6 MB embedding snapshot and 578.7 MB
NLI snapshot, the test corpus/index, 16 logical CPUs and 16,876,888,064 bytes of
physical RAM. Those are file/hardware observations, not peak-memory estimates.
The original index manifest was legacy/alias-only and had no matching build receipt.
The completed campaign used a separately built ten-chunk index and an explicitly
approved preparation roster/procedural reservation. Those local artifacts are
listed in the results document; the template remains deliberately incomplete.

The currently installed Transformers tokenizer implementation reads the cached
`tokenizer.json` directly; absent optional SentencePiece is not treated as a missing
model dependency. Actual local constructor failures still propagate clearly.

## Observe or prepare resources explicitly

The metadata observation command uses only loopback GET requests to
[`/api/tags`](https://docs.ollama.com/api/tags) and
[`/api/version`](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml).
It does not pull, load or generate with a model. Only the requested model digest
and server version are retained, not the service's complete model list. URL
credentials/query strings and non-loopback services are rejected. No secret
environment values are serialized.

```powershell
.venv/Scripts/python.exe -m app.benchmark.project_adapter observe-service build/verifier-collection/adapter.local.json --output build/verifier-collection/ollama-observed.json
```

Set `service_observation` in the adapter JSON to that output. A saved observation
is not proof the service is still running: the factory compares fresh metadata.
No version is inferred from the mutable `llama3.2:3b` alias. Both raw hex and
`sha256:`-prefixed service digests are normalized and validated.

The separate local metadata check succeeded: Ollama reported version `0.40.5`
and a SHA-256 digest for the installed `llama3.2:3b` binding. The observation is
saved in `build/verifier-collection/ollama-observed.json`; it contains no timings
or generated answers. The socket check required leaving the sandbox after Windows
denied loopback access. Preflight itself still made zero provider requests.

For an index without a reliable build receipt, do not create one by copying a
model alias or merely hashing the old vectors. The explicit preparation command
builds a **new** index using the existing EvidenceRetriever and observed local
embedding model, then records the corpus, model, vectors and chunks digests.
It performs potentially costly corpus embedding and is never called by preflight
or the collection factory. Review corpus size/hardware first and run only when
authorized. It refuses existing target directories and only writes under `build/`.

Set `index_dir` to `build/verifier-collection/new-index` and `index_receipt` to
`build/verifier-collection/index-receipt.json` in the reviewed adapter JSON, then:

```powershell
.venv/Scripts/python.exe -m app.benchmark.project_adapter prepare-index build/verifier-collection/adapter.local.json --output build/verifier-collection/index-receipt.json
```

Preflight itself never builds indexes, downloads models or generates answers. Full
directory digests cover the local weight/tokenizer/config bytes. Source fingerprints
cover verifier implementations, adapter code and relevant prompt/claim/retrieval
helpers; setup records include dirty application source digest, Git revision,
dependencies, CPU/thread settings and service/model identity. Repeated resource
hashing is observer overhead outside the `verify` timer, not calibrated attempt cost.

## Supply approved preparation data

Copy `docs/verifier_preparation.template.json` to `build/approved-preparation.json`.
The dataset custodian supplies explicit permission, distinct history/development
dataset IDs, related-question group assignments and the existing outcome-free
final-test reservation. Each example supplies `example_id`, `question_id`,
`split_identity`, unique `run_id`, dataset ID/role, `purpose`, question, candidate
answer and actual nullable reference `context`. Labels and report fields are
rejected by this label-free schema. Final-test roles, reserved identities/content,
cross-role leakage, inconsistent repeated examples and inconsistent related groups
are rejected before any attempt. Repeated warm-up/calibration runs share the
example/group identity but require distinct run IDs.

`data/test_benchmark.jsonl` has 10 question/answer rows and 10 supplied contexts,
but no role/group roster, permission or final-test reservation. It cannot be
assigned preparation roles automatically. Its boolean flags are not used as
policy label provenance. There is consequently no legitimate populated collection
configuration yet. No missing references, labels, groups or reports were invented.

```powershell
.venv/Scripts/python.exe -m app.benchmark.prepare_collection build/verifier-collection/adapter.local.json build/approved-preparation.json --output build/collection.json
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG = (Resolve-Path build/verifier-collection/adapter.local.json).Path
.venv/Scripts/python.exe -m app.benchmark.collect_costs build/collection.json --output build/verifier-attempts.json
.venv/Scripts/python.exe -m app.game.offline.calibration build/calibration-settings.json --measurements build/verifier-attempts.json --output build/verifier-costs.json
```

Collection requires review/authorization of the resource report before expensive
execution. With N=5 (the existing default), every reached confidence attempt whose
context is not explicit judgment labels intends five generation calls. Preflight
counts this exactly for the supplied roster, including warm-ups, and gives a
0-to-intended range because an earlier verifier/provider failure can stop work.
Counts are unknown while the approved roster is absent; no generation count is
invented from the ten unapproved candidate rows.

The timing collector still propagates the original exception after recording all
attempts so far, never retries, and never invents later attempts. The separate
labelled recording producer has its own explicit failure contract. No changes
were made to that producer's behavior.

## Connect measured costs to compatible policy recordings

Timing-only output lacks canonical verifier reports, analysis/prerequisite
captures and independent correctness labels. It cannot become a TrainingManifest
by itself. The recording/integration owner must supply those independent inputs
using the existing detached recording contracts. Use `measurement_input(bundle)`
when measurements and reports are from that same verified recording bundle.

The current detached recording CLI is available for owners with approved labels,
analysis and candidate metadata. Its separate request must set
`factory=app.benchmark.project_adapter:create_recording_verifiers` and the matching
observed setup/resource ID. Validate it before running any collection:

```powershell
.venv/Scripts/python.exe -m app.game.offline.collect validate build/recording-request.json
# Only after resource/execution authorization:
.venv/Scripts/python.exe -m app.game.offline.collect collect build/recording-request.json --output-dir build/labelled-recording
.venv/Scripts/python.exe -m app.game.offline.collect check build/labelled-recording
```

Use `build/labelled-recording/recordings.json` as the collection bundle and
`build/labelled-recording/measurements.json` as calibration measurements. Do not
combine independently recorded timing rows with unrelated reports. For the
observer-enabled path, each executed attempt additionally performs four metadata
GET requests (two before, two after); resource hashing and these checks occur
outside the attempt timer. There are no inference requests from observation.

There are two distinct compatibility cases:

1. **Already exported Example records:** `planning_category` includes costs,
   budget, loss, dependencies and the frozen history snapshot through `category_id`.
   New costs can invalidate that identity even when raw reports would be unchanged.
   The diagnostic command below calls public `apply_calibration`, preserves the
   original manifest, and lists incompatible recording identities. It never clears
   bindings or rewrites categories. Recollect under the target category, or obtain
   a separately reviewed category/rebinding contract from the recording owner.
2. **Detached RecordingBundle before its first training export:** use public
   `export_training(bundle, context)` to assign its initial category, after its
   prerequisite/capability/content/resource checks. The preparation command supports
   this path, links the source bundle/request/calibration IDs, calls public
   `apply_calibration` and validates history/resources via `bind_evaluation`.
   It preserves the immutable raw bundle and creates a new manifest; it does not
   relabel an old manifest. A compatible captured history snapshot and approved
   priors are still required. Warm-up and smoke bundles cannot be promoted to training.

```powershell
# Diagnose an existing unbound policy specification without rewriting its records:
.venv/Scripts/python.exe -m app.game.offline.prepare_calibrated_context build/policy-input.json --calibration build/verifier-costs.json --settings build/calibrated-build-settings.json --output build/calibrated-context-diagnostic.json

# Initial export from a complete detached bundle (context/contract/recording/attacks input):
.venv/Scripts/python.exe -m app.game.offline.prepare_calibrated_context build/collected-context-input.json --collection-bundle build/recording-bundle.json --calibration build/verifier-costs.json --settings build/calibrated-build-settings.json --output build/calibrated-training-inputs.json

$s = Get-Content build/calibrated-build-settings.json -Raw | ConvertFrom-Json
.venv/Scripts/python.exe -m app.game.offline.build build/policy-input.json --calibration build/verifier-costs.json --budget-ms $s.budget_ms --resource-weight-per-ms $s.resource_weight_per_ms --measurement-setup-fingerprint $s.expected_setup_fingerprint --output-dir build/calibrated-policy
```

For initial export, copy `docs/verifier_collected_context.template.json`; supply an
unbound raw context (costs may be omitted), v2 execution contract, recording resource
configuration and attacks. The resulting `context` and `manifest` are supplied in
the complete policy specification by its owner. No final outcome file is opened.
All history/development provenance, partition, readiness and evidence-contract gates
remain active. Existing known evidence/public-coverage defects still block affected
empirical studies; this adapter does not repair or bypass them.

## Explicit settings checklist

- Before collection: custodian permission, grouped roster/reservation, intended
  resources/population, repeat/warm-up run plan and approved warm-up inclusion rule.
- Before calibration: required candidates, inclusion/exclusion choice, same final
  reservation and freeze witness. The old template's `include_warmups=false` is an
  unapproved starting value, not an adopted study decision. Exclusion retains marked
  warm-ups in provenance while fitting costs only to calibration attempts.
- After measured costs are available: review the cost report in **milliseconds**,
  then choose `budget_ms` and `resource_weight_per_ms` (loss per millisecond) and
  approve the evaluated setup fingerprint. No final budget/weight is requested or
  guessed before measurement. Other losses, labels, priors, attacks and study
  settings remain the policy owner's responsibility.

Costs remain estimated sums of verifier-attempt wall times, not money or CPU time.
Parallel request elapsed time can differ from that sum. Synthetic tests produce
no empirical costs. The separately authorized campaign produced calibration only;
it did not fit a policy or integrate the adapter into production request handling.
