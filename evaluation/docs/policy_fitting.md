# Policy Fitting

## 1. Purpose and scope

This document records the offline policy-fitting methodology, input requirements, validation process and historical experimental results for the capstone.

The authoritative implementation references are:
- `docs/game_policy_build.md`
- `docs/multitask_policy_workflow.md`
- `docs/multitask_policy_results.md`
- `docs/factual_policy42_results.md`

Policy fitting is an offline research operation. It uses declared history and development recordings, independent labels, planning context, resource evidence and approved scientific settings.

The fitted output is a versioned PolicyArtifact. It must be validated, exported, reloaded and checked before any integration.

Historical fitting results are documented as historical evidence. They do not authorize new fitting or changes to the frozen policy during the current transfer evaluation.

## 2. Separation of fitting and evaluation

- History supplies the reputation/planning snapshot.
- Development data supports fitting and development diagnostics.
- Final-test payloads remain outside fitting inputs.
- Transfer evaluation applies the unchanged frozen policy to fresh paired reports.
- Transfer evaluation must not refit, recalibrate or update reputation.

A mathematically valid fitted policy is not automatically an operationally useful policy or evidence of held-out performance.

## 3. Required fitting inputs

The build specification uses the versioned `offline_policy_build_v1` format.

It retains the study and dataset declarations, recording identities, scope, code revision, execution contract, attack scenarios, costs, losses, seeds and uncertainty design.

The training manifest uses `game_training_manifest_v1` and contains exactly two full partitions:
- History.
- Development.

Final-test data is represented only by a metadata-only reservation. The fitting configuration must not contain final outcome filenames, URIs, labels, reports or payload paths.

A captured PlanningContext must agree with independent history under the declared priors. The builder recomputes and verifies the history snapshot before binding the context to the training/reservation identity and execution contract.

Stale bindings, inconsistent snapshots and recording categories that do not match `category_id(context)` must be rejected rather than silently rewritten.

## 4. Readiness and fitting constraints

Before fitting, the builder checks candidate completeness, independent labels, configuration, resources, adapters, supported achieved coverage and evidence-producer readiness.

Other requirements include:
- Explicit treatment of unknown dependencies.
- Valid execution and failure semantics.
- Complete development examples and attack scenarios.
- Compatible planning and resource bindings.
- Approved loss, cost, budget, threshold, prior and uncertainty settings.

Pooled contexts require the explicit multi-domain workflow.

Every feasible team and both aggregation methods remain represented, including strategies with zero probability.

The builder replays every development example and attack, then passes the declared optimizer tolerance to the existing LP solver.

Missing inputs or readiness failures must block fitting. No synthetic substitute may fill missing scientific inputs.

## 5. Policy validation and artifact export

After fitting, the builder checks the optimizer certificate and exports the PolicyArtifact.

It then reloads the exported artifact, refits under the same installed environment and compares the results.

The reproducibility checks include:
- Matrix axes, definitions and values.
- Policy strategy probabilities.
- Reputation records.
- Execution and context bindings.

Matrix values and policy probabilities must match with absolute tolerance `1e-12` and relative tolerance zero. Reputation records are compared exactly.

The certificate tolerance is explicit and recorded in the build metadata. The factual campaign used `1e-8`.

Successful builds write:
- `policy.json`
- `build-report.json`
- `summary.txt`

Blocked builds write `missing-inputs.json` and `summary.txt`, return status 2 and must not produce a policy artifact.

Use a new output directory for each successful build. Existing artifacts must not be overwritten.

## 6. Reproducibility metadata

Build metadata records:
- Canonical input/configuration digest.
- Exact Git revision and working-tree cleanliness.
- Application Python source digest.
- Python version and platform.
- NumPy, SciPy and Pydantic versions.
- Bundled HiGHS version and solver method/options policy.
- Seeds, repetitions and uncertainty settings.
- Explicit optimizer tolerance.

Scientific outputs are separated from incidental build metadata.

Artifact identifiers remain exact hashes. Numerically equivalent outputs do not necessarily have identical bytes across different environments.

An isolated seeded RNG checks provider compatibility without changing scientific outputs. The builder does not run bootstrap inference.

## 7. Historical artifact identity

The factual Policy42 campaign retained these identifiers:

| Artifact component | Identifier |
|---|---|
| Artifact | `238adc94fa3d6d81f60740d4cb585c52befa1748ea2ca1ee7aa2e169cf464236` |
| Policy | `99d6d6369341c48f919c8a8f2a1643f0320821afa15bf9d323e816e5e46dad30` |
| Matrix | `25303e5c2f8d8db609c812b780e9373923204743ee459d56e0000b0cd94504bc` |
| History snapshot | `0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3` |
| Calibration | `d5fd225b45d0b09fb54de3a07344415604638ce004fa8b51dac6218bd25a2793` |
| Recording bundle | `71ccd4a8c331e574e849e1d84b4b9993df60be3c38da2275b19b8b8872eaab3c` |

The original source revision was `17b695373f935dc1f5fd09c37cf8917969367f7a`. The campaign recorded CPython 3.11.5, NumPy 2.4.6, SciPy 1.17.1, Pydantic 2.13.5 and bundled HiGHS 1.12.0.

The approval binding records the approved configuration digest, artifact, calibration and fit-driver source digest.

## 8. Runtime integration boundary

The documented integration path loads the saved artifact using `PolicyArtifact.model_validate_json`, registers it with `InMemoryPolicyProvider` and constructs a compatible `DeploymentEpisode`.

The runtime must receive the artifact's exact context, execution contract and execution-configuration identity.

Compatibility identifiers enforce captured planning and resource contracts. They are not semantic allowlists for arbitrary questions.

The integrating caller must respect the narrower approved study scope.

The factual Policy42 artifact is retained for engineering inspection. Its always-abstaining outcome is not a recommendation for operational activation.

## 9. Current transfer-evaluation restrictions

The current transfer protocol uses the original frozen artifact without refitting.

During transfer evaluation:
- Do not rerun policy fitting.
- Do not update reputation from new reports.
- Do not replace strategy probabilities.
- Do not tune thresholds, losses or dependency assumptions.
- Do not change the execution contract or configured cost model.
- Do not create a replacement deployment artifact.

Historical fitting results and fresh transfer results must remain separate.

Any future scientific change requires explicit study-owner approval and a separately bound build. It must not be introduced as an adjustment to the current transfer experiment.

## 10. Ownership and outstanding dependencies

The study owner is responsible for approving scientific settings, threat assumptions, losses and verifier roster changes.

Dataset and adjudication owners supply independent labels, provenance, audited splits, history/development recordings and final-test custody records.

Collection and integration owners supply compatible reports, resource observations, execution identities and runtime integration evidence.

The current transfer evaluation additionally requires authorized current-source snapshots, compatible clean and altered resources, paired recordings and resource-bound Evidence proofs.

These prerequisites have not been supplied or executed for a new real transfer experiment. Historical fitting completion does not establish current transfer readiness.

## 11. Validation evidence

The factual campaign handoff records the following verification:

- The resumed affected test suite passed 193 tests.
- Four selected public Evidence reproduction tests passed, with 89 deselected.
- Earlier focused readiness/research tests passed 51 tests.
- An earlier broader affected suite passed 267 tests.
- The completed report-only phase generated development diagnostics and two successful runtime parity checks.
- The saved artifact, solver certificate, provider and source digest were revalidated.
- Runtime parity checks used retained real development reports and the live resource observer, without additional inference attempts.

These counts overlap and must not be added together as unique passing tests.

The original prototype package and fitted artifact checks are separate from empirical evaluation. Synthetic tests and software probes establish implementation behaviour, not held-out robustness.

The absent `data/articles_13083.json` remains a separate full-corpus limitation.

## 12. Final limitations

Policy fitting depends on approved scientific inputs and complete, independently labelled development evidence.

A successful solver result does not establish that the selected policy is operationally useful. The factual Policy42 result demonstrates this distinction: the optimizer produced a valid certificate, but the minimum-contributor guard resulted in zero decision coverage.

Development comparisons do not establish held-out superiority. Reference-assisted country-capital results do not establish open-domain factual verification.

No new policy fitting, calibration, final-test evaluation or deployment activation is authorized by this document.

The frozen-policy transfer evaluation remains a separate procedure and must follow `docs/upstream_transfer_evaluation.md`.


