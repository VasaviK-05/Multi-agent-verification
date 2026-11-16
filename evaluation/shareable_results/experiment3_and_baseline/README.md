# Experiment 3 and baseline results

Shareable Development results for the Experiment 3 aggregation comparison and the Experiment 1 selection comparison. The package contains the findings, the paired intervals, and the empirical figures. It does not contain raw verifier reports, the full result tables, credentials, or datasets.

Evidence in the numbered documents is empirical unless a sentence names a policy analysis or a synthetic control. No synthetic figure is included.

Experiment 3 source commit: `22dbf42fcb8e75f5255a64c95248e75fedd57f55`. The Experiment 1 replay is scored from that commit's verifier reports. This folder does not replace either source directory.

## Read in this order

1. This README
2. [01_experiment3_results.md](01_experiment3_results.md)
3. [02_experiment1_baseline_results.md](02_experiment1_baseline_results.md)
4. [03_experiment3_vs_baselines.md](03_experiment3_vs_baselines.md)
5. [04_research_conclusions_and_limitations.md](04_research_conclusions_and_limitations.md)

Figure captions are in [figures/captions.md](figures/captions.md).

## Figures for a presentation

Use these three, in this order:

1. `figures/experiment3_attack_loss_by_method.svg` — the three aggregation methods match on every attack.
2. `figures/experiment3_team_selection.svg` — evidence + rule is the unique lowest worst-case team.
3. `figures/paired_differences_versus_full_minimax.svg` — fixed team matches minimax; uniform and feasible greedy have higher paired loss, on different group counts.

`figures/experiment1_baseline_decision_loss.svg` is useful only with the caption. Its greedy series uses 510 candidates per attack, while the other series use 744.

## Where the originals are

| Package file | Original |
| --- | --- |
| Experiment 3 prose numbers | `evaluation/experiments/experiment3/empirical/metrics.json` and `bootstrap_results.json` |
| Experiment 3 cells | `evaluation/experiments/experiment3/empirical/results.json` |
| Verifier reports | `evaluation/experiments/experiment3/empirical/verifier_reports.jsonl` |
| Experiment 3 figures | `evaluation/experiments/experiment3/empirical/figures/` |
| Experiment 1 numbers | `evaluation/experiments/experiment1/development/metrics.json`, `bootstrap_results.json`, and `policy_manifest.json` |
| Experiment 1 figure | `evaluation/experiments/experiment1/development/figures/method_decision_loss.svg` |
| Longer research notes | `evaluation/docs/experiment3_final_research_synthesis.md`, `experiment3_paper_integration.md`, `experiment3_limitations.md`, `experiment3_reproducibility.md`, `experiment3_visualization_report.md`, `experiment3_policy_diagnosis.md`, `experiment1_offline_replay.md`, `experiment1_reproducibility.md` |

`metrics.json` repeats each slice for all three aggregation methods. Its top-level correctness counts are three times the one-method counts. The documents in this folder use the one-method counts: 126, 586, 110, 415, and 3971.

## Reproduce

Experiment 3 was already collected. Do not rerun `empirical_executor.py` against the empirical directory.

Confirm the frozen SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `results.json` | `82324e96da71095bf1f2e75a2c080a396151590671111a91d7a870a6a657f8f8` |
| `metrics.json` | `2c186172e5f1e9e2c2f344292d0b5a093a11e8fbb746294bde6cb54faeb08c57` |
| `bootstrap_results.json` | `2b56ac693740bfdbee00dcf788c0bb4a097d7f70c3ad78b3335bd6b120dce53a` |
| `verifier_reports.jsonl` | `877d0218dd498e8ca525e651f52f8aa1e337cd6f5123583fb277a2a28e01eca5` |
| `figures/attack_validation_loss.svg` | `8be472c94d29b34caec0829065afcc21eb059b746d0d31f8b2871fc7465b1dd4` |

The Experiment 1 replay, which only rereads the frozen reports, is:

```text
python -u evaluation/experiments/experiment1/offline_replay.py
```

That command rewrites the Experiment 1 development files. It refuses to write into the Experiment 3 empirical directory. Tests that do not rescore the corpus:

```text
python -m pytest tests/test_experiment1_offline_replay.py -q --tb=short
```

## Limitations

Development only. Policies were fit and scored on the same rows. Incorrect candidates are synthetic. Reputation is a cold start. Dependencies are assumed. The budget and loss coefficient were selected, not optimized. Greedy has no loss on 117 groups. Final Test was not used. Details are in `04_research_conclusions_and_limitations.md`.
