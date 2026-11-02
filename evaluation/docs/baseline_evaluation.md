# Baseline Evaluation of the Multi-Agent Answer Validation Framework

## 1. Experiment title

Baseline evaluation of the game-theoretic multi-agent framework for adaptive AI answer validation, under the existing non-adversarial `execution_mode="baseline"` pipeline.

## 2. Research objective

Measure how the implemented validation framework behaves on a fixed development mixture of fact verification, multi-hop question answering, and arithmetic reasoning, without adversarial inputs and without changing verifier logic, thresholds, reputation formulas, or selection rules. These measurements are the reference for later adversarial, cost–accuracy, and game-theoretic comparisons.

## 3. Research question

When the existing orchestrator is run in baseline mode on the unified development set, what definitive-decision quality, abstention behavior, and verification cost does the unmodified pipeline produce?

## 4. Experimental hypothesis

Under cold-start reputation and the default selector, the baseline pipeline will often abstain. Word-problem arithmetic does not match the rule verifier’s implemented patterns, and the configured evidence corpus does not contain the benchmark evidence pages. The hypothesis is therefore descriptive: coverage and selective accuracy will be limited by those implementation boundaries, not by a claim that the current pipeline is already accurate on these benchmarks. This hypothesis is not used to change the system.

## 5. Framework architecture and baseline execution behavior

`ValidationOrchestrator(execution_mode="baseline")` runs four stages. It does not run a game-theoretic team selector.

1. `QuestionAnalyzer.analyze` classifies the question. With `ANALYZER_MODE` unset, the constructor default is the surface heuristic, not Ollama. The project `.env` does not set `ANALYZER_MODE`.
2. `VerifierSelector.plan` takes one reputation snapshot and builds a coverage-greedy team. The registered order is semantic, evidence, rule, confidence. Semantic is ineligible when reference context is missing or is a judgment-label list. The plan returns `initial_selected` and a `fallback` queue. It does not execute verifiers. Target size depends on difficulty: easy selects 2, medium 2 or 3, hard 3 or 4, and required coverage can add specialists beyond a soft target. Baseline therefore does not mean “always run all four verifiers.”
3. The orchestrator walks `initial_selected` and then `fallback`. Each name is resolved lazily and cached. A result is marked abstention when verifier metadata decision is `UNSURE`. `AdaptiveEarlyTermination` may approve a stop, but the orchestrator vetoes that approval when requirements are unknown or invalid, when unsupported requirements remain, when the initial team is incomplete, when the question is hard, or when a requested capability has no directional vote. Hard questions never stop early. If every veto blocks the stop, execution ends at `candidate_exhaustion`.
4. `DecisionEngine.decide_detailed` aggregates directional votes. Verifier decisions are `SUPPORT`, `REJECT`, and `UNSURE`. The engine’s status is `passed`, `failed`, `uncertain`, or `unknown` (no results). Cuts on the signed score in [-1, 1], with default threshold 0.55, are: score above 0.55 is `passed`, score below -0.55 is `failed`, and the band between them is `uncertain`. The score is not a probability. The orchestrator then forces `final_status="uncertain"` when contributing votes are below the minimum, required coverage is missing, or coverage requirements are invalid. `UNSURE` verifier outputs and `uncertain`/`unknown` framework statuses are abstentions. They are not rejections.

`validate` does not update reputation. Reputation changes only in `record_ground_truth`, which this experiment never calls.

The experiment injects a new `ReputationManager` with the default prior alpha = 1, beta = 1, so every domain reputation starts at 0.5 and stays there. The default orchestrator constructor would instead load PostgreSQL reputation. That path is not used, so stored feedback cannot affect this run and this run writes nothing back. At reputation 0.5 every log-odds weight is 0, and the decision engine falls back to equal-weight aggregation of directional votes.

Automatic Wikidata ground truth inside baseline `validate` only handles “capital of” questions and returns no label otherwise. Benchmark labels come from the dataset adapters, not from that field.

## 6. Dataset description

Source file, read only: `evaluation/datasets/unified/development.json`.

The file contains 2,000 examples. The final-test split is not used.

| Benchmark | Examples | Task stored in the file |
|---|---:|---|
| FEVER | 500 | Fact verification. Labels: SUPPORTS 167, REFUTES 162, NOT ENOUGH INFO 171. |
| HotpotQA | 500 | Multi-hop question answering. Each example has two candidate answers. |
| GSM8K | 500 | Arithmetic word problems. Each example has two candidate answers. |
| MultiNLI | 500 | Premise, hypothesis, and entailment / neutral / contradiction. |

GSM8K candidates are the gold number (`benchmark_gold`, `expected_correct=true`) and one numeric perturbation (`synthetic_numeric_perturbation`, `expected_correct=false`). HotpotQA candidates are the gold answer and one answer taken from another example (`synthetic_cross_example_answer`). The perturbation and cross-example strings are fields already stored on the example. They are not recomputed and they are not used as evidence for any other example.

The evaluation unit for GSM8K and HotpotQA is one stored candidate. That produces 1,000 instances per benchmark. FEVER has one instance per claim (500). Eligible instances: 2,500. MultiNLI examples are skipped (500).

## 7. Dataset-specific input mappings

| Benchmark | Question | Candidate answer | Context | Gold role |
|---|---|---|---|---|
| GSM8K | The example question | Each `candidate_answers[].answer` | `null` | `accept` if `expected_correct` is true, otherwise `reject` |
| HotpotQA | The example question | Each `candidate_answers[].answer` | That example’s own paragraphs, including distractors, joined as title plus text | Same boolean mapping as GSM8K |
| FEVER | The claim text | The same claim text | `null` | SUPPORTS → `accept`; REFUTES → `reject`; NOT ENOUGH INFO → `abstain` |
| MultiNLI | Not submitted | Not submitted | Not submitted | Skipped |

FEVER claims are statements. The existing claim generator keeps a statement answer as the claim under test, so the evidence and confidence verifiers see the claim rather than the token “true.” The dataset does not contain evidence sentences. `evidence_urls` are Wikipedia titles. A title overlap check against `EVIDENCE_CORPUS_PATH` (`data/articles_13083.json`, 13,083 articles) found 0 of 301 distinct FEVER titles in the corpus. 171 FEVER rows have an empty URL list, matching the NOT ENOUGH INFO count. Gold FEVER evidence is not available to the evidence verifier.

HotpotQA context is passed because the semantic verifier requires reference text and refuses to run without it. The evidence verifier does not retrieve from `request.context`. It uses the same global corpus. Of 500 HotpotQA examples, 7 have any context title in that corpus, 0 have all supporting-fact titles in the corpus, and 1 of 1,000 supporting-title occurrences is present. Passing context therefore enables semantic comparison only. It does not supply gold evidence to retrieval.

MultiNLI is skipped. The framework decides whether a candidate answer is acceptable. Treating the hypothesis as an answer and the premise as a semantic reference would score cosine similarity, which the semantic verifier itself describes as resemblance rather than entailment.

A framework `passed` matches gold `accept`. A framework `failed` matches gold `reject`. `uncertain` and `unknown` match only gold `abstain`. An abstention is never scored as a rejection.

## 8. Experimental configuration

- Orchestrator: `ValidationOrchestrator(reputation_manager=ReputationManager(), execution_mode="baseline")`.
- Selector, decision engine, early stopping, and verifier constructors: their defaults. No threshold, cost, or reputation edits.
- Analyzer: process default, which is the heuristic.
- Evidence corpus: the environment path `data/articles_13083.json`.
- Seed: `random.seed(0)`. Self-consistency sampling, when the confidence verifier runs, uses its own seeds `0 .. n_samples-1`.
- One orchestrator is reused so embedding and NLI models are constructed once.
- Resume: `baseline_results.jsonl` is appended. An `instance_id` already present is not run again and previous lines are not rewritten.

## 9. Evaluation methodology

For each eligible instance the adapter builds a `ValidationRequest`, `validate` is called, and wall-clock latency is recorded around that call. Exceptions are stored with type, message, and traceback. They are not dropped.

Framework `final_status` is the decision being scored. Verifier `metadata.decision` is recorded separately. `final_score` and `signed_score` are stored and are not treated as calibrated probabilities.

Smoke test, kept separate under `evaluation/results/baseline/smoke/`: the first two FEVER examples, the first two GSM8K examples, and the first HotpotQA example in file order. Both candidates are run for GSM8K and HotpotQA, so the smoke file contains 8 instances. Smoke output is not an input to the full summary.

The full run then executes every eligible instance.

## 10. Metric definitions and formulas

Let \(N\) be the number of completed instances. Let \(A\) be the number whose framework status is `uncertain` or `unknown`. Let \(D = N - A\) be the number of definitive statuses (`passed` or `failed`). Let \(C\) be the number whose status matches the gold role, including gold abstention.

- Accuracy \(= C / N\). An abstention on a gold accept or gold reject is not correct.
- Coverage \(= D / N\).
- Abstention rate \(= A / N\).
- Selective accuracy \(= C_D / D\), where \(C_D\) counts matches among definitive predictions only. Gold abstention predicted as `passed` or `failed` is a definitive error.

Precision, recall, and macro F1 are computed only on definitive predictions whose gold role is binary (`accept` or `reject`). Abstentions are left out of these counts.

- True accept: `passed` and gold `accept`.
- False accept: `passed` and gold `reject`.
- False reject: `failed` and gold `accept`.
- True reject: `failed` and gold `reject`.
- Precision \(= TP / (TP + FP)\). Recall \(= TP / (TP + FN)\). Accept F1 is the harmonic mean of those two.
- Macro F1 is the unweighted mean of accept-class F1 and reject-class F1. Reject-class false positives are the false rejects above, and reject-class false negatives are the false accepts.

False acceptance rate \(=\) (gold `reject` predicted `passed`) / (all gold `reject` instances), including gold rejects on which the system abstained. False rejection rate \(=\) (gold `accept` predicted `failed`) / (all gold `accept` instances). Gold `abstain` is in neither denominator. `uncertain` is not counted in the numerator of either rate.

Latency is the wall-clock time of `validate`, in milliseconds. The summary reports the mean, the sample median, and the linear-interpolated 95th percentile. Total execution time is the sum of instance latencies and the runner wall clock. Verifier calls are `len(execution_audit["attempted_verifiers"])`, which includes a verifier that was invoked even if it later abstained. Selection frequency counts names in `selection_plan.initial_selected`. Execution frequency counts names in `attempted_verifiers`.

## 11. Actual results

### 11.1 Smoke test

The smoke test is not the baseline result. It is recorded here so it cannot be confused with the full run.

Command: `evaluation/baseline/run_baseline_experiment.py --smoke 5`.

Completed instances: 8. Execution failures: 0. Wall clock: 145.48 seconds. Sum of instance latencies: 145,467.328 ms.

| Benchmark | Instances | Accuracy | Coverage | Abstention rate | Selective accuracy | Mean latency (ms) | Mean verifier calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| FEVER | 2 | 0.0 | 0.0 | 1.0 | n/a | 12,495.761 | 3.0 |
| GSM8K | 4 | 0.0 | 0.0 | 1.0 | n/a | 15,785.986 | 3.0 |
| HotpotQA | 2 | 0.0 | 0.5 | 0.5 | 0.0 | 28,665.930 | 4.0 |
| Overall | 8 | 0.0 | 0.125 | 0.875 | 0.0 | 18,183.416 | 3.25 |

Overall smoke decision counts: `failed` 1, `uncertain` 7. The single definitive decision was a HotpotQA gold-accept candidate classified `failed` (selective accuracy 0 on that one definitive case). False acceptance rate on the smoke set was 0. False rejection rate was 0.2 (1 / 5 gold-accept instances).

No production verifier was changed after inspecting this output. The full run uses the same code path.

### 11.2 Complete development run

The complete-run tables below are filled from `evaluation/results/baseline/baseline_summary.json` after that run finishes. Until that file exists, this subsection has no measured full-set numbers.

## 12. Benchmark-wise result tables

See section 11.2. Per-benchmark blocks in `baseline_summary.json` use the same metric definitions as section 10.

## 13. Decision distribution

See section 11.2. Counts are framework statuses, not verifier `SUPPORT` / `REJECT` / `UNSURE` counts.

## 14. Efficiency analysis

See section 11.2 for mean, median, and p95 latency, total latency, and verifier call counts. Selection and execution frequencies are separate fields in the summary file.

## 15. Observations and interpretation

Smoke observations, which do not estimate the full set:

- Every smoke instance exhausted the candidate queue (`candidate_exhaustion`). Early stopping did not approve a stop.
- GSM8K and FEVER selected `rule` and `evidence`. Semantic was not eligible because context was null. Confidence was not in the initial team but still executed from the fallback queue, because unknown or uncovered requirements veto early stopping.
- HotpotQA selected `rule` and `semantic` once context was present, then still executed evidence and confidence.
- The rule verifier abstained (`UNSURE`, unsupported) on these word problems and claims. That matches its documented limit to implemented arithmetic patterns.
- Evidence usually abstained with `no_relevant_evidence`, which is consistent with the corpus overlap check. One FEVER claim received an evidence `REJECT` from the unrelated corpus. That vote is not gold FEVER evidence.
- Where only one directional vote remained, the orchestrator often returned `uncertain` for `insufficient_contributors` rather than adopting that vote. The minimum contributor count is the difficulty-band minimum, at least 2 for easy and medium questions.

Full-set interpretation will be added only from the complete summary.

## 16. Limitations

- MultiNLI cannot be scored with this interface without treating similarity as entailment. All 500 development examples are skipped and listed in `baseline_errors.json`.
- FEVER gold evidence text is not in the request or in the configured corpus. FEVER metrics measure the pipeline without benchmark evidence. They are not a standard FEVER score.
- HotpotQA gold supporting pages are essentially absent from the retrieval corpus. Semantic similarity to the example’s own context is not multi-hop correctness. The semantic verifier states that low similarity is not evidence of falsity.
- GSM8K word problems are not the closed arithmetic expressions the rule verifier implements. Candidate perturbations are synthetic offsets stored in the dataset, not independent human wrong answers.
- Cold-start equal-weight aggregation is the behavior of an isolated prior. It is not the behavior of a database that already contains feedback.
- Confidence may call the configured Ollama sampler. If that service is unavailable, the verifier abstains. Latency includes that call when it is attempted. This run does not disable it.
- `final_score` is a rounded signed vote, not a probability. Precision and recall are not computed by thresholding that score.
- Older smoke latency includes model load on the first instance. The full run loads models again in its own process.

## 17. Reproducibility instructions

From the repository root, using the existing virtual environment:

```text
.venv\Scripts\python.exe evaluation\baseline\run_baseline_experiment.py --smoke 5
.venv\Scripts\python.exe evaluation\baseline\run_baseline_experiment.py
```

The full command resumes from `evaluation/results/baseline/baseline_results.jsonl` and will not duplicate an `instance_id`. Smoke results stay in `evaluation/results/baseline/smoke/`.

Outputs:

- `evaluation/results/baseline/baseline_results.json`
- `evaluation/results/baseline/baseline_results.csv`
- `evaluation/results/baseline/baseline_summary.json`
- `evaluation/results/baseline/baseline_errors.json`
- `evaluation/results/baseline/baseline_results.jsonl` (checkpoint)

Do not point the run at `evaluation/datasets/unified/final_test.json`. Do not edit the dataset files.

## 18. Conclusion

The smoke test shows that the unmodified baseline path runs, records abstentions separately from rejections, and does not throw on the five sampled examples. A conclusion about development-set accuracy waits on the complete summary and is not inferred from the smoke sample.

## Corpus preflight used in sections 6 and 7

Measured against `data/articles_13083.json` before the full run:

- FEVER: 0 / 301 distinct evidence titles occur as corpus titles or URL slugs. 0 / 500 examples have any cited title in the corpus.
- HotpotQA: 7 / 500 examples have any context title in the corpus. 0 / 500 have every supporting-fact title in the corpus. 1 / 1,000 supporting-title occurrences match.
