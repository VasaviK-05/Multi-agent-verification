# Experiment 3 reproducibility

Branch `raunak-exp-3`. Commit `5485c54eaaecc1e338d4b1e3b889353a7a34ce98`. The working tree is dirty with the Experiment 3 implementation. Do not treat that commit alone as containing this run. Reproduction uses the files in the working tree.

## Commands

Automated readiness, which does not call verifiers:

```text
python -c "from evaluation.experiments.experiment3.execution_readiness import execution_report; import json; print(json.dumps(execution_report(), indent=2))"
```

Status manifest without verifier calls:

```text
python evaluation/experiments/experiment3/collection_gate.py
```

Full Development collection. This resumes `evaluation/experiments/experiment3/empirical/verifier_reports.jsonl` and does not open Final Test labels:

```text
python evaluation/experiments/experiment3/empirical_executor.py
```

A one-candidate probe, which is not the experiment:

```text
python evaluation/experiments/experiment3/empirical_executor.py --limit 1
```

Tests that do not call the live verifiers:

```text
python -m pytest tests/test_experiment3_approval_package.py tests/test_experiment3_prerequisites.py tests/test_experiment3_empirical_integration.py tests/test_experiment3_resource_sensitivity.py evaluation/tests/test_experiment3_execution_gate.py -q --tb=line
```

## Bound inputs

| Input | SHA-256 or identifier |
| --- | --- |
| Execution configuration | `5c7e026db04a4623b53e4f12c79c9cc150e53a71059b4fae55117461418874ee` |
| Eligibility manifest, complete file | `1ebb4357d599a52d1c1fc8d8951ab39fa6992e846cf997d9e588820c87cbe731` |
| Dependency configuration | `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d` |
| Calibration id | `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d` |
| Coefficient | `1.3399597937725295e-05` loss per millisecond |
| Budget | `14996.39091498102` milliseconds |
| Bootstrap | 2000 resamples, 95% interval, seed `20261113`, groups as the resample unit |
| Reputation | `Beta(1, 1)`, 0 approved observations, no decay |
| Generator | local Ollama `llama3.2:3b` at `http://127.0.0.1:11434`, 5 samples, temperature 0.8 |
| Evidence corpus | Development corpus SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` |

Model-weight snapshot hashes are `UNKNOWN`. They were not invented.

## Collection that produced the stored results

An earlier process, `python evaluation/experiments/experiment3/empirical_executor.py`, started at `2026-11-14T09:00:04.556Z` and was aborted at `2026-11-14T11:16:44.119Z` (exit code 1, elapsed 8199563 ms) after logging 604 collected candidates. Reports already written were kept.

The completing process was:

```text
python -u evaluation/experiments/experiment3/empirical_executor.py
```

It started at `2026-11-14T11:24:21.194Z`, logged 138 additional HotpotQA collections, and ended at `2026-11-14T11:56:55.911Z` with exit code 0 and elapsed 1954717 ms. Stdout ended with `{"status": "COMPLETE", "completed_cells": 15624, "candidates": 744, "final_test_accessed": false}`.

Do not run `empirical_runner.py` against `evaluation/experiments/experiment3/empirical`. That entry point writes a not-collected status and would replace `results.json`.

The empirical figure, which does not call verifiers:

```text
python evaluation/experiments/experiment3/write_empirical_figure.py
```

## Outputs

Prior not-collected files remain in `evaluation/experiments/experiment3/empirical/prior_not_collected/`. They are not the experiment. `smoke_results.json` is the two-candidate probe and is not the experiment.

| Output | SHA-256 | Bytes |
| --- | --- | ---: |
| `empirical/results.json` | `82324e96da71095bf1f2e75a2c080a396151590671111a91d7a870a6a657f8f8` | 33384864 |
| `empirical/metrics.json` | `2c186172e5f1e9e2c2f344292d0b5a093a11e8fbb746294bde6cb54faeb08c57` | 48945 |
| `empirical/bootstrap_results.json` | `2b56ac693740bfdbee00dcf788c0bb4a097d7f70c3ad78b3335bd6b120dce53a` | 1411 |
| `empirical/verifier_reports.jsonl` | `877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5` | 11064096 |
| `empirical/figures/attack_validation_loss.svg` | `8be472c94d29b34caec0829065afcc21eb059b746d0d31f8b2871fc7465b1dd4` | 3978 |

Completed cells: 15624. Candidates: 744. Groups: 372. `final_test_accessed`: false. Evidence label: `EMPIRICAL`.

## Environment

Python 3.12.1 on `PATH`. Platform recorded in the run manifest: `Windows-11-10.0.26300-SP0`. Git commit `5485c54eaaecc1e338d4b1e3b889353a7a34ce98` on branch `raunak-exp-3`. The working tree is dirty, so that commit alone does not contain this run. Ollama was reachable with `llama3.2:3b` at `http://127.0.0.1:11434` when collection ran. Package versions were not re-frozen. The environment manifest remains `OBSERVED_NOT_APPROVED`. The post-collection test command above passed 51 tests.

The completion record is `evaluation/experiments/experiment3/empirical/run_manifest.json`. It records `gate_status` `EMPIRICALLY_COMPLETED`, 15,624 rows, `final_test_accessed` false, and `historical_approval_gate` `READY_FOR_APPROVAL`. The historical approval package remains unsigned. No signed policy artifact was written.
