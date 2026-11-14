# Tanmayee collection and execution handoff

## 1. Scope and status

This handoff describes the implemented engineering interfaces, synthetic validation, recorded test-environment evidence, and the remaining owner decisions for research_v1 collection preparation.

It does not establish collection authorization, an approved research runtime configuration, live verifier or service compatibility, supported-platform durability certification, or Final Test authorization. The Experiment 4 diagnostic preflight remains unauthorized. Synthetic tests and historical test-host results are not live research execution evidence.

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

Windows/Python 3.10, identified in `filesystem-support.md` as the authentic calibration host, is not supported or certified for this implementation’s POSIX directory-sync durability contract. Linux, deployment storage, network filesystems, special container mounts, and the actual future recording location remain unverified unless separately tested. Exactly-once external verifier effects are not established.

## 6. Resource configuration status

`app/benchmark/project_adapter.py::AdapterConfiguration` defines configuration fields for embedding and NLI model snapshots, corpus and evidence index, index receipt, saved service observation, optional relocation binding, Ollama endpoint and model, sampling/temperature/timeout settings, chunk size, and CPU device selection.

The root `adapter.json` is generic configuration. It is not automatically selected or approved for research_v1. No authoritative research-specific resource selection has been established. The responsible runtime/research owners must select and review actual resource paths and identities, model/service details, corpus/index relationship, receipt/metadata, and execution settings. This handoff invents none of those values.

## 7. Commands and authorization boundaries

### SAFE TO RUN NOW

From a shell with `TEST_PYTHON` set to a prepared compatible test interpreter, the focused synthetic suite can be run with:

```sh
"$TEST_PYTHON" -B -m pytest -p no:cacheprovider tests/test_research_v1_recording_binding.py tests/test_diagnostic_collection.py::test_diagnostic_same_collection_without_label_or_custody_claims tests/test_diagnostic_collection.py::test_experiment4_diagnostic_request_enforces_development_roster_and_bounds tests/test_diagnostic_collection.py::test_experiment4_specific_measurement_and_bundle_round_trip_synthetically tests/test_diagnostic_collection.py::test_experiment4_unauthorized_cli_stops_before_factory_initialization tests/test_experiment4_applicability.py tests/test_game_collection.py::test_prerequisites_unavailable_and_abstention_are_distinct
```

`TEST_PYTHON` must point to an already prepared compatible test environment. The recorded Python 3.12/macOS test profile is separate evidence; that environment is not bundled with this publication branch. These tests exercise synthetic binding, diagnostic, and prerequisite behavior only and do not demonstrate live readiness.

Structural validation is available for a supplied recording request. The `validate` command parses and checks the request structure without initializing its factory; it does not establish factory construction, resource compatibility, service readiness, authorization, or durable recording. A concrete validation command requires an actual request file. This publication branch does not include the previously referenced standalone Experiment 4 diagnostic preflight JSON, so no runnable command using that file is provided here.

### PRE-FLIGHT / STRUCTURAL ONLY

After an owner-reviewed binding and adapter configuration exist, a request may be structurally checked with the `validate` command above. No approved research-specific runtime configuration currently exists. This handoff does not provide a live-resource preflight command: such a command must be defined against the reviewed configuration and its effects before use.

### NOT AUTHORIZED / REQUIRES OWNER APPROVAL

The generic collection command form is:

```text
python -m app.game.offline.collect collect <approved-request.json> --output-dir <new-run-directory>
```

Do not run it until an approved research binding/configuration exists, required resources and service compatibility have been reviewed and validated, a supported recording platform is designated, and explicit collection authorization is granted. No such authorization is established here. Collection may invoke the configured factory and observer, construct verifiers, contact a service, and write a durable journal.

## 8. Remaining inputs and ownership

| Owner | Required input |
|---|---|
| Vasavi / runtime or research owners | Select and review the authoritative research binding and adapter configuration, including the resource identities and execution settings; distinguish implementation authorization from collection authorization. |
| Raunak / verifier or dataset owner | Review verifier prerequisites and the protocol-specific question/reference/input treatment and confirm that the configured resources match those requirements. |
| Research lead / custodian | Decide the approved dataset/population and reference treatment, resolve custody boundaries, and provide explicit collection authorization when appropriate. No Final Test payload is accessed by this handoff. |
| Platform owner / research lead | Designate the recording host and storage, then validate the required filesystem durability behavior on that platform. |

## 9. Current status summary

### Implemented / documented now

- Generic eager factory and separate research-specific lazy binding interfaces exist.
- The research binding requires explicit configuration and preserves the full nominal roster without eagerly constructing it.
- Synthetic tests cover binding and prerequisite behavior; the unauthorized E4 preflight remains unauthorized.
- Test-environment and macOS/APFS filesystem test evidence are documented with their limits.
- Structural request validation is available without factory initialization.

### Still required before live collection

- Owner-reviewed research-specific adapter/resource configuration and protocol treatment.
- Current live resource/service compatibility observation and any required active-instance checks.
- Approved custody and collection authorization.
- Designated, validated recording platform and storage.
- A controlled research run demonstrating actual reports, failures, abstentions, timings, and restart/recovery behavior; synthetic tests do not supply that evidence.
