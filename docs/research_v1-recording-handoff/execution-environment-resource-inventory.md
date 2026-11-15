# Item 4: Execution environment and resource inventory

## 1. Scope and evidence boundary

This document consolidates existing repository evidence for Vasavi's Item 4. It does not select or approve a runtime configuration, establish current runtime readiness or live service compatibility, authorize collection, or designate a supported recording platform. Environment and resource facts below are kept separate by their evidence status; historical and generic values are not promoted to a current research configuration.

No factory, verifier, model, service, or collection path was initialized to prepare this inventory.

## 2. Execution environment inventory

| Evidence | Exact value | Status | Interpretation / limitation |
|---|---|---|---|
| Integration checkout | Branch `tanmayee-integration`, HEAD `0d4c0fbd5419172262e356d30e1691a9baba9cb1` | CURRENTLY OBSERVED | This inspection checkout has pre-existing dirty and untracked paths; this is not a clean release identity. |
| Published Experiment 4 checkout | Branch `tanmayee-experiment4-publication-96abae7`, HEAD `aca6314ab3ad00e8311c15e490e78d66f477e845` | CURRENTLY OBSERVED | Separate publication worktree; it is not the integration checkout. The standalone E4 preflight JSON cited below is absent there. |
| Current host/interpreters | 64-bit Windows (`10.0.26200.0`); system Python `3.10.0`; local `.venv-test` Python `3.10.0` | CURRENTLY OBSERVED | Windows/Python 3.10 is **not supported or certified for this repository's POSIX directory-sync durability contract**. No current production dependency freeze is established for this host. |
| Recorded test host | Python `3.12.0`, x86_64 Intel macOS, local APFS | TEST ENVIRONMENT | Recorded in `validation/public-results.json` and `filesystem-support.md`; limited to the documented engineering tests. It is not a current collection host or production certification. |
| Test dependency freeze | PyTorch `2.2.2`; NumPy `1.26.4`; Transformers `4.48.3`; Sentence Transformers `3.4.1`; Pydantic `2.14.3`; httpx `0.28.1`; pytest `9.2.0`; FAISS CPU `1.16.0`; psycopg2-binary `2.9.13` | TEST ENVIRONMENT | `validation/test-environment.freeze.txt`; an isolated test resolution, not a production lock. |
| Current app source digest | `466fe5fedaca4436a14cbbf756d4fc9486696f824308151c519de198680258f2`, calculated over 140 sorted `app/**/*.py` relative-path/file-SHA pairs using `app.game.models.content_id` semantics | CURRENTLY OBSERVED | Read-only snapshot of the integration checkout's app bytes at this inspection. It is not an approved runtime identity or a stable identifier for future source states; recompute it after application-source changes. |
| Older E4 candidate/proposal digest | `46b00b691ea201e2d99d35882b9fdaa54133d235f565c0271ae3975592336063` | HISTORICAL / STALE | Recorded against an earlier working-tree state and earlier repository identity; do not use as the current app digest. |
| Historical rehearsal source | Revision `662bd5cdbf2c8b2dc9885f6bb80e42abf7c5205e`; app digest `ecb12d8934a3d55dd745887ecf9b3c164ea308f3b07eaa895a6d69f246e87e6c` | HISTORICAL | From `source-resource-summary.json`; describes historical rehearsal/calibration lineage, not current source. |
| Filesystem contract and validation | Local POSIX primitives; macOS acknowledgments require `F_FULLFSYNC`; tests used local APFS | TEST ENVIRONMENT | Windows is not certified. Linux/deployment storage, network filesystems, special mounts, physical power loss, and the future recording location remain unverified. |
| Current storage type | Exact filesystem/device for a future recording location | UNKNOWN / UNVERIFIED | The current Windows checkout location does not establish the filesystem durability behavior of any approved recording destination. |

`environment.md` documents an isolated test setup, and `public-results.json` reports 115 local validation cases plus 11 policy regressions, including 27 filesystem tests. The results explicitly state that there was no live verifier/model/service or empirical collection and that Windows, deployment storage, physical power loss, and exactly-once external effects were unverified.

## 3. Resource configuration inventory

The root `adapter.json` is a generic `project_collection_adapter_v1` configuration, not an approved research configuration. The earlier inventory recorded its declared paths and historical identities; a subsequent local-only inspection adds point-in-time observations below without changing that approval status.

### Subsequent local-only inspection

The candidate binding was supplied explicitly to `resolve_research_configuration()` from the integration checkout (`tanmayee-integration`, HEAD `0d4c0fbd5419172262e356d30e1691a9baba9cb1`). Its relative adapter path resolved to the repository-root `adapter.json`. The candidate was supplied for inspection only; it was not activated for collection.

`inspect_setup()` returned `ready: true`, no blockers, and `ready_scope: "local inputs only; saved service observation is revalidated live by factory"`. Here, `ready: true` means no blockers were collected for the local checks that ran. The inspection read and hashed local model snapshots, corpus, and index files; it read and checked receipt/manifest metadata and parsed the relocation binding and saved service-observation JSON. It did not load model weights into model objects or contact a service.

| Local input | Observation from that inspection |
|---|---|
| Embedding snapshot | 11 files, 91,578,415 bytes; SHA-256 `23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255`. This matches the hash previously listed as historical. |
| NLI snapshot | 7 files, 578,729,785 bytes; SHA-256 `a28c08014f62b13be758a1f22d1cbfd30e9f7b0f91d19fbc3bd5c369b11fcf7e`. This matches the hash previously listed as historical. |
| Corpus | 9,206 bytes; SHA-256 `28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a`. This matches the hash previously listed as historical. |
| Index files | `faiss.index`: `5bc44bf0f694d4ffd08b7d5a51191cd953a784d98f9041bd0b52867d42f7c287`; `chunks.json`: `bce84c9632b231d0611da47d133c1bb444f2189f0b6ed1701fdbda3929dcec33`; `manifest.json`: `651ce5709b186670806d9319e7f4e73911a628d7eb175bee10f63ac5555fb92e`. The derived evidence-index fingerprint was `a09afd412b9549f5c89d421eed246324eb41884d62a7d44181a8cff74b417f98`, matching the previously listed historical fingerprint. |
| Receipt and manifest | The inspection reported no blockers after checking the receipt against locally derived embedding, corpus, index/chunk hashes and configured chunk size, and checking the manifest against expected local metadata. |
| Saved service observation | The local JSON passed schema and configured URL/model checks. It records alias `llama3.2:3b`, digest `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`, and server version `0.40.11`. This is stored metadata, not a live observation. |

The resulting setup fingerprint was `27b7327bfd5bb58125596dd27b0a77aad70e981774cd5d21a1e95a26ceac65a8`; the report recorded code revision `0d4c0fbd5419172262e356d30e1691a9baba9cb1` and application-source digest `466fe5fedaca4436a14cbbf756d4fc9486696f824308151c519de198680258f2`. These are point-in-time identities for the inspected integration checkout and must not be attributed automatically to the separate publication branch.

`inspect_setup()` reported `ready: true` with no blockers after checking the index manifest and receipt against local corpus, index, and model hashes. The prior printed summary did not include `relocation_audit`, so it does not establish whether the relocation-mapping branch was exercised or provide its detailed validation result.

The inspection does not establish research approval, resource approval, current live service compatibility, executable runtime readiness, supported-platform durability, or collection authorization. The saved service observation would require a separate live path such as `observe_service()` to compare against a current service; that function was not called. The candidate was supplied explicitly to the resolver for inspection; this task did not set `RESEARCH_V1_RECORDING_BINDING_CONFIG`.

### Current service-observation preflight

**Currently observed:** An OS-level listener check found no TCP listener on port `11434` at the time checked. No HTTP request was sent. Therefore, no current Ollama version, model digest, or live API compatibility was observed. This is a point-in-time listener result; it does not show that Ollama cannot be started later or that another approved runtime cannot provide the service.

**Code-derived behavior:** The configured initial URL is `http://localhost:11434/api/generate` (local/loopback); `observe_service()` derives `http://localhost:11434` and would send GET requests to `/api/version` and `/api/tags`. It does not start the service, load models, construct verifiers, initialize the research factory, or start collection. The Requests GET calls follow redirects by default, and `observe_service()` does not revalidate redirect destinations. `trust_env=False` disables environment proxy inheritance.

The saved `service-observation.json` remains stored metadata, not a current observation. Local consistency from `inspect_setup()` does not substitute for current live service compatibility. No configuration was activated and no collection authorization is implied. **Classification: NOT READY — no local listener observed.**

| Resource | Exact value or identity evidenced | Evidence source and classification | Current research configuration? |
|---|---|---|---|
| Semantic verifier | `semantic_v1`; requires a nonblank reference; generic binding uses the configured embedding snapshot. Historical implementation SHA-256 `cddd1bf8b3b8de71453647ff5d58ef65acc5ff18a7c643b216edff3cb8cda2a6` | Adapter/code declaration plus HISTORICAL source-resource summary | No |
| Evidence verifier | `evidence_v1`; generic corpus/index/receipt paths are listed below. Historical implementation SHA-256 `5903359855c9fef4e92584643aceb8b4c494835907aaaa5106fa80c45b58119e` | Adapter/code declaration plus HISTORICAL identity | No |
| Rule verifier | `rule_v1`; no model resource is declared for it by `AdapterConfiguration`. Historical implementation SHA-256 `7522a6bcffe4234e3e0a23e0a944a197f831b7a496f905b049ffed552afd907d` | Adapter/code declaration plus HISTORICAL identity | No |
| Confidence verifier | `confidence_v1`; generic settings include `n_samples=5`, temperature `0.8`, timeout `60.0`. Historical implementation SHA-256 `1492ddd2562e338a8a1a84dc8edc01ffd997ae1701ab436bc2fec0613e3683f6` | Generic declaration plus HISTORICAL identity/settings | No |
| Embedding model | Generic path `C:/Users/User/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; path existed. Historical snapshot SHA-256 `23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255` | `adapter.json` DECLARED path; source-resource summary HISTORICAL hash | No |
| NLI model | Generic path `C:/Users/User/.cache/huggingface/hub/models--cross-encoder--nli-deberta-v3-small/snapshots/fa2804872c3b4bd748f38c0185cc85775361e735`; path existed. Historical snapshot SHA-256 `a28c08014f62b13be758a1f22d1cbfd30e9f7b0f91d19fbc3bd5c369b11fcf7e` | `adapter.json` DECLARED path; source-resource summary HISTORICAL hash | No |
| Ollama endpoint/model | `http://localhost:11434/api/generate`; alias `llama3.2:3b` | `adapter.json` DECLARED generic values; no endpoint contact made | No |
| Saved service observation | `build/multitask-policy42/service-observation.json`; saved server version `0.40.11`, alias `llama3.2:3b`, model digest `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`. Historical service-resource SHA-256 `bd8df84f5b911a5ced6db9e39942b8dc16e63eea8a9e543d5d2ec5cc44295aa1` | Stored observation and HISTORICAL resource summary; not a current observation | No |
| Prompt/configuration identities | Historical self-consistency prompt SHA-256 `dc09c40fa96b3410833dd681cd674806dbffc8301db4c5890a5b3043b86b868b`; historical adapter-configuration SHA-256 `f638ac090bffc9b348bca8b6c9660ab107e3d15870a237a901273ddb7bc46aa0` | HISTORICAL source-resource summary; the generic adapter schema does not supply an approved research prompt identity | No |
| Evidence corpus | `build\multitask-policy42\corpus.json`; path existed. Historical corpus SHA-256 `28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a` | Generic DECLARED path; HISTORICAL hash | No |
| FAISS/index resources | `build\multitask-policy42\index-v2`; path existed. Historical index SHA-256 `a09afd412b9549f5c89d421eed246324eb41884d62a7d44181a8cff74b417f98` | Generic DECLARED path; HISTORICAL hash | No |
| Index receipt/build evidence | `build\multitask-policy42\index-receipt.json`; path existed. `AdapterConfiguration` also declares `chunk_size=500` and `device="cpu"`. | Generic DECLARED path/settings; no fresh receipt/index validation in this task | No |
| Other generic adapter fields | `resource_relocation_binding`: `build/multitask-policy42/resource-relocation-v2.json` (present); Ollama sampling, timeout and chunk settings as above | `adapter.json` DECLARED generic configuration | No |
| Historical full-roster provenance | Resource manifest ID `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c`; setup fingerprint `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee`; historical app revision/digest as in Section 2 | `source-resource-summary.json`, marked historical evidence only | No |
| Static candidate setup | Candidate manifest ID `898af00e993768ab1d2d320a4cd2d743187ccb475979a39072c1bc8deabf96d7`; candidate setup fingerprint `0fa90ad646008b9ca2f16b9d03d37fe4dc1e5b005828109059a121d4c7d59ca3` | E4 candidate assessment: `CANDIDATE_STATICALLY_COMPATIBLE_PENDING_LIVE_VALIDATION`; generic root adapter not selected/approved; `live_checked=false` | No |
| Research-specific binding | Candidate was explicitly supplied to `resolve_research_configuration()` for the local inspection only; it was not activated for collection. Earlier inventory recorded the environment variable as unset; this task did not set it. The proposal remains `PROPOSED_NOT_APPROVED_NOT_EXECUTABLE`; collection authorization is false and freeze ID null. | CURRENTLY OBSERVED inspection input plus DECLARED / PROPOSED artifact status | No |

These identities answer what was recorded in generic or historical artifacts. They do not assert that the snapshot paths' present bytes, the corpus/index relationship, the saved service observation, or the verifier instances match an approved research runtime.

## 4. Commands and execution status

### SAFE STRUCTURAL / SYNTHETIC CHECKS

The following paths were verified in the **integration checkout**: `.venv-test/Scripts/python.exe`, the listed test files, and the standalone E4 preflight request.

Focused synthetic tests, from the integration checkout root:

```powershell
.\.venv-test\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_research_v1_recording_binding.py tests/test_diagnostic_collection.py::test_diagnostic_same_collection_without_label_or_custody_claims tests/test_diagnostic_collection.py::test_experiment4_diagnostic_request_enforces_development_roster_and_bounds tests/test_diagnostic_collection.py::test_experiment4_specific_measurement_and_bundle_round_trip_synthetically tests/test_diagnostic_collection.py::test_experiment4_unauthorized_cli_stops_before_factory_initialization tests/test_experiment4_applicability.py tests/test_game_collection.py::test_prerequisites_unavailable_and_abstention_are_distinct
```

The pytest command exercises collector logic in synthetic tests using fake verifiers; it does not perform a live or authorized research collection, initialize the production request factory, contact services, or load production models. The separate `validate` command performs request-structure validation only and does not initialize the request factory. Passing the tests does not establish live readiness.

Structural validation, also from the integration checkout root:

```powershell
.\.venv-test\Scripts\python.exe -B -m app.game.offline.collect validate docs/research_v1-recording-handoff/experiment4-development-diagnostic-preflight-request-v1.json
```

The request file exists in the integration checkout and has `collection_authorized: false`. The standalone request file is absent from the published Experiment 4 worktree, so this exact command is not available from that checkout. Structural validity is not runtime readiness or authorization.

### REQUIRES A PREPARED ENVIRONMENT

The documentation uses `TEST_PYTHON` for a separately prepared compatible test interpreter. For example, in a POSIX shell from the repository root:

```sh
"$TEST_PYTHON" -B -m pytest -p no:cacheprovider tests/test_research_v1_recording_binding.py
```

`TEST_PYTHON` must point to a prepared test environment. The published branch does not bundle the recorded Python 3.12/macOS test environment or its package installation. Its freeze file is evidence about that test resolution, not an included environment and not a production lock.

### NOT AUTHORIZED / BLOCKED

The collection CLI form is only a template:

```text
python -m app.game.offline.collect collect <approved-request.json> --output-dir <new-run-directory>
```

It is not an approved runnable instruction. Before collection, the project needs a reviewed/approved research binding and resource configuration, appropriate current resource/service compatibility evidence, a designated supported recording platform, and explicit collection authorization. Those prerequisites are not established here. Collection can initialize a factory, construct verifiers, contact a configured service, and write a durable journal.

## 5. What is exact today vs what is missing

### Exact, documentable facts available now

- Separate integration and published branch identities, with their observed HEADs.
- Current Windows/Python 3.10 host details and a time-specific app-source digest, with no durability certification implied.
- The separate Python 3.12/macOS/APFS test profile and its recorded dependency freeze.
- Generic adapter fields and paths, explicitly classified as generic declarations.
- Historical resource, setup, calibration, and service identities, explicitly classified as historical.
- Existing synthetic test and structural validation commands and their checkout/input requirements.
- The research-binding configuration entry point and the fact that no binding is selected in the inspected shell.

### Missing decisions/evidence

- An owner-reviewed and approved research-specific binding/resource configuration.
- Current verification of the resource bytes and evidence corpus/index relationship under that selected configuration.
- Current live service/model observation and any required active-instance attestation.
- A supported recording platform/storage designation and validation there.
- Protocol/reference/input decisions where they affect verifier compatibility.
- Explicit collection authorization.

## 6. Authority and ownership boundaries

### Tanmayee can document/validate independently

Consolidate existing environment, source identity, generic configuration, historical provenance, and safe command evidence. Run synthetic or structural checks only when their stated files and prepared test interpreter are available. This document does not change the framework.

### Needs Vasavi/runtime-owner decision

Select/review the binding and runtime configuration, identify the intended execution host and storage, and designate the supported recording platform. Collection authorization must also be granted by the responsible project authority before any collection.

### Needs Raunak/research-lead decision

Resolve research protocol choices such as verifier applicability, reference/input treatment, and whether the candidate resources are appropriate to the research protocol.

### Needs custodian authorization

Custodian authorization is **not required for this Development-only, non-protected evidence documentation task**. It is required if future work accesses or releases protected Final Test labels, answers, scoring, or other protected evaluation payloads; none were accessed for this inventory.

## 7. Bottom-line status

The repository now has exact evidence describing available environments, generic configuration, historical resource identities, and safe structural checks, but it does not yet have an approved current research runtime configuration or authorization for collection.
