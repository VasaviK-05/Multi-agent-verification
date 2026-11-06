# Dataset selection recommendation

## Recommendation

Use **GSM8K as the arithmetic population**, after a development-only candidate audit and with the limitation that existing rule verification supports narrow/direct arithmetic patterns rather than the full word-problem distribution. That verifier limitation is not a population marker. Direct arithmetic is not a separate experimental population in `research_v1`: no verified subset, annotation, or direct-arithmetic flag exists, so no direct-arithmetic count is claimed.

Use **HotpotQA as a factual question-answering population only for a reference-assisted condition** unless a frozen configured corpus with adequate supporting evidence is selected and verified. The existing shared corpus has virtually no supporting-page coverage. The supplied HotpotQA contexts contain reference material and supporting-fact annotations, making it the strongest of the available factual QA sources for a reference-assisted interface-compatible condition. Every method must get the same permitted paragraphs. The current synthetic negative candidate needs independent adjudication.

Treat **FEVER as an optional separate claim-verification task**, not as ordinary question-answer validation. It has independent SUPPORTS/REFUTES/NOT ENOUGH INFO labels, but the present adapter puts the claim in both question and candidate answer and supplies no evidence text. Direct title checks find no FEVER cited title in the configured corpus. NOT ENOUGH INFO is an abstention/unknown-evidence class and must not be converted into a false candidate. Include FEVER only if the team accepts this task mapping and chooses an evidence condition that is explicit and shared.

Do not force **MultiNLI** into the answer-validation interface. Its labels concern premise-hypothesis entailment, not answer correctness for a question.

## Observed scale and suitability

| Dataset | Local source size | Existing unified sample | Candidate construction | Interface/evidence fit |
|---|---:|---:|---|---|
| GSM8K | 7,473 train; 1,319 test | 2,000 history, 500 development, 500 final-test questions | Gold numeric answer plus gold+1 synthetic candidate | Fits question/answer interface; no reference text; candidate negative needs validation. |
| HotpotQA distractor | 90,447 train; 7,405 validation | 2,000/500/500 questions | Gold answer plus another question's gold answer | Fits question/answer interface; reference context available; shared corpus lacks supporting pages for nearly all sampled questions. |
| FEVER v1.0 | 311,431 train rows; 18,999 paper-dev rows; 18,567 paper-test rows (annotation rows before grouping) | 2,000/500/500 unique claims | One claim with benchmark label; no correct/incorrect candidate pair | Claim-verification task; referenced evidence text absent; 0 sampled titles overlap configured corpus. |
| MultiNLI | 392,702 train; 9,815 matched validation; 9,832 mismatched validation | 2,000/500/500 | No answer candidates | Not compatible with this interface. |

The “existing unified sample” is not endorsed as a final selection or split. Its samples are audit material and the present final-test file is already locally exposed.

## Candidate-quality conditions

GSM8K gold answers are derived from the benchmark's final-answer marker. The existing wrong answer is a numeric increment, not a naturally generated or independently adjudicated error. Validate numeric equivalence, units, formatting and whether the problem admits the candidate through a different interpretation. If any item is ambiguous, record it and exclude only under a predeclared exclusion rule with a reason; do not silently discard it.

HotpotQA gold answers are benchmark labels. The cross-example negative is a heuristic only: it may be correct by coincidence, be a valid alias, or be compatible with a broad question. Independently verify every proposed negative against the gold reference and permitted context; store annotator/reviewer, adjudication, and provenance. Candidate correctness should be attached to each question-answer pair.

## Computational feasibility

The existing baseline contains 1,232 completed records and demonstrates that selected batches have been processed. It does not establish the cost of the game-theoretic protocol. Begin with a Development pilot, record wall time and attempt count, estimate per-example cost, then approve a sample size and method budget. Do not infer a universal split ratio from the current 2,000/500/500 files.

## Decisions before final inclusion

Approve benchmark populations and task mapping; decide corpus-only versus reference-assisted factual evaluation; independently adjudicate negative candidates; define exclusion and group rules; and reserve a new, protected final-test pool. Direct arithmetic is excluded as a separate `research_v1` population, as recorded below. Until the remaining items are approved, neither benchmark is ready as a final research dataset.

## Selected research_v1 population

The built population is `research_v1`, configured by `evaluation/config/research_dataset.yaml` and recorded in `evaluation/datasets/reconciled_candidates/research_v1/manifest.json` and `validation_summary.json`. Final Test is disabled (`final_test.enabled: false`, `source: null`). The manifest records `final_test_records_or_identities_accessed: false`.

A question group is one source question. A candidate record is one answer attached to that question. Group counts are not candidate counts.

| Population | Question groups | History groups | Development groups |
|---|---:|---:|---:|
| GSM8K | 500 | 300 | 200 |
| HotpotQA | 500 | 300 | 200 |
| **research_v1 total** | **1,000** | **600** | **400** |

Candidate records for the same groups, from `validation_summary.json` `quality.benchmarks`:

| Benchmark | Question groups | Candidate records | Verified correct | Verified incorrect | Unresolved |
|---|---:|---:|---:|---:|---:|
| GSM8K | 500 | 1,000 | 464 | 215 | 321 |
| HotpotQA | 500 | 1,050 | 500 | 0 | 550 |
| **Combined** | **1,000** | **2,050** | **964** | **215** | **871** |

GSM8K has 500 `benchmark_gold` records and 500 `synthetic_numeric_perturbation` records. HotpotQA has 500 `benchmark_gold` records, 500 `synthetic_cross_example_answer` records, and 50 preserved `explicit_negation_of_context_supported_benchmark_answer` records. History holds 1,240 candidate records (GSM8K 600, HotpotQA 640). Development holds 810 (GSM8K 400, HotpotQA 410).

`quality_control.retain_unresolved` is true and `exclude_unresolved_from_binary_examples` is true. Unresolved candidates stay in the reconciled files and are excluded from binary offline examples. They are not relabeled as incorrect. Offline preparation reports 1,179 prepared labelled candidates and 871 excluded unresolved candidates. It also reports zero complete verifier attempt records and zero complete offline examples. `policy_fitting_ready` is false.

## FEVER

FEVER is excluded from `research_v1`. The YAML benchmark list and the manifest counts contain only GSM8K and HotpotQA. That exclusion is a dataset-selection decision for this version. It does not mean the framework cannot accept a FEVER-style claim, and it does not withdraw the optional claim-verification use described above. A later FEVER population would need its own approved task mapping and evidence condition.

## HotpotQA input condition

HotpotQA in `research_v1` is a source/reference-context condition. Gold candidates are checked against the benchmark answer and the supporting passages supplied with that question. Prepared verifier input may include those permitted passages. This does not evaluate retrieval against the shared Evidence Verifier corpus, and it does not measure whether that corpus contains the supporting pages.

## Candidate-label limitations

GSM8K incorrect labels use the narrow gold+1 rule recorded in the manifest: `narrow discrete-count +1 rule with independently replayed source equations`. A perturbation is `verified_incorrect` only when that existing discrete-count rule accepts it. Other gold+1 candidates stay `unresolved`. This is not a sample of natural wrong answers.

HotpotQA has zero `verified_incorrect` candidates in `research_v1`. Borrowed cross-example answers stay unresolved. The manifest records `hotpotqa_borrowed_candidates_automatically_incorrect: false` and `prior_explicit_negation_statuses_demoted_to_unresolved: 50`. The 50 explicit-negation records from the prior pilot remain unresolved in this version. `human_adjudication_claimed` is false.

## Source, version, and license

Verified from `manifest.json` `source_versions` and the local dataset metadata files:

| Benchmark | Source path used by the build | Version string in the manifest | License in local `dataset_info.json` | Citation in local `dataset_info.json` |
|---|---|---|---|---|
| GSM8K | `evaluation/datasets/raw/gsm8k/train` plus unified History/Development | `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866` | Empty. License text is pending. | Empty. Citation text is pending. |
| HotpotQA | `evaluation/datasets/raw/hotpotqa/train` plus unified History/Development | `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab` | Empty. License text is pending. | Empty. Citation text is pending. |

No license or citation string is invented here. Confirm both against the benchmark release before redistribution. The manifest records SHA-256 hashes for the YAML config, the unified History/Development files, the train split files that were read, and the prior reconciled v1 inputs.

## Verifier eligibility

`research_dataset.yaml` does not name verifiers or eligibility restrictions. No verifier-eligibility rule is treated as approved for `research_v1`. Pending approval: which verifiers may run, whether source-replay and controlled-construction labels qualify as scientific ground truth, and which question groups are in scope for a given verifier. Whether the Rule Verifier applies to a GSM8K word problem is a runtime property of that verifier. It does not define a direct-arithmetic population.

The implemented population restrictions that are already in the configuration are: GSM8K and HotpotQA only, 300/200 History/Development groups per benchmark, exact normalized question grouping with source IDs preserved, unresolved candidates retained but excluded from binary examples, and Final Test disabled.

## Direct arithmetic population

Direct arithmetic is excluded as a separate experimental population for `research_v1`.

`evaluation/config/research_dataset.yaml` has no direct-arithmetic target. `manifest.json` and `validation_summary.json` have no direct-arithmetic marker, annotation, or count. GSM8K preparation replays worked solutions and applies a narrow gold+1 discrete-count rule for some incorrect candidates. That rule checks candidate labels. It does not classify questions as direct arithmetic. No validated subset was found, so none is claimed.

GSM8K remains one word-problem population: 500 question groups, 300 History and 200 Development. Rule Verifier applicability is separate. Success or failure of the Rule Verifier must not be used to infer which questions are direct arithmetic. Development or Final Test performance must not be used to define the population.

A future direct-arithmetic evaluation, if wanted, is a new Development-time annotation task. It requires a written inclusion and exclusion rubric, annotation completed before any evaluation, measured reviewer agreement, and results reported as a separate population. The definition must not be chosen from Final Test items or from evaluation scores. Until that annotation exists and is validated, direct arithmetic stays outside the `research_v1` experimental populations.

## Evidence corpus and index identity

`research_v1` does not bind an Evidence Verifier corpus or index. Any experiment that runs the Evidence Verifier must record, before comparing methods, the resolved corpus path, corpus SHA-256, index identity, chunking settings, embedding model, and retriever configuration actually used. Two local corpora are already documented as distinct resources in `evaluation/docs/dataset_and_candidate_readiness.md`; a run must say which one, if either, was loaded:

| Documented local resource | Path and index | Recorded identity |
|---|---|---|
| Baseline configured corpus | `data/articles_13083.json`; `data/evidence_index/articles_13083/` | 13,083 articles; SHA-256 `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8`; index `idx-6d28c9c49dac`; chunk size 500; `all-MiniLM-L6-v2` |
| Retriever code default | `data/evidence_corpus.json`; `data/evidence_index/evidence_corpus/` | 500 articles; SHA-256 `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5`; index `idx-9c87422f0357`; chunk size 500; `all-MiniLM-L6-v2` |

The code default can differ from the process environment. Title overlap with either corpus is not a retrieval result. HotpotQA reference context in this dataset is not a substitute for that record.

## Dataset Selection Decisions and Remaining Actions

| Item | Status | Decision or remaining action |
|---|---|---|
| GSM8K and HotpotQA question groups | Completed | 500 groups each; 1,000 groups total; History 600; Development 400. |
| Question group versus candidate record | Completed | 1,000 groups and 2,050 candidate records. Counts are not interchangeable. |
| FEVER in research_v1 | Completed | Excluded from this version only. Exclusion is not a claim that the framework cannot handle FEVER. |
| MultiNLI in the answer-validation interface | Completed | Not forced into this interface. |
| HotpotQA evidence condition | Completed | Source/reference context supplied with the question. Not a shared-corpus retrieval evaluation. |
| GSM8K incorrect-candidate rule | Completed as a limitation | Only the narrow gold+1 discrete-count rule can mark a candidate `verified_incorrect`. |
| HotpotQA verified incorrect candidates | Completed as a limitation | Zero in research_v1. |
| Unresolved candidates | Completed as a limitation | 871 unresolved records stay unresolved and are excluded from binary examples. |
| Final Test | Completed for this version | Disabled. No final-test identities were accessed. A protected holdout is still required before confirmatory evaluation. |
| Source version strings | Completed | Manifest `source_versions` as listed above. |
| License and citation text | Pending | Local `dataset_info.json` fields are empty. Confirm from the benchmark releases. |
| Direct arithmetic as its own population | Completed | Excluded for research_v1. No verified subset or marker exists. GSM8K stays a word-problem population. |
| Verifier eligibility | Pending approval | Not specified by the research_v1 configuration. Rule Verifier applicability is not a population definition. |
| Scientific acceptance of automated labels | Pending approval | No human adjudication is claimed. |
| Evidence Verifier corpus and index for a run | Pending approval | Identity must be pinned to the resource actually loaded. research_v1 does not choose one. |
| Verifier attempts and policy fitting | Unresolved | Zero complete attempts and zero complete offline examples. `policy_fitting_ready` is false. |
