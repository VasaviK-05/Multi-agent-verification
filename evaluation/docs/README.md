# Evaluation notes

Research write-ups for this repository live in this directory. Dataset files under `evaluation/datasets/` are inputs and are not rewritten by these experiments.

## Experiment index

| Experiment | Status | Report | Results |
|---|---|---|---|
| Baseline validation (`execution_mode="baseline"`) | Development-set run | [baseline_evaluation.md](baseline_evaluation.md) | `evaluation/results/baseline/` |
| Evidence verifier on HotpotQA (single verifier, not the orchestrator) | Existing script `evaluation/run_evidence_hotpotqa.py` | Not part of the baseline report | `evaluation/results/evidence_hotpotqa_results.json` |
| Rule verifier on GSM8K (single verifier, not the orchestrator) | Existing script `evaluation/run_rule_gsm8k.py` | Not part of the baseline report | `evaluation/results/rule_gsm8k_results.json` |

The baseline report describes the full orchestrator. The single-verifier scripts are separate measurements and are not substitutes for it.

Planned follow-ups, not yet reported here:

- Adversarial robustness.
- Cost–accuracy trade-off.
- Game-theoretic selection compared with this baseline.
