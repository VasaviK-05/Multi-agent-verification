# Experiment 1 reproducibility

The replay command is:

```text
python -u evaluation/experiments/experiment1/offline_replay.py
```

It reads `evaluation/experiments/experiment3/empirical/verifier_reports.jsonl` and the Development eligibility inputs. It refuses a destination under Experiment 3 empirical outputs or a path containing `final_test`. Before and after scoring, it checks these frozen SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Experiment 3 `results.json` | `82324e96da71095bf1f2e75a2c080a396151590671111a91d7a870a6a657f8f8` |
| Experiment 3 `metrics.json` | `2c186172e5f1e9e2c2f344292d0b5a093a11e8fbb746294bde6cb54faeb08c57` |
| Experiment 3 `bootstrap_results.json` | `2b56ac693740bfdbee00dcf788c0bb4a097d7f70c3ad78b3335bd6b120dce53a` |
| Experiment 3 `verifier_reports.jsonl` | `877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5` |
| Experiment 3 `figures/attack_validation_loss.svg` | `8be472c94d29b34caec0829065afcc21eb059b746d0d31f8b2871fc7465b1dd4` |

Those five hashes matched before the replay and again after it. The completed command printed `candidates` 744, `greedy_infeasible` 234, and `final_test_accessed` false. Runtime on this machine was about 107 seconds.

## Experiment 1 artifact hashes

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `evaluation/experiments/experiment1/offline_replay.py` | 22764 | `4ef0f29c3387d410d04f76c419cd5591c55510d9bc57d47d6bdbd3381de9405a` |
| `development/results.json` | 15176181 | `0ce2de3caa2705cafe12877efe1345dce904def6116f5e239c3cccfd07684145` |
| `development/metrics.json` | 25545 | `898766ea5b0f52d5bd071a74deb5ec377e18209258d5a6b1f84409fe87fd23d4` |
| `development/bootstrap_results.json` | 1504 | `ce87a818cca59417ce8a99665b45b719bbe0801370eca0c83bdd82629a25f941` |
| `development/policy_manifest.json` | 2105 | `3e2bc3d546df782dc804edc6250499c8d0b980b53de921036fd4a96e13b2aec6` |
| `development/figures/method_decision_loss.svg` | 3610 | `d80892331ba9d0664d651b7b74a9003af5386a034cd7d08609eb234800b1748d` |

The figure text contains `EMPIRICAL` and does not contain `SYNTHETIC`.

## Tests

`python -m pytest tests/test_experiment1_offline_replay.py -q --tb=short` checks the probability rules, the worst-column tie-break, the destination guard, that the selector plan does not call a verifier, the frozen Experiment 3 hashes, and the completed policy manifest. The first five tests passed before the replay. The manifest assertion was added after the replay and is run with the suite.

## Recorded deviations

- Suppression is absent, as in Experiment 3.
- Greedy aggregation is `reputation_weighted` because the pilot proposal names it and the Experiment 1 proposal does not.
- Question requirements come from the keyword heuristic. The optional Ollama analyzer was not called.
- The selector still uses its dimensionless cost and latency profiles. Feasibility is then judged with the Experiment 3 millisecond budget. The confidence + evidence + rule team fails that budget for 234 candidates.
- `deterministic_minimax` can coincide with full minimax, and it does here. The rule was not edited to force that coincidence.
- Re-running the command rewrites the Experiment 1 development files. It does not rewrite Experiment 3.

These outputs are uncommitted. Experiment 3 remains at commit `22dbf42fcb8e75f5255a64c95248e75fedd57f55`.
