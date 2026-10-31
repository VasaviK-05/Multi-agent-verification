# Isolated upstream evidence experiments (development only)

This opt-in offline path adds `upstream_evidence_intervention_v1`, distinct from
`report_corruption_v1`. The latter still transforms retained reports and its
public contracts, IDs and behavior are unchanged. The former consumes **fresh
recorded verifier calls** against explicitly altered resources. It never flips
clean reports. Neither contract asserts evidence truth, source trust or independent
corroboration. URLs, verifier names and model agreement do not establish those
properties. No mandatory independent-source guard is introduced.

## What is implemented

`scripts.upstream_evidence_experiment prepare` takes an explicit complete adapter
configuration and a predeclared replacement specification. It validates the clean
corpus hash, unique record IDs and original text hashes before creating a fresh
output directory. It replaces only specified text fields in a separate JSON
corpus, preserves other fields, and produces a separate adapter and preparation
receipt. It does not build an index, run a verifier, read labels or alter the
source corpus/index. Its input format is a JSON list of string `id`/`text` records;
other corpus formats need an explicitly reviewed adapter.

`app.game.offline.upstream` validates the collected experiment:

- The clean `RecordingBundle` is exported through existing training contracts.
  Existing history-only reputation, metadata-only reservation, split, eligibility,
  task-history and resource checks apply. Use a fresh unbound base-objective
  context with the original approved settings and clean history statistics.
  Empirical inputs additionally require `clean_build_specification`: the existing
  `PolicyBuildSpecification` with the exact clean training manifest, bound context,
  execution contract and report-attack settings. Existing `check_readiness` must
  pass against the recorded code revision. Empirical fitting requires the actual
  current code revision explicitly; the approved optimizer tolerance is retained.
  Evidence-bearing empirical scenarios also require the existing seven-probe
  `EvidenceValidation` bound to their altered resources. A clean-resource proof
  cannot be reused as an altered-resource proof. None of these proofs is an
  independent-source or evidence-truth guard.
- Every intervention declares its corpus resource ID, alteration, scope,
  provenance, clean/altered manifests, affected verifier entries, request ID,
  timing/knowledge and a scenario-specific cache attestation. Observed logical
  resource IDs stay constant; altered content has different fingerprints.
- Changed corpus consumers with an index must have a changed, separately observed
  index. Algorithm/model/prompt/service changes and undeclared extra corpora are
  rejected. Changed configuration hashes require explicit project adapter JSONs,
  verified against their actual fingerprint formula. Only corpus/index/receipt/
  service-observation paths may differ; scientific and sampling settings stay equal.
  Generic experimental adapters with different configuration fingerprint contracts
  need a separately reviewed extension; unknown hashes are not accepted as proof.
- The real project adapter fingerprints corpus/index locations in **all four**
  verifier configurations. Declare all changed entries, including configuration-
  only changes. This does not mean all four verifiers consume poisoned evidence.
  Every configuration entry is checked against the supplied project configurations;
  a shared path change cannot be hidden by declaring one entry unaffected.
- Each scenario recollects the **entire candidate roster** for every clean
  development example, with distinct execution IDs. It retains complete reports,
  failures, timings, pre/post observations and capability audits through the existing
  collector. Partial, missing, smoke/diagnostic, cross-split, relabelled, changed
  reference/planning, unknown-resource and changed-environment bundles are rejected.
  No clean outcome is substituted for an absent scenario outcome.
  This version does **not** reuse even demonstrably unaffected clean reports;
  all scenario outcomes are recorded separately. Unexecuted outcomes may only
  represent explicit prerequisite/factory unavailability with a retained reason.
  A returned report marked unexecuted is rejected. Declared call failures and
  unavailability remain diagnostics and still reach the ordinary uncertainty guards.
- History and independent correctness labels are unchanged. Altered collection
  requests contain development examples only. Final-test records are neither
  collected nor loaded; only the existing reservation metadata is carried forward.

The supported attacker commits a fixed resource intervention before collection
and before the verifier team is sampled. It may know public questions, references
and clean resources; it must not know independent labels or the realized team.
The adversary may know the policy distribution. These are explicit study/custody
obligations, not filesystem access control or proof that an external producer was
honest. There is no final-test or adaptive-team attack interface in this version.

### Team reuse and fitting

`complete_team_independent_v1` alone is insufficient authorization for cross-team
reuse under a changed resource. The new declaration requires
`complete_team_independent_within_fixed_scenario_v1` and an explicit attestation
of fixed resources, controlled randomness, no team/prefix/order dependence and
no adaptive mutations. Collection still uses the established complete-team
recorder, but reuse is limited to that exact scenario and request. A stateful or
team-dependent adapter cannot use this path without a different recording
contract. Reuse is an assumption to audit, not inferred independence.

Payoffs replay each complete scenario through the existing public finalizer with
its **altered** execution contract. Clean deployment guards are not bypassed: the
experimental replay context is temporary and never exported for deployment.
Columns include the existing clean/report-corruption actions plus each declared
upstream scenario. Poisoning and report corruption are not implicitly composed.
The existing minimax solver, certificate validator, exact strategy enumeration,
minimum contributors, coverage, uncertainty, failure and hard budget rules apply.
Every feasible team and both aggregations remain, including zero probabilities.
Pooling, coverage-constrained and reliability-first objective variants are
explicitly rejected here pending separate contracts; they are not silently dropped.

The fitted artifact keeps the existing decision/solver semantics and format. Its
provenance names the new combined scenario-set digest; its offline binding also
binds the exact experiment. The versioned `fit.json` sidecar contains the full
experiment and validates reconstructed payoffs plus the ordinary artifact and
numerical certificate on reload. Deploying `policy.json` means **clean resource
compatibility only**. An altered corpus is incompatible with that deployment
episode even if it was evaluated experimentally. Numerical validation is not an
attestation of evidence truth or the producer's resource observations.
At runtime, an altered pre-dispatch resource observation produces uncertainty
with `provenance_incompatible` and no verifier dispatch. Drift detected after
dispatch also forces uncertainty under the existing resource-provenance guard.

Scientific identities exclude measured durations but retain outputs, request IDs,
code/environment versions and resource observations. Full raw timings remain in
the audit sidecar. Costs and budgets use the supplied frozen **clean estimated
attempt costs**; altered timings do not recalibrate them. These are neither money
nor latency guarantees. `development.json` separates validation loss from the
cost-inclusive `mean_loss` objective, with per-strategy and policy-weighted coverage,
uncertainty, errors and worst-case scenario. Solver/environment versions are recorded.

## Later bounded real experiment (not executed or approved here)

Use a fresh `build/` experiment directory and installed resources only. Do not
reuse historical artifacts as measurements for changed implementation/resources.
Both clean and altered collection must share one code/environment setup. Obtain
approval for exact task groups, development-only scope, predeclared replacements,
scenario count, candidate roster, costs/loss/budget/dependency settings, seed controls
and maximum calls. Let H/D be approved history/development example counts, V the
candidate count and K fixed interventions. A new complete clean campaign plus
altered development collection contains **V × (H + D + K × D)** candidate outcomes
(actual verifier calls depend on legitimate prerequisite eligibility). Do not retry
attempted failures; use the collector's journal/resume mechanism unchanged.

The safe template `docs/upstream_corpus_alterations.template.json` is deliberately
invalid until its hash/text placeholders are replaced with reviewed real inputs.
Keep completed configurations, labels, receipts, model paths and recordings private.

Preparation commands (only preparation and retained-record validation are inference-free):

```powershell
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment prepare --clean-adapter CLEAN_ADAPTER.json --alterations REVIEWED_ALTERATIONS.json --output-dir build/UPSTREAM_NEW/altered
# Later authorization required: this performs local embedding work.
.venv/Scripts/python.exe -m app.benchmark.project_adapter prepare-index build/UPSTREAM_NEW/altered/adapter.json --output build/UPSTREAM_NEW/altered/index-receipt.json
# Later resource owner supplies/observes compatible local service metadata.
.venv/Scripts/python.exe -m app.benchmark.project_adapter observe-service build/UPSTREAM_NEW/altered/adapter.json --output build/UPSTREAM_NEW/altered/service-observation.json
```

The resource/collection owner must run the existing `inspect_setup` contract on
both configurations and review readiness before constructing requests. Use
`create_recording_verifiers` / the existing resource observer; do not instantiate
teammate retrievers with an unbuilt/stale index. No retrieval/verifier fix is
required by the synthetic implementation, but real index provenance, live observer
readiness and actual Evidence behavior remain unverified in this extension. The
existing resource-bound controlled/real-NLI validation must be supplied for each
empirical Evidence resource setup; this publication does not run those probes.

Construct the scenario request without changing labels or grouping:

```python
import json
from pathlib import Path
from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup
from app.game.offline.calibration import read_json
from app.game.offline.upstream import scenario_request, EvidenceIntervention
clean_config = AdapterConfiguration.model_validate(read_json('CLEAN_ADAPTER.json'))
altered_config = AdapterConfiguration.model_validate(read_json('build/UPSTREAM_NEW/altered/adapter.json'))
# Hashes installed files/saved metadata; no model loading or inference.
clean_report, altered_report = inspect_setup(clean_config), inspect_setup(altered_config)
assert clean_report['ready'], clean_report['blockers']
assert altered_report['ready'], altered_report['blockers']
request = scenario_request(read_json('CLEAN_REQUEST.json'),
    altered_report['observed_setup'], name='REVIEWED_SCENARIO_NAME',
    preparation_authorization='NEW_EXTERNAL_AUTHORIZATION_RECORD',
    study_approval='NEW_EXTERNAL_STUDY_APPROVAL_RECORD')
receipt = read_json('build/UPSTREAM_NEW/altered/intervention-preparation.json')
clean_resources = clean_report['observed_setup']['resources']
altered_resources = altered_report['observed_setup']['resources']
before = {v['verifier_name']: v for v in clean_resources['verifiers']}
changed_entries = tuple(v['verifier_name'] for v in altered_resources['verifiers']
                        if v != before[v['verifier_name']])
declaration = EvidenceIntervention(
    version='upstream_evidence_intervention_v1', name='REVIEWED_SCENARIO_NAME',
    affected_resource='evidence-corpus', alteration=json.dumps(receipt['specification']),
    scope=receipt['specification']['scope'],
    provenance='EXTERNAL_AUTHORIZATION_RECORD; specification_id='+receipt['specification_id'],
    clean_resources=clean_resources, altered_resources=altered_resources,
    affected_verifiers=changed_entries, request_id=request.request_id,
    timing=receipt['specification']['timing'], knowledge=receipt['specification']['knowledge'],
    reuse_contract='complete_team_independent_within_fixed_scenario_v1',
    reuse_attestation='EXTERNAL_OWNER_FIXED_SCENARIO_REUSE_ATTESTATION_RECORD',
    clean_adapter_json=clean_config.model_dump_json(), altered_adapter_json=altered_config.model_dump_json())
with open('ALTERED_REQUEST.json', 'x', encoding='utf-8') as f:
    f.write(request.model_dump_json(indent=2))
with open('DECLARATION.json', 'x', encoding='utf-8') as f:
    f.write(declaration.model_dump_json(indent=2))
```

Before collection, construct and validate an `EvidenceIntervention` with all
fields listed above, its `request_id=request.request_id`, both **actual observed**
resource manifests, and explicit clean/altered adapter JSON. Use the preparation
receipt/specification digest in `provenance` and the exact replacements in
`alteration`; archive the declaration before any calls. Obtain the resource owner's
scenario reuse attestation. Do not derive it from favorable verifier outcomes.
`EvidenceIntervention.model_json_schema()` and
`UpstreamExperiment.model_json_schema()` give the exact machine-readable contracts.
The example above uses the project adapter's actual logical corpus ID; a different
adapter must supply its observed ID rather than copying that name blindly. Replace
all external authority/attestation placeholders with actual reviewed records.

After approval, bounded collection uses the existing collector, not a new framework:

```powershell
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG='build/UPSTREAM_NEW/altered/adapter.json'
.venv/Scripts/python.exe -m app.game.offline.collect validate ALTERED_REQUEST.json
.venv/Scripts/python.exe -m app.game.offline.collect collect ALTERED_REQUEST.json --output-dir build/UPSTREAM_NEW/altered-recordings
.venv/Scripts/python.exe -m app.game.offline.collect check build/UPSTREAM_NEW/altered-recordings
# No inference below. Supply the clean unbound calibrated context and contract.
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment assemble --clean-bundle CLEAN_RECORDINGS_DIR --context CLEAN_CONTEXT.json --contract CLEAN_CONTRACT.json --report-attacks REPORT_ATTACKS.json --clean-build-specification READY_CLEAN_BUILD_SPECIFICATION.json --scenario DECLARATION.json build/UPSTREAM_NEW/altered-recordings --scenario-evidence-validation DECLARATION.json ALTERED_EVIDENCE_VALIDATION.json --output build/UPSTREAM_NEW/experiment.json
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment validate --experiment build/UPSTREAM_NEW/experiment.json
.venv/Scripts/python.exe -m scripts.upstream_evidence_experiment fit --experiment build/UPSTREAM_NEW/experiment.json --code-revision ACTUAL_CURRENT_GIT_SHA --output-dir build/UPSTREAM_NEW/fit
```

Repeat `--scenario DECLARATION RECORDINGS` for each predeclared scenario. Use a
clean configuration for clean collection; never overwrite its adapter or paths.
Any real collection, empirical fit or publication remains a separate approved run.
The two readiness options may be omitted for explicitly synthetic fixtures; they
are not an empirical bypass. Repeat `--scenario-evidence-validation` for each
Evidence-bearing scenario, keyed by its declaration path. Duplicate/unknown proof
assignments reject. The assembly command never initializes verifiers.

### Ownership handoff

- Study owner: approve the exact scenario set, altered text, task groups, authority
  records, independent labels, loss/resource settings, dependency assumptions,
  maximum calls and timing/knowledge limitations **before** examining outcomes.
  Earlier prototype settings are not approval of this experiment.
- Dataset custodian: supply grouped labelled history/development requests and the
  metadata-only final-test reservation. Keep independent labels unavailable to the
  attacker producer and final-test payloads inaccessible to every fitting command.
- Resource/Evidence owner: supply installed model snapshots, clean/altered corpus
  and isolated index receipts, live observations, configuration payloads, the
  resource-bound Evidence contract validations and the scenario reuse attestation.
  No teammate algorithm repair is inferred or requested by synthetic test results.
- Collection owner: execute only the approved bounded requests through the existing
  factory/observer, preserving all attempts, failures and ledgers. Resume only
  supported unattempted work, never retry recorded failures or overwrite outputs.
- Offline policy owner: supply the already approved calibrated clean costs and
  ready clean build specification, assemble/validate, then fit the explicitly
  supported ordinary unpooled minimax objective with the approved tolerance.
  Clean-coverage, reliability-first and pooling settings must not be stripped to
  make this fitter accept them; those objective variants need a separate extension.
- Integration owner: reload the full `UpstreamFit` sidecar for experiment audit,
  register only its validated clean-resource `PolicyArtifact` with a compatible
  clean deployment episode and live observer. Activation/API integration is outside
  this extension. Models, corpus, labels and real study data are not published here.

## Validation and limits

Synthetic regression command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_upstream_evidence.py tests/test_game_collection.py tests/test_game_offline.py tests/test_game_build.py tests/test_game_runtime.py tests/test_game_prototype_bundle.py tests/test_game_foundation.py tests/test_game_task_conditioning.py tests/test_game_research.py -q
```

These fixtures exercise identity rejection, independently preserved labels,
collector-to-matrix-to-fit/export/reload, certificates, shared finalization and
the real runtime's rejection of experimental resources. They are software checks,
not empirical security evidence. Real scenario collection and evidence-owner
resource/reuse validation remain pending. The completed prototype and historical
arithmetic/factual findings are unchanged. Report-level robustness and numerical
certificates do not establish evidence truth, poisoning immunity, independence,
held-out superiority or efficiency improvement.
