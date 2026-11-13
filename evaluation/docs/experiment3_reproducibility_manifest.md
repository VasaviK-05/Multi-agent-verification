# Experiment 3 reproducibility manifest

Empirical Experiment 3 cannot be reproduced because it was not run. The checks below can be repeated without opening Final Test labels.

## Commands

```text
.venv\Scripts\python.exe evaluation\experiments\experiment3\corpus_audit.py
.venv\Scripts\python.exe evaluation\experiments\experiment3\collection_gate.py
.venv\Scripts\python.exe evaluation\experiments\experiment3\export_synthetic_figures.py
.venv\Scripts\python.exe -m pytest evaluation/tests/test_experiment3_execution_gate.py tests/test_experiment3_prerequisites.py tests/test_experiment3_visualizations.py tests/test_research_readiness.py -q
```

Do not run `evaluation/experiments/experiment3/synthetic_runner.py`. The runner source is missing, and writing outputs would replace `synthetic/results.json`.

## Identifiers

| Item | Value |
|---|---|
| Git commit at audit | `65115a530d2939ecc35b7e214f4b32c3e800fab0` |
| Specification SHA-256 | `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529` |
| Eligibility body SHA-256 | `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d` |
| Corpus SHA-256 | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |
| Index | `idx-c1dc6980912b` |
| Python | 3.12.1 |
| Platform | Windows-11-10.0.26300-SP0 |
| Hardware | UNKNOWN |
| Model-weight snapshots | UNKNOWN |
| Collection seed | null |
| Bootstrap seed | proposed 20261113, not approved |

The audit record is `evaluation/experiments/experiment3/manifests/corpus_audit.json`. The gate record is `evaluation/experiments/experiment3/logs/collection_gate.json`.

## Tests

45 passed across the four modules listed above. `tests/test_experiment3_synthetic.py` failed during collection because the dependency helpers it imports are absent. The full suite was not run, because `tests/test_final_test_v2_custody.py` contains a live label-hash check and Final Test labels were required to stay sealed.
