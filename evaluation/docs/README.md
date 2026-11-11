# Evaluation notes

Research write-ups for this repository live in this directory. Dataset files under `evaluation/datasets/` are inputs and are not rewritten by these experiments.

## Experiment index

| Experiment | Status | Report | Results |
|---|---|---|---|
| Baseline validation (`execution_mode="baseline"`) | Development-set run | [baseline_evaluation.md](baseline_evaluation.md) | `evaluation/results/baseline/` |
| Evidence verifier on HotpotQA (single verifier, not the orchestrator) | Existing script `evaluation/run_evidence_hotpotqa.py` | Not part of the baseline report | `evaluation/results/evidence_hotpotqa_results.json` |
| Rule verifier on GSM8K (single verifier, not the orchestrator) | Existing script `evaluation/run_rule_gsm8k.py` | Not part of the baseline report | `evaluation/results/rule_gsm8k_results.json` |

## Person 1 dataset and protocol records

| Record | Purpose |
|---|---|
| [person1_compliance_matrix.md](person1_compliance_matrix.md) | PASS/BLOCKED status, commands, test results, conclusion |
| [person1_approval_checklist.md](person1_approval_checklist.md) | Pending decisions, options, owners |
| [research_v1_inventory_and_provenance.md](research_v1_inventory_and_provenance.md) | Artifact inventory, sources, corpus identity, result-file compatibility |
| [research_v1_label_audit.md](research_v1_label_audit.md) | Label counts, methods, consistency checks, unresolved reasons |
| [research_v1_development_roster.md](research_v1_development_roster.md) | Development eligible roster, ordered collection rosters, hashes |
| [final_test_manifest.md](final_test_manifest.md) | Provisional Final Test identity, hashes, isolation |

Re-run the validation with `python -m evaluation.data_preparation.person1_validation validate`.

The baseline report describes the full orchestrator. The single-verifier scripts are separate measurements and are not substitutes for it.

Planned follow-ups, not yet reported here:

- Adversarial robustness.
- Cost–accuracy trade-off.
- Game-theoretic selection compared with this baseline.
