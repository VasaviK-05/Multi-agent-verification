# Experiment 2 — Supplementary Development Results

## Scope and status
This package contains supplementary summaries derived from two frozen, task-conditioned Development policies in `multitask-prototype42-current-v1-rerun1` (arithmetic and factual). These are **not** the three-budget Experiment 2 evaluation and must not be presented as budget-sensitivity results.

No three-budget loss curve, budget-specific strategy distributions, matched feasible baselines, or raw per-attempt timing observations for box plots are included. No Final Test outcomes were used to create these summaries.

## Source artifact identities
- Arithmetic artifact ID: `1a336129b0c32b8634e434be7c1ff3a8ef73f79353270be03ce61ecf2e91f697`
- Arithmetic policy ID: `99d261fcf126e930fa4f0becd7c763ec4224c2e436db7bbe05b64922a6e87f6b`
- Arithmetic calibration ID: `357ca8dc3dfb273de028ba4bd7b317b6b223fb8c907d2513bcd1228452cf3c13`
- Factual artifact ID: `d65f9a06e87621225d948cc3412f1098141893460e360661a08fb105cdc38dbb`
- Factual policy ID: `952305abb963f1149ea605ac4183cf8e0d830860d82078df25471068f1cc050c`
- Factual calibration ID: `42ad21401196b164eee5847d1b1f1b1d211fa7302bd9e0224e807ebdac181f04`
- Execution configuration ID (both): `898af00e993768ab1d2d320a4cd2d743187ccb475979a39072c1bc8deabf96d7`

## Summary
| Metric | Arithmetic | Factual |
|---|---:|---:|
| Development clean coverage | 50% | 25% |
| Game value / worst-case loss | 0.38485 | 0.32000 |
| Expected estimated cost | 7,253.05 ms | 9,230.43 ms |
| Candidate strategies | 14 | 14 |
| Positive-probability strategies | 3 (one is a tiny numerical residual) | 2 |
| Solver status | Optimal | Optimal |

## Interpretation
- Probabilities and verifier inclusion values are copied/calculated from frozen policy outputs. Arithmetic's third strategy has probability about 0.000034%, a numerical residual rather than a meaningful selection.
- Expected costs are policy-level estimates in milliseconds, not observed end-to-end request latency.
- Arithmetic latency CSV contains measured means, medians, P95 and counts from 80 attempts per verifier, with zero failures. Its chart shows means on a logarithmic scale; it is not a box plot.
- Factual latency CSV contains mean attempt costs from the episode context only. The supplied extract did not include raw timing distributions, median or P95, so none are invented.
- Verifier inclusion is the sum of strategy probabilities for strategies containing that verifier; it is not an independent selection probability.

## Contents
- `tables/`: CSV summaries.
- `figures/`: PNG charts.
- `supplementary-results/`: empty folders reserved for copies of original frozen JSON artifacts. The originals are not embedded; copy them from the source build directory without modifying them.

## Reproducibility and safety
Preserve source build directories and frozen artifacts unchanged. Keep this package labelled supplementary until the Experiment 2 specification, approved Development evaluation context and three budget levels are confirmed. Do not run or inspect Final Test for this work.
