# Resource Manifest Field Map

## Purpose and status

This document is a Person 2 preparation and handoff crosswalk between research-level requirements and the repository's runtime resource, setup, execution, and measurement contracts. It is not a canonical `ResourceManifest`, a replacement for the repository schemas, or a host attestation. Use [`app/game/resource_provenance.py`](../../app/game/resource_provenance.py), [`evaluation/docs/runtime_configuration.md`](runtime_configuration.md), and [`evaluation/docs/cost_measurement_protocol.md`](cost_measurement_protocol.md) for the authoritative runtime and measurement contracts.

It separates the completed Development-only direct-verifier cost calibration from the broader research/runtime configuration and later policy work. A verified resource identity for a specific pilot does not by itself establish compatibility for a different game policy, workload, host, or evaluation stage.

Status labels used below:

- **VERIFIED / FROZEN** — validated for the specifically named Development cost-calibration bundle. This does not imply global or Final Test approval.
- **AVAILABLE / OWNER-DEFINED** — dataset or protocol material is present or designated, while remaining owner decisions and limitations are stated explicitly.
- **PENDING FROM PERSON 1** — benchmark, dataset, partition, label, or corpus decisions that belong to the research protocol/data owner.
- **PENDING FROM PERSON 3** — experimental policies, matched baselines, strategy, and reproducibility decisions.
- **PERSON 2 FOLLOW-UP** — runtime/resource compatibility checks or measurements for a later, explicitly approved configuration.

## Completed Development-only cost-calibration freeze

The bounded `research_v1` Development direct-verifier cost calibration is complete and frozen as a versioned research input. The bundle is at [`artifacts/research-v1-development-cost-calibration-v1/`](../../artifacts/research-v1-development-cost-calibration-v1/) in commit `f71ddca323fea1ee60bf88ed87eef06d1901024d`.

| Identity or setting | Frozen value |
|---|---|
| Calibration artifact | `artifacts/research-v1-development-cost-calibration-v1/calibration.json` |
| Calibration artifact ID | `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` |
| Calibration SHA-256 | `7fbfe418c0c65c3782628ab5117b773f2fc4c8312c33d769934f76d2ff61a7f3` |
| Calibration input digest | `543991e00c2c3d19b31f30d226167021a22a27d78cf6c3d0cab3645e9ebed629` |
| Measurement SHA-256 | `514e39a1422a1ef0b3846e02f010e6edc4ab1a1aec89e1605e82f03199836a94` |
| Calibration method / units | `mean_attempt_wall_time_ms_v1` / milliseconds |
| Warm-up handling | `include_warmups=false`; 8 warm-up attempts excluded, 480 calibration attempts eligible |
| Collection identity | dataset `research_v1_exploratory_v1`; permitted pair `("development", "research_v1_exploratory_v1")` |
| Required verifier roster | `semantic`, `evidence`, `rule`, `confidence` |
| Resource manifest ID | `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c` |
| Setup fingerprint | `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee` |
| Confidence configuration | `llama3.2:3b`, `n_samples=5` |

The bundle preserves `measurements.json`, `calibration.json`, the calibration-input provenance record, and a freeze manifest. The calibration artifact is accessible to a compatible Development-stage policy build by supplying its path with the builder's `--calibration` argument; the builder independently checks setup/resource compatibility. Path availability does not assert that a policy specification is ready or that policy fitting has occurred.

**Freeze boundary:** this is a Development-only cost-calibration freeze. It is **not** a full or global research freeze, does **not** authorize Final Test access or execution, and does **not** complete policy fitting or budget selection.

## Research-level field crosswalk

The runtime `game_resource_manifest_v1` binds per-verifier resource fingerprints. It does not contain all research-level information such as dataset partitions, label provenance, hardware/dependency environment, policy applicability, or protocol decisions. A future research-level configuration should reference the appropriate validated runtime `ResourceManifest` and `MeasurementSetup` alongside the separate dataset, execution, policy, and provenance records. Do not treat one schema as a substitute for the others.

### Dataset and protocol identity

| Field / information | Current status | Evidence and scope | Responsible owner | Remaining work |
|---|---|---|---|---|
| Development source for the completed cost calibration | **VERIFIED / FROZEN** | Raunak designated `evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/`; the collection-level ID is `research_v1_exploratory_v1`. The selected collection and calibration were Development-only. The frozen measurement and calibration bundle records the permitted pair. | Person 1 designated the population; Person 2 recorded and froze the cost evidence. | None for the completed calibration. Any different workload or population requires its own explicit decision and provenance. |
| History/Development source material | **AVAILABLE / OWNER-DEFINED** | Research dataset and handoff material is locally available under `evaluation/datasets/`; the handoff ZIPs inspected were byte-identical duplicates of existing ignored dataset files. Their presence does not make them policy-fit inputs or authorize a new population. | Person 1 | Confirm the exact dataset/split and payload identities for any later policy or evaluation task; preserve unresolved/label limitations. |
| Source question IDs versus collection dataset ID | **VERIFIED / FROZEN for the cost collection** | `research_v1_exploratory_v1` is the collection-level Development ID. Original source-question dataset identifiers remain separate per-example provenance. | Person 1 owns dataset identity; Person 2 preserves the mapping. | Do not substitute per-question source IDs for the collection-level ID. |
| Research question, inclusion rules, source/license decisions, and protocol version | **AVAILABLE / OWNER-DEFINED; broader approval remains distinct** | Dataset manifests and protocol documents provide recorded definitions and limitations; the cost-calibration freeze does not approve or freeze the complete research protocol. | Person 1, with project approval as required | Verify against the current protocol/readiness records before asserting a full research freeze or confirmatory evaluation. |
| Candidate-answer and label provenance | **AVAILABLE / OWNER-DEFINED with documented limitations** | Dataset records and preparation documentation describe candidate construction, labels, and unresolved records. The cost-only measurement artifact is not an adjudication or policy-quality result. | Person 1 | Preserve the documented label source, adjudication status, and unresolved handling in later evaluation. |
| Benchmark context versus retrieval corpus condition | **PENDING for broader policy/evaluation scope** | The completed cost calibration is tied to its recorded corpus/index/resource identities. That does not settle which context condition a future baseline or fitted policy must use. | Person 1 defines the evidence condition; Person 3 defines matched policy/baseline inputs; Person 2 verifies runtime resources | Bind the chosen condition consistently across the later policy and comparison workload. |
| Final Test separation | **SEPARATE / NOT AUTHORIZED BY THIS FREEZE** | The calibration uses only Development examples. Its reservation is metadata-only leakage protection; the freeze does not permit Final Test payload access or execution. | Person 1/custodian controls test custody; project owner authorizes any future stage | Keep Final Test payloads, labels, questions, answers, contexts, and outcomes outside Development collection and calibration. Any later Final Test work needs its own explicit authorization and process. |

### Runtime resources, setup, and compatibility

| Field / information | Current status | Evidence and scope | Responsible owner | Remaining work |
|---|---|---|---|---|
| Resource manifest and setup identity | **VERIFIED / FROZEN for the Development direct-verifier calibration** | Manifest ID `754bfa8ec4b43881a183c64478d791496e6a21d2e68b3c862d85a8e89beda10c`; setup fingerprint `83c114806aa6eb3ba06664b8d3d6bd1892699f0c588990e0fb88f35bcc37f1ee`, retained in the frozen bundle. | Person 2 | For later policy execution, compare the chosen contract to this setup; do not presume compatibility if policy, roster, host, or resources change. |
| Service/model identity | **VERIFIED / FROZEN for this pilot** | Ollama server version `0.40.14`; model `llama3.2:3b`; model digest `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`. The mutable model name alone is not the identity. | Person 2 verifies runtime metadata; Person 3 may define later policy needs | Reverify only when a later approved run requires it or the configuration changes. |
| Confidence generation configuration | **VERIFIED / FROZEN for this pilot** | Adapter/configuration fingerprint binds `llama3.2:3b` and `n_samples=5`; see the frozen resource manifest and calibration bundle. | Person 2 recorded; Person 3 considers applicability to later policy work | Any change requires a new compatibility assessment and cannot silently inherit this calibration. |
| Per-verifier resource requirements and fingerprints | **VERIFIED / FROZEN for the four-verifier setup** | `ResourceManifest` represents verifier implementations/configuration and applicable model, corpus, index, prompt, and service resources. The frozen manifest covers the required calibration roster exactly. | Person 2 measured/validated; Person 3 defines any later selected verifier scope | Check the exact policy candidate roster and execution contract before reuse. `apply_calibration` requires exact candidate coverage and compatible manifest/setup bindings. |
| Evidence corpus, index, receipt, and relocation | **VERIFIED within the frozen pilot contract; not a general transfer grant** | The pilot manifest and separately validated Evidence relocation authorization bind the specific Evidence index/resource identity. Relocation authorization is narrow and does not authorize unrelated resource or service changes. | Person 2 verifies the specific contract; Person 1/Person 3 define any changed evidence condition | Revalidate any changed corpus, index, path, model, or resource manifest under the repository compatibility checks. |
| Hardware, environment, dependencies, source revision | **RECORDED in the frozen MeasurementSetup for that run** | `MeasurementSetup` records environment, dependency versions, source revision/digest, resources, and evidence kind. These are run-specific provenance, not a claim about a future machine or clean checkout. | Person 2 | Capture new observations if a later approved runtime differs or requires fresh setup verification. |
| Runtime preflight and compatibility evidence | **COMPLETED for the Development cost collection** | The pilot-specific adapter/resource contract was verified before collection; the frozen setup and resource identities are carried by the measurement/calibration artifacts. This is not a global system preflight for other policies or workloads. | Person 2 | Perform only the compatibility checks required for a later, separately approved execution configuration. Do not bypass manifest or provenance validation. |

### Policy, strategy, and evaluation configuration

| Field / information | Current status | Responsible owner | Remaining work |
|---|---|---|---|
| Research-v1 experimental policy and selected strategy | **Not established by the cost-calibration freeze** | Person 3 | Supply or fit an explicitly applicable policy under the approved research scope, with policy, matrix, contract, and applicability identities. Do not infer applicability from shared verifier names. |
| Matched baseline and policy comparison | **Separate later work** | Person 3, with Person 1’s protocol decisions | Define the baseline and matched workload/context/resource conditions; preserve the comparison protocol and reproducibility evidence. |
| Budget and resource-weight selection | **Not completed or authorized by the cost-calibration freeze** | Person 3 / study owner | Make the required experimental decisions separately. The calibrated timings are not a budget, monetary price, or automatic resource weight. |
| Policy-specific runtime and execution contract | **Pending the later policy/strategy configuration** | Person 3 defines it; Person 2 verifies compatibility | Bind candidates, route/team/component requirements, execution configuration, and applicable runtime resources. Check the supplied calibration against these exact identities before a future build. |
| Final Test evaluation or release | **Not authorized by this freeze** | Project owner and independent custody process | Requires a separate explicit authorization and applicable custody/release procedure. This document does not request or expose Final Test payloads. |

## Responsibilities and handoff

### Person 1 — protocol and datasets

- Research-v1 dataset and Development handoff material is available locally, and Raunak designated the exploratory v1 Development population for the completed cost collection.
- Own the research question, benchmark/split definitions, source and license decisions, candidate/label provenance, unresolved-record policy, and evidence/context condition.
- For any later policy or evaluation use, identify the exact approved population and limitations. Do not treat the cost pilot as protocol approval or Final Test authorization.

### Person 2 — runtime configuration and cost estimation

- Completed and froze the Development-only four-verifier cost calibration described above; the canonical committed inputs are in `artifacts/research-v1-development-cost-calibration-v1/`.
- Preserve the calibration method, measurement provenance, resource manifest, setup fingerprint, and Confidence configuration. Later actual evaluation durations must remain distinct from frozen planning estimates.
- For any later approved policy runtime, verify its adapter, observed resources, setup fingerprint, and compatibility with the calibration. A changed setup or roster may require new authorized measurements; no such run is implied here.

### Person 3 — policies, baselines, and reproducibility

- Define and prepare the research-scope policy/strategy, matched baseline, policy applicability, and reproducibility/checkpoint evidence.
- Treat the frozen calibration as a candidate input only after checking its exact setup/resource and verifier coverage against the policy build contract.
- Policy fitting, budget/resource-weight selection, optimization, and Final Test work are separate stages; none is completed or authorized by this cost-calibration freeze.

## Contract references

| Contract concern | Repository source | Crosswalk use |
|---|---|---|
| Per-verifier resource rows, manifest identity, required kinds | `app/game/resource_provenance.py` | Fingerprint implementation/configuration and applicable model, corpus, index, prompt, and service resources; require exact verifier coverage and consistent shared hashes. |
| Runtime configuration and dispatch | `evaluation/docs/runtime_configuration.md`; `app/game/execution_contract.py`; `app/game/artifacts.py`; `app/game/deployment.py` | Distinguish existing package-specific policies from a future research-v1 policy; bind execution configuration to the applicable resource manifest. |
| Measurement and calibration provenance | `evaluation/docs/cost_measurement_protocol.md`; `app/game/offline/calibration.py`; `app/game/offline/collection.py`; `app/game/offline/timing.py` | Link dataset/split/purpose, setup, resource identities, source revision, durations, and statuses; preserve planning estimates separately from later observations. |
| Frozen Development calibration bundle | `artifacts/research-v1-development-cost-calibration-v1/` | Authoritative committed measurements, calibration, calibration-input provenance, and Development-only freeze manifest. |
| Project adapter and resource preflight | `app/benchmark/project_adapter.py` | Inspect actual adapter/resource configuration and observed setup; preflight is distinct from verifier generation. |
| Resource relocation | `app/game/offline/resource_relocation.py`; `docs/game_resource_relocation.md` | Treat relocation as narrow, explicitly validated evidence, not a general compatibility override. |
| Policy applicability and calibration use | `evaluation/docs/policy_applicability.md`; `docs/verifier_cost_calibration.md`; `app/game/offline/build.py` | Check applicability and pass a compatible calibration by explicit path; no policy fit is implied by this document. |
