# Tanmayee collection and execution handoff

## 1. Scope and status

This handoff describes the implemented engineering interfaces, synthetic validation, recorded test-environment evidence, and the current execution boundary for the bounded research_v1 Development diagnostic.

Vasavi has explicitly approved the bounded Experiment 4 Development diagnostic collection within the existing framework limitations. The setup-bound request at `experiment4-development-diagnostic-setup-bound-request-v1.json` records that approval and structurally validates. This approval does not establish that the current host is suitable, that resources or live services are compatible, or that collection has run. No actual E4 live collection has yet been performed. Synthetic tests and historical test-host results are not live research execution evidence.

## 2. Factory and observer architecture

The offline command flow is:

```text
RecordingRequest.factory
  -> app/game/offline/collect.py::main
  -> configured module:function factory
  -> verifier pool + MeasurementSetup + optional observer
  -> app/game/offline/collection.py::collect
```

The `validate` command parses and structurally validates a request without initializing its factory. The `collect` command checks collection authorization before importing the factory or creating the output directory. Once authorized, it calls the configured zero-argument factory, which returns a verifier pool, setup, and optionally an observer. The collector performs per-example prerequisite planning and invokes the observer during collection.

### Generic path

`app/game/offline/recording_adapters.py::project_factory()` calls `app/benchmark/project_adapter.py::create_verifiers()`. The generic adapter configuration is selected through `VERIFIER_COLLECTION_ADAPTER_CONFIG`. `create_verifiers()` constructs the configured verifier roster eagerly. This generic factory and the root `adapter.json` are not automatically an approved research_v1 binding.

### Research-specific path

`app/game/offline/research_v1_recording_binding.py::research_v1_factory()` is a separate factory entry point. It requires an explicit binding document through `RESEARCH_V1_RECORDING_BINDING_CONFIG`; absent, unreadable, or invalid configuration fails closed. The binding document explicitly names an adapter configuration. There is no implicit fallback to root `adapter.json`.

The research binding creates lazy builders for the nominal roster `semantic`, `evidence`, `rule`, and `confidence`. Reading the pool names does not construct verifiers; a builder is invoked only when the collector requests that verifier after prerequisite planning. Its roster-level observer validates the complete declared setup/resource roster without requiring all verifier instances to exist. Active-instance attestation, when configured, is limited to instances actually constructed by that lazy pool.

**Observer errors do not fail closed before dispatch.** In `collection.py::collect()`, the per-example plan is computed first, then the pre-observation is attempted. Exceptions from `observer.snapshot()` are caught and recorded as `pre_observation:<exception type>:<message>` issues (and post-observation exceptions are recorded similarly). The collector then evaluates the candidate's `eligible` flag and whether its verifier is available in the pool. An eligible, available slot can still call `pool.get()`, invoke `on_start`, and dispatch the verifier after a pre-observation error. A mismatch therefore records an observation issue; it is not a service-compatibility gate that blocks dispatch. The observation issue can prevent a verified measurement from being produced. This behavior does not approve resources or service compatibility, establish runtime readiness, authorize collection, or certify a platform; a non-fatal mismatch must not be interpreted as approval to execute.

The binding's `dataset_id` and `split` fields are declared target metadata. The current factory interface takes no request argument, so those fields are **not validated against the invoking `RecordingRequest`**. The implementation and its synthetic tests do not approve a configuration or establish live readiness.

## 3. Evidence levels and what they establish

The binding separates four kinds of evidence:

1. **Declared configuration** identifies the explicitly selected binding document, adapter configuration, and nominal roster. It does not prove that resource files exist, that a service is available, or that the invoking request matches the binding's declared dataset/split metadata.
2. **Local resource inspection** uses the project adapter's `inspect_setup()` to inspect local model snapshots, corpus/index/receipt files, saved service metadata, and setup identity. It does not load the verifier models or contact the service. Local inspection does not prove current live service compatibility.
3. **Live service observation** compares service metadata with the configured/saved observation. The research observer can perform this when `snapshot()` is called during collection. It can contact the configured service; it is not part of structural request validation and must not be described as a safe static check.
4. **Active-instance attestation** optionally checks actual verifier instances that have already been constructed by the research lazy pool. It does not establish that unconstructed verifiers were loaded or that a collection is authorized.

No current research-specific live observation or active-instance attestation is claimed by this document.

## 4. Environment and dependency evidence

The repository records an isolated **test environment**, not a production lock or runtime certification. `environment.md`, `validation/public-results.json`, and `validation/test-environment.freeze.txt` document Python **3.12.0**, x86_64 Intel macOS, and the test dependency resolution. Recorded versions include PyTorch 2.2.2, NumPy 1.26.4, Transformers 4.48.3, Sentence Transformers 3.4.1, Pydantic 2.14.3, httpx 0.28.1, pytest 9.2.0, FAISS CPU 1.16.0, and psycopg2-binary 2.9.13. The constraints and psycopg2-binary addition are test-environment choices; production requirements were not replaced.

The public validation results explicitly report no live verifiers, models, services, or empirical collection. These recorded versions are not evidence of current live versions on a collection host.

## 5. Filesystem and durability limitations

`filesystem-support.md` describes the recorder's local POSIX filesystem contract: same-directory atomic replacement, hard-link create-if-absent, file fsync and directory fsync; macOS acknowledgments additionally require `F_FULLFSYNC`. Unsupported synchronization fails closed, without a flush-only fallback. The documented test host used temporary directories on local APFS and exercised these interfaces, injected failures, and subprocess exits. These tests do not simulate physical power loss or establish controller/cache guarantees.

Windows/Python 3.10, identified in `filesystem-support.md` as the authentic calibration host, is not supported or certified for this implementation's POSIX directory-sync durability contract. Linux, deployment storage, network filesystems, special container mounts, and the actual future recording location remain unverified unless separately tested. Exactly-once external verifier effects are not established.

## 6. Resource configuration status

`app/benchmark/project_adapter.py::AdapterConfiguration` defines configuration fields for embedding and NLI model snapshots, corpus and evidence index, index receipt, saved service observation, optional relocation binding, Ollama endpoint and model, sampling/temperature/timeout settings, chunk size, and CPU device selection.

The root `adapter.json` is generic configuration. It is not automatically selected or approved for research_v1. No authoritative research-specific resource selection has been established. The responsible runtime/research owners must select and review actual resource paths and identities, model/service details, corpus/index relationship, receipt/metadata, and execution settings. This handoff invents none of those values.

## 7. Commands and authorization boundaries

### SAFE TO RUN NOW

From the repository root, the focused synthetic suite is:

```powershell
.\.venv-test\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_research_v1_recording_binding.py tests/test_diagnostic_collection.py::test_diagnostic_same_collection_without_label_or_custody_claims tests/test_diagnostic_collection.py::test_experiment4_diagnostic_request_enforces_development_roster_and_bounds tests/test_diagnostic_collection.py::test_experiment4_specific_measurement_and_bundle_round_trip_synthetically tests/test_diagnostic_collection.py::test_experiment4_unauthorized_cli_stops_before_factory_initialization tests/test_experiment4_applicability.py tests/test_game_collection.py::test_prerequisites_unavailable_and_abstention_are_distinct
```

This exercises synthetic binding, diagnostic, and prerequisite behavior only; it does not demonstrate live readiness.

The authorized setup-bound Experiment 4 Development request can be structurally validated with:

```powershell
.\.venv-test\Scripts\python.exe -B -m app.game.offline.collect validate docs/research_v1-recording-handoff/experiment4-development-diagnostic-setup-bound-request-v1.json
```

The reported validation result was `valid: true`, with four examples, 16 candidate outcomes, and `factory_initialized: false`. The request has `collection_authorized: true`, `intended_use: "smoke"`, and `study_approval: null`. Structural validity does not establish target-host compatibility, service readiness, or durable recording.

The embedded Final Test exclusion roster is the outcome-free `diagnostic_exclusion_roster_v1` for dataset `research_v1_final_test_v2_exploratory_v1`, with 1,200 entries containing only `example_id`, `split_identity`, `question_id`, `content_identity`, and `validation_id`. Its separate artifact is `evaluation/datasets/final_test_research_v1_eval_v2/diagnostic_exclusion_roster_v1.json` (SHA-256 `69e4ed2197d0f5aaa9a731db8355d7f76384725e8487f4dd0a8c2938ad6627b3`). No Final Test questions, labels, answers, scores, or outcomes were accessed for this preparation.

### STRUCTURAL VALIDATION / EXECUTION BOUNDARY

The request is explicitly setup-bound to the locally inspected Windows/Python 3.10 configuration. The local `inspect_setup()` result established local-input consistency only; it did not establish live service compatibility or platform durability. Windows is unsupported/uncertified for the recorder's documented durability contract. The request must not be run unchanged on macOS or another host.

Before execution on another host, select the target host and filesystem, configure compatible local resources, run the filesystem validation procedure there, inspect the host-specific configuration, and rebind `expected_setup` and `execution_configuration_id` using the existing schema. Then structurally validate the resulting request. Current live service compatibility must be checked when service contact is permitted. These are execution-readiness steps, not a withdrawal of the bounded collection approval.

### AUTHORIZED SCOPE / NOT YET READY TO EXECUTE

The generic collection command form remains a template, not an instruction to run the current Windows-bound request:

```text
python -m app.game.offline.collect collect <approved-request.json> --output-dir <new-run-directory>
```

Collection is authorized only for the bounded Development diagnostic represented by the request. Do not execute it until a supported target platform and storage are designated and validated, the host-specific configuration and request are inspected/rebound and structurally validated, and live service compatibility is checked when permitted. Collection may initialize the configured factory, construct verifiers, contact a service, and write a durable journal. No collection output or live E4 report, failure, abstention, timing, or restart/recovery evidence exists yet.

## 8. Remaining inputs and ownership

| Owner | Required input |
|---|---|
| Vasavi / runtime or research owners | The bounded Development diagnostic collection has been approved. A target recording host/filesystem and host-specific resource configuration still need to be selected and reviewed before execution. |
| Raunak / verifier or dataset owner | Review verifier prerequisites and the protocol-specific question/reference/input treatment and confirm that the configured resources match those requirements. |
| Research lead / custodian | Maintain the approved dataset/population and custody boundary. The outcome-free exclusion roster is embedded in the request; this does not authorize Final Test access, scoring, or label release. No protected Final Test payload was accessed for this handoff. |
| Platform owner / research lead | Designate the recording host and storage, then validate the required filesystem durability behavior on that platform. |

## 9. Current status summary

### Implemented / documented now

- Generic eager factory and separate research-specific lazy binding interfaces exist.
- The research binding requires explicit configuration and preserves the full nominal roster without eagerly constructing it.
- Synthetic tests cover binding and prerequisite behavior. The bounded Development request is authorized and structurally valid, but no actual E4 collection has run.
- Test-environment and macOS/APFS filesystem test evidence are documented with their limits.
- Structural request validation is available without factory initialization.

### Still required before live collection

- A supported target recording platform/storage and host-specific request/resource configuration; collection approval alone does not establish these.
- Current live service/resource compatibility evidence, checked when service contact is permitted.
- A controlled E4 run demonstrating actual reports, failures, abstentions, timings, and restart/recovery behavior; synthetic tests and historical rehearsal records do not supply that evidence.
