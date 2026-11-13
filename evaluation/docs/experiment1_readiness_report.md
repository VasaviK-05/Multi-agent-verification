# Experiment 1 readiness report

Experiment 1: clean and attacked performance against strong baselines (`research_objective.md` § Experiment 1). Assessed 2026-11-11 on branch `raunak-research-evaluation`.

**Overall: Experiment 1 cannot start.** The pipeline code is ready and tested on synthetic Development data, but no real verifier recordings exist and no valid Final Test exists. Most scientific settings also still await human approval.

Status values used here:
- **COMPLETED:** implemented and verified in this repository.
- **BLOCKED:** missing data or work that sign-off alone cannot clear.
- **PENDING HUMAN APPROVAL:** the work or evidence exists, and a named person must decide.

## Update 2026-11-11: temporary research mode

Human approval, human adjudication and manual verification were declared out of scope for this preparation phase. Automated, provisional labels now give both benchmarks an incorrect class (`exploratory_dataset_and_final_test_v2.md`). **Exploratory Experiment 1 work can use these datasets.** Confirmatory Experiment 1 remains blocked: the labels are synthetic, and evaluation authorization is pending. Custody is now designated to the dataset creator and is not independent.

| Item | Status | Evidence |
|---|---|---|
| Label-source taxonomy (VERIFIED_CORRECT / SYNTHETIC_INCORRECT / HUMAN_VERIFIED_INCORRECT / UNRESOLVED) in data and game layer | COMPLETED | `label_classes.py`; `Example.label_class`; `label_composition` in readiness, comparison and Final Test evaluation |
| Exploratory Development `research_v1_exploratory_v1` | COMPLETED (provisional labels) | Development: GSM8K 187 correct / 187 synthetic incorrect; HotpotQA 200 / 200. History: GSM8K 277 / 277; HotpotQA 300 / 299. 0 human-verified |
| Final Test v2 `research_v1_final_test_v2_exploratory_v1` | COMPLETED (provisional labels) | 600 fresh groups: 300 GSM8K train and 300 HotpotQA validation, each 1 correct + 1 synthetic incorrect. Exposure, leakage and isolation audits pass. Manifest `e572093a…d3319ee` |
| `FinalTestReservation` for v2 | COMPLETED (label-free) | `final_test_research_v1_eval_v2/final_test_reservation.json`, 1,200 examples |
| Final Test v2 custody | DESIGNATED, NOT INDEPENDENT | Dataset creator Raunak is the designated custodian (`final_test_v2_custodian_appointment.json`). No independent custodian and no OS protection. Previous status `PENDING_NO_INDEPENDENT_CUSTODIAN` |
| Human approval of synthetic rules, GSM8K train source and 300-group cap | DEFERRED | Out of scope in temporary research mode |
| Human adjudication of negatives and the 871 unresolved candidates | DEFERRED | Unresolved candidates stay separate and unlabelled |
| Final Test v2 evaluation authorization | PENDING | Gate reasons: `evaluation_authorization_pending`, `no_confirmatory_authorization_record`. Custody does not authorize evaluation. Manifest `e572093a…d3319ee` stays `NOT_AUTHORIZED` |

Checks run for this update:
- New tests: `tests/test_synthetic_negatives.py` (10) and `tests/test_final_test_v2.py` (14). They cover negative generation, label provenance, class balance, exposure exclusion, split leakage, reservation integrity and Final Test isolation.
- Updated tests: `test_final_test_retirement.py` (gate accepts the new classes) and `test_verified_candidate_adapter.py` (contract now includes `synthetic_transformation`).
- Full suite: 1,493 passed, 1 skipped, 2 failed. The two failures (`test_question_analyzer_ollama` heuristic fallback and `test_validation::test_orchestrator_pipeline`) import none of the changed modules.
- Validators:
  - `build_exploratory_development validate` and `build_final_test_v2 validate`: 0 mismatches.
  - `person1_validation validate`: 17 PASS, 3 BLOCKED, no drift.
  - `experiment1_preparation validate`: 0 stored-hash mismatches. Its exposure-dependent outputs now recompute differently because the exposure scan includes the two new datasets. The v1 outputs remain the frozen snapshot, and v2 reproduced their pool hashes using the snapshot's file set.

Custody check after the appointment: `tests/test_final_test_v2_custody.py` (6). It checks the designated-creator status, refusal of verifier developers and Development runners, preservation of the label, roster, and reservation-entry hashes, and that the appointment does not authorize evaluation.

Rows 4, 5a and 8j in the table below are superseded by this update for exploratory work only. Every other row is unchanged: Attempts, cost calibration, the dependency registry and the approvals are still missing.

## Status (before temporary research mode)

| # | Item | Status | Evidence / what is missing |
|---|---|---|---|
| 1 | Content-level Final Test contamination audit | COMPLETED | `final_test_contamination_audit.md`: 807 of 2,638 groups contaminated (GSM8K 500, HotpotQA 307) |
| 2 | Correct docs that reported leakage as fully passed | COMPLETED | See "Documentation corrected" below |
| 3 | Retire the provisional Final Test | COMPLETED | `evaluation/config/final_test_retirements.json`; label access refused and readiness BLOCKED for its manifest; files unchanged |
| 4 | Development label balance audit | COMPLETED | Table below; HotpotQA has no verified incorrect candidates in History or Development |
| 5 | Final Test v2 selection plan | COMPLETED (plan) | `final_test_v2_selection_plan.md`; label-free eligible pools recorded with hashes |
| 5a | Final Test v2 build, reservation, custody | BLOCKED | Needs approved negative rules, sample size, GSM8K train-source approval, a builder extension and a named custodian |
| 6 | `FinalTestReservation` and readiness consistency | COMPLETED | Fixes listed below |
| 7 | Experiment 1 pipeline on Development | COMPLETED (synthetic) / BLOCKED (real) | Reservation-based pipeline tested; 0 real verifier Attempts recorded for research_v1 |
| 8a | Verifier Attempts on Development | BLOCKED | Development feasibility pilot stopped before execution (adapter configuration unset); `protocol_readiness.yaml` `attempts.complete_count: 0` |
| 8b | Person 2 cost calibration for research_v1 | BLOCKED | No research_v1 measurements. Details below |
| 8c | Attack implementation | COMPLETED (code) / PENDING HUMAN APPROVAL (settings) | Five report-corruption kinds implemented and tested; suppression mode and dependency registry undecided |
| 8d | Dependency registry for attack groups | BLOCKED | No registry is declared anywhere. Under `shared_unknown`, all four verifiers form one failure group, so every attack corrupts the whole team and the attack game is degenerate |
| 8e | Baseline implementation | COMPLETED (code) / PENDING HUMAN APPROVAL (roster) | Seven methods in `comparison.METHODS` |
| 8f | Evidence-bearing scope (all HotpotQA) | PENDING HUMAN APPROVAL | Readiness blocks evidence studies over three named evidence-contract failures, which now pass. A reviewer must confirm the repair and remove the gate |
| 8g | Loss, threshold, minimum contributors, budget | PENDING HUMAN APPROVAL | `person1_approval_checklist.md` items 1–10; `protocol_readiness.yaml` all `approved: false` |
| 8h | Statistical analysis plan, sample size | PENDING HUMAN APPROVAL | No power or precision justification |
| 8i | Source population, licenses, label policy | PENDING HUMAN APPROVAL | `protocol_readiness.yaml` |
| 8j | Unresolved candidate review (871) | BLOCKED | Needs named reviewers; queue in `evaluation/datasets/person1/research_v1_person1_v1/` |

`python -m evaluation.data_preparation.final_test_workflow readiness --config evaluation/config/protocol_readiness.yaml --manifest evaluation/datasets/final_test_research_v1_eval_v1/manifest.json` reports:
- exploratory readiness: LIMITED;
- confirmatory readiness: BLOCKED;
- BLOCKED items: policy fitting, Development pilot, Attempts, Offline Examples, and the Final Test (retired; no verified incorrect candidates for GSM8K or HotpotQA; no content-level exposure audit);
- every other item: NOT APPROVED.

## Development label balance

From `development_label_balance.json` (same output directory as the contamination audit). Unresolved candidates are excluded from binary metrics and never counted as incorrect.

| Role | Benchmark | Verified correct | Verified incorrect | Unresolved |
|---|---|---:|---:|---:|
| History | GSM8K | 277 | 124 | 199 |
| History | HotpotQA | 300 | **0** | 340 |
| Development | GSM8K | 187 | 91 | 122 |
| Development | HotpotQA | 200 | **0** | 210 |

**Benchmark without verified incorrect answers: HotpotQA, in both History and Development.** Consequences:
- Development payoffs cannot penalize HotpotQA false acceptance, so a fitted policy is not tested against the main threat on HotpotQA.
- History reputation for HotpotQA is learned from correct answers only.

GSM8K negatives all come from one narrow synthetic rule (gold+1 discrete counts), which limits how far GSM8K results generalize.

## Fixes made

**Final Test workflow** (`evaluation/data_preparation/final_test_workflow.py`):
- `build` now runs a content-level exposure check over `evaluation/datasets/`, `evaluation/results/` and `data/test_benchmark.jsonl`. It excludes previously exposed questions, fails closed on any remaining overlap, and records a computed `exposure_audit` in place of the hardcoded `previously_exposed_final_test_reused: False`.
- New retirement registry, `evaluation/config/final_test_retirements.json`. `read_custodian_labels` refuses retired manifests before touching authorization files or logs.
- `validate_readiness` used to map the manifest's permanent `NOT_AUTHORIZED` status to "NOT APPROVED", while `validate_artifacts` requires that status. Confirmatory readiness could therefore never reach READY. It now uses `final_test_gate`, which:
  - blocks retired manifests, hash mismatches, single-class labels and a missing exposure audit;
  - grants approval only from a separate authorization record bound to the manifest hash (`--authorization`).
- Missing data (Development pilot not completed, zero Attempts, zero Offline Examples) is now BLOCKED, not "NOT APPROVED".

**Research comparison** (`app/game/research/`):
- `ExperimentSpecification.manifest` used to accept only a fully labelled `DatasetManifest`. Experiment 1 inputs, including Development-only comparison, therefore had to carry Final Test labels, and the specification's `FinalTestReservation` branch was unreachable. It now also accepts a `TrainingManifest` that holds only the reservation.
- `score_frozen_final` and `bootstrap_frozen_final` take a separately released `final_partition`. It must match the reservation exactly and is rechecked for split leakage and label sources. The result records `reservation_id` and `final_payload_id`.
- Readiness adds `empirical_study_requires_final_test_reservation`, so an empirical study cannot embed Final Test labels in its specification.

## Person 2 cost calibration

- The only calibration (`docs/verifier_cost_results.md`, calibration ID `1a2abc56…ab992`) measured 344 attempts on an arithmetic-heavy sample (80 arithmetic, 6 factual) at code revision `224a2e5`. It does not cover research_v1 GSM8K/HotpotQA Development.
- Its bundle lives under the Git-ignored `build/` directory, which is absent from this workspace, so it cannot be re-verified here.
- `CalibrationRequest` and `apply_calibration` require the study's own `FinalTestReservation`. Research_v1 calibration therefore has to wait for the v2 reservation.
- The label-free collection roster (`person2_cost_collection_order.jsonl`, 478 Development candidates) exists. Its size and budget values are pending.

## Attacks and baselines

- **Attacks** (`app/game/offline/attacks.py`): clean, forced support, forced rejection, confidence inflation and suppression, each applied to one full dependency group.
  - Pending decisions: suppression mode (`unavailable` or `abstention`) and a dependency registry.
  - Forced-support effects need verified incorrect candidates to be measurable.
- **Baselines** (`app/game/research/comparison.py`): full minimax, uniform, deterministic minimax, clean-Development optimum, fixed reputation-weighted, fixed dependency-group, and the captured coverage-aware greedy team. All are selected on Development only and tested.
  - The runtime `execution_mode="baseline"` orchestrator is a separate live path that is not replayed in the comparison.
  - Its partial run (`evaluation/results/baseline/`) touched 30 questions of the retired Final Test.
  - Whether "strong baselines" needs more methods (for example single best verifier, or all-verifier majority) is a team decision.

## Tests executed

- New tests:
  - `tests/test_experiment1_reservation.py`: 5 tests covering the reservation-based pipeline, Development-only scoring and the released-payload checks.
  - `tests/test_final_test_retirement.py`: 13 tests covering retirement, the readiness gate and content-level exposure.
  - `tests/test_experiment1_preparation.py`: 7 tests covering the contamination audit, label balance, the label-free pool and write-once output.
- Updated: `tests/test_development_feasibility_pilot.py::test_readiness_keeps_policy_fitting_blocked` now expects zero Attempts to be BLOCKED.
- Full research/evaluation selection: 554 passed, 0 failed. The selection is the three new files plus `test_final_test_workflow`, `test_game_offline`, `test_game_research`, `test_game_foundation`, `test_game_build`, `test_game_completion`, `test_game_collection`, `test_game_runtime`, `test_cost_calibration`, `test_pilot_abstention_contract`, `test_research_dataset_pipeline`, `test_development_feasibility_pilot`, `test_person1_validation`, `test_arithmetic_pilot` and `test_adaptive_pipeline`.
- Provisional Final Test files (roster, audit, manifests, custodian labels) still match their integrity receipts byte-for-byte.
- `python -m evaluation.data_preparation.experiment1_preparation validate`: 0 stored-hash mismatches, 0 recomputed mismatches, generator unchanged.
- `python -m evaluation.data_preparation.person1_validation validate`: 17 PASS, 3 BLOCKED, no drift. Its frozen "Final Test isolation PASS" covers History/Development only; see the correction in `person1_compliance_matrix.md`.

## Documentation corrected

- `person1_compliance_matrix.md`
- `final_test_leakage_audit.md`
- `final_test_manifest.md`
- `final_test_custody_protocol.md`
- `research_protocol_readiness.md`
- `dataset_split_protocol.md`
- `research_objective.md`

Each now states that the exact-leakage pass covered research_v1 History/Development only, that content-level exposure failed, and that the provisional Final Test is retired.

## Next actions before Experiment 1 can begin

1. **Protocol owner:** approve loss, threshold, minimum contributors, budget, suppression mode, baseline roster, metrics and the statistical plan (`person1_approval_checklist.md`).
2. **Team:** declare the verifier dependency registry, i.e. which verifiers share models, corpora or prompts.
3. **Reviewer:** confirm the evidence-contract repair (the three tests in `readiness.EVIDENCE_FAILURES` now pass) and remove the evidence gate, or restrict Experiment 1 to GSM8K.
4. **Team:** approve negative-candidate rules for both benchmarks, the GSM8K train source and the sample size. Name reviewers for HotpotQA adjudication and the 871 unresolved candidates.
5. **Person 1:** rebuild History and Development with the approved negatives as a new research_v1 version, keeping the current version.
6. **Person 1 with the custodian:** extend the builder for train sources and negatives. Then the custodian builds Final Test v2 from the recorded pool, checks its exposure audit, and prepares the `FinalTestReservation`.
7. **Person 2:** configure verifier adapters and record complete Attempts on Development only. Then collect costs and calibrate against the v2 reservation.
8. **Person 1:** assemble an `ExperimentSpecification` with a `TrainingManifest`, run readiness, fit on Development, and freeze the comparison.
9. **Protocol owner and custodian:** sign an authorization record for the v2 manifest. Only then may the custodian release the Final Test payload for one confirmatory scoring run.
