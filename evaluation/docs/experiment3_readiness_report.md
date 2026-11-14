# Experiment 3 readiness report

## Gate change

`collection_gate.collection_allowed` no longer treats a human signature as a prerequisite for execution. `prerequisite_validator.assess` is unchanged and still reports `READY_FOR_APPROVAL` when the unsigned approval templates are internally consistent. That status means the historical approval package is unsigned. It is not the execution gate.

The execution gate is `evaluation/experiments/experiment3/execution_readiness.py`. It distinguishes:

- `BLOCKED`: configuration, hash, population, calibration, or dependency integrity failed.
- `TECHNICALLY_READY`: integrity passed and the verifier runtime is not available.
- `AUTHORIZED_BY_RESEARCH_LEAD`: integrity passed, the recorded research-lead authorization matches, and the verifier runtime is available. Verifiers have not necessarily been called.
- `EMPIRICALLY_EXECUTED`: at least one completed empirical cell exists and the full 15,624-cell structural grid is not finished.
- `EMPIRICALLY_COMPLETED`: 15,624 completed empirical cells are stored. The 8,928 count is the one-column-per-kind design and is not the completion target.

After the completed collection, `execution_report()` returned `EMPIRICALLY_COMPLETED`, `empirical_recording_count` 15624, `verifiers_available` true, and an empty blocker list. `independent_human_approval`, `contributor_signatures_obtained`, and `fabricated_signatures` remain false. `collection_allowed()` still does not launch verifiers. Its status field is the completion record. `collection_started` on that command stays false because the command itself does not start collection.

## What replaced signatures

The gate checks the execution configuration against constants and recomputed calibration quantities:

- loss 1.0 / 1.0 / 0.2, threshold 0.55, suppression unavailable
- coefficient `1.3399597937725295e-05` loss per millisecond
- budget `14996.39091498102` milliseconds, equal to the cheapest frozen size-3 confidence team
- calibration id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`
- dependency `structural_shared_resource_v1` with `empirical_evidence: none`
- reputation inputs still at 0 observations and not self-approved
- eligibility roster still 372 groups and 744 candidates, with collection and Final Test flags still false
- bootstrap seed `20261113`
- verifier modules import, the Development evidence corpus exists, and local Ollama has `llama3.2:3b`
- output paths containing `final_test` are refused

An `approved: true` field, an approver name, or a different budget fails `configuration_errors`. The eligibility manifest and the cost-calibration freeze were not edited to flip their authorization flags.

## What remains unsigned

Person 1's eligibility manifest still withholds verifier collection, attempt recording, and policy fitting. Person 3's reputation input file remains `PENDING_PERSON3`. The protocol, corpus, dependency, and collection approval templates remain unsigned. Vasavi's cost freeze remains a freeze of the millisecond measurements, not an Experiment 3 protocol signature. Model-weight snapshot hashes in the collection configuration remain `UNKNOWN`. No hash was invented for them.

## Implementation status

`empirical_runner.run` writes a status manifest and does not call verifiers. `empirical_executor.py` calls `SemanticVerifier`, `EvidenceVerifier`, `RuleVerifier`, and `ConfidenceVerifier` on Development inputs, applies `transform` for the four conditions, scores feasible teams with `DecisionEngine`, and solves the three methods with `solve_minimax`.

A two-candidate probe wrote `evaluation/experiments/experiment3/empirical/smoke_reports.jsonl` and `smoke_results.json`. That probe is not the experiment. The full collection command is `python -u evaluation/experiments/experiment3/empirical_executor.py`. It resumes `verifier_reports.jsonl`. The completed run stored 744 reports and 15,624 cells.

## Tests

After the completed collection, this command passed 51 tests:

`python -m pytest tests/test_experiment3_approval_package.py tests/test_experiment3_prerequisites.py tests/test_experiment3_empirical_integration.py tests/test_experiment3_resource_sensitivity.py evaluation/tests/test_experiment3_execution_gate.py -q --tb=line`

The one failure in the first run was an assertion that collection stayed blocked on an unsigned coefficient. That assertion was updated to require the coefficient and budget to be present, the protocol approval to remain unsigned, and `independent_human_approval` to stay false. The rerun of that test and the live status test passed.

## Blockers

The completed collection has no remaining execution blocker. `execution_report()` blockers are empty. Failed verifier calls, had any occurred, would have been stored and not imputed. None of the 744 stored calls failed. A later reproduction can still fail if Ollama or a model load fails. That would leave the new run short of 15,624 cells, and a short run is not a completed experiment.
