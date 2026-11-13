# Dataset and candidate-answer readiness audit

## Executive summary

The current unified files contain 12,000 questions across History (8,000), Development (2,000), and Final Test (2,000), evenly divided among FEVER, GSM8K, HotpotQA, and MultiNLI. The separate processed files contain FEVER and HotpotQA only (6,000 rows total) and no candidate-answer pairs.

GSM8K and HotpotQA each have 3,000 questions and 6,000 stored candidates. The 3,000 benchmark-answer candidates per benchmark match their linked local source answer under the audit comparison rule. The other 3,000 per benchmark are generated negatives whose `expected_correct: false` is a generation annotation, not adjudicated ground truth. The current full adjudication overlay records those 6,000 as unresolved; it records no verified incorrect candidate. FEVER has claim labels, not answer candidates. MultiNLI has NLI labels and is not a QA candidate-answer dataset.

The configured baseline evidence resource is documented as `data/articles_13083.json` with index `data/evidence_index/articles_13083/`. Title presence and retrieval are not the same as sufficient evidence: prior corpus checks found no FEVER cited titles and very sparse HotpotQA supporting-page overlap. The existing Final Test partition has been inspected during candidate auditing and was included in the earlier pilot v1 review preparation; it must be treated as exposed, not as a protected unseen holdout.

**Readiness:** benchmark-gold provenance and the existing partition files are usable for continued development work with transparent limitations. The generated incorrect candidates need independent adjudication before binary correctness metrics are credible. Evidence-conditioned factual evaluation needs a defined, validated evidence source. The current Final Test cannot support a protected holdout claim.

## Scope and evidence labels

This is a read-only audit of the files in the current checkout. The read-only inventory script is `evaluation/data_preparation/audit_datasets.py`; candidate source-linkage checks are in `evaluation/data_preparation/audit_candidate_answers.py`. Candidate construction is in `evaluation/prepare_all_benchmarks.py`. Existing counts below are reported from the local audit script output and the adjudication overlay at `evaluation/datasets/adjudication/v1/`.

- **Verified repository fact** means visible in a local file, code path, or reproducible local count.
- **Prior documented audit** means recorded in an existing report and not freshly measured in this pass; it is identified as such.
- **Unknown** means the available files do not establish the claim.
- No dataset, result, label, script, or existing documentation was changed by the audit.

## Dataset inventory

### Raw benchmark sources

| Dataset / source | Local source and version | Local rows | Main fields / task | Gold format and context |
|---|---|---:|---|---|
| FEVER 1.0 | `evaluation/datasets/raw/fever/`; source config is locally saved as FEVER; source revision not encoded in the local top-level manifest | train 311,431; labelled_dev 37,566; unlabelled_dev 19,998; unlabelled_test 19,998; paper_dev 18,999; paper_test 18,567 | `id`, `label`, `claim`, evidence annotation/id, Wikipedia URL and sentence ID; claim verification | `SUPPORTS`, `REFUTES`, `NOT ENOUGH INFO`; evidence is referenced by identifiers/title, not embedded as full evidence text in unified records |
| GSM8K main | `evaluation/datasets/raw/gsm8k/`; `openai/gsm8k@740312add88f781978c0658806c59bc2815b9866` | train 7,473; test 1,319 | `question`, `answer` (worked solution with final-answer marker) | Canonical answer extracted from `#### ...`; worked derivation available in raw source |
| HotpotQA distractor | `evaluation/datasets/raw/hotpotqa/`; `hotpotqa/hotpot_qa@1908d6afbbead072334abe2965f91bd2709910ab` | train 90,447; validation 7,405 | `id`, `question`, `answer`, type, level, supporting facts, context | Short answer, with supplied context paragraphs and supporting-fact title/sentence references |
| MultiNLI via GLUE | `evaluation/datasets/raw/multinli/`; `nyu-mll/glue@bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c` | train 392,702; validation_matched 9,815; validation_mismatched 9,832; test_matched 9,796; test_mismatched 9,847 | `premise`, `hypothesis`, label, `idx` | Entailment / neutral / contradiction; premise is the reference text, but the task is NLI rather than answer validation |

FEVER's exact upstream version is not recoverable from the local files inspected here, so version pinning should be added to provenance before regeneration. The local raw data are saved Arrow datasets; their partition counts are the actual rows in those local files, not a claim that source splits are independent of every other benchmark release.

### Existing processed files

| File | Rows | Contents and fields relevant here |
|---|---:|---|
| `evaluation/datasets/processed/history.json` | 4,000 | 2,000 FEVER + 2,000 HotpotQA; `group_id` present; zero candidate answers |
| `evaluation/datasets/processed/development.json` | 1,000 | 500 FEVER + 500 HotpotQA; `group_id` present; zero candidate answers |
| `evaluation/datasets/processed/final_test.json` | 1,000 | 500 FEVER + 500 HotpotQA; `group_id` present; zero candidate answers |

The processed file audit reports no label-provenance field and no evidence-resource identity field in these rows. Its group IDs cannot be assumed to match the unified partition grouping without checking the actual ID scheme.

### Existing unified files

| File | Rows | FEVER | GSM8K | HotpotQA | MultiNLI | Questions with candidates |
|---|---:|---:|---:|---:|---:|---:|
| `evaluation/datasets/unified/history.json` | 8,000 | 2,000 | 2,000 | 2,000 | 2,000 | 4,000 |
| `evaluation/datasets/unified/development.json` | 2,000 | 500 | 500 | 500 | 500 | 1,000 |
| `evaluation/datasets/unified/final_test.json` | 2,000 | 500 | 500 | 500 | 500 | 1,000 |

Each unified record has a stable-looking `id` and `benchmark`, but no `group_id`, label provenance, or evidence-resource ID. GSM8K rows store question, solution, `gold_answer`, and two candidate objects. HotpotQA rows store question, gold answer, context, supporting facts, and two candidate objects. FEVER rows store claim, FEVER label, and evidence identifiers/URLs, but no `candidate_answers`. MultiNLI rows store premise, hypothesis, and NLI label fields, but no `candidate_answers`.

The current exact hashes from the adjudication manifest are:

| File | SHA-256 |
|---|---|
| `history.json` | `4e32f5490a2ebaaaacba9d5e7dcc80352e3cfa20da6bf1ceb2572fa7b3aeb6ee` |
| `development.json` | `6e59b1fd5a813a39e70f25cdfc4402727b6ca60431eba87e2bd7ba3f6da98ce4` |
| `final_test.json` | `80fc2bcf2736b30bed68257d2ef167a14a01bf370fca552de19dcf9be4489966` |

## Candidate-answer label audit

The exact totals are from `audit_candidate_answers.py` and `evaluation/datasets/adjudication/v1/statistics.json`. A status of `verified_correct` for a benchmark-gold candidate means the candidate matches the linked benchmark's canonical answer under that audit's comparison rule. It does not mean the question was independently solved by a reviewer.

| Benchmark | Questions | Candidate answers | Source-linked gold candidates | Synthetic / borrowed candidates | Independently adjudicated incorrect | Unresolved correctness |
|---|---:|---:|---:|---:|---:|---:|
| GSM8K | 3,000 | 6,000 | 3,000 | 3,000 numeric perturbations | 0 | 3,000 |
| HotpotQA | 3,000 | 6,000 | 3,000 | 3,000 borrowed answers | 0 | 3,000 |
| FEVER | 3,000 claims | 0 | n/a (claim labels) | n/a | n/a | n/a |
| MultiNLI | 3,000 premise/hypothesis pairs | 0 | n/a (NLI labels) | n/a | n/a | n/a |

Across GSM8K and HotpotQA, the full overlay has 12,000 candidate records: 6,000 `verified_correct` benchmark-gold matches and 6,000 unresolved generated candidates; zero `verified_incorrect`. It contains 3,000 records per benchmark per partition for candidate rows, split as follows: History 2,000 gold + 2,000 unresolved per benchmark; Development 500 + 500; Final Test 500 + 500. No human decisions are evidenced in the overlay.

### GSM8K

`evaluation/prepare_all_benchmarks.py` extracts the number after `####` from each official solution and generates a synthetic candidate by adding one. The candidate source is marked `synthetic_numeric_perturbation`; all 3,000 pairs match that construction rule and have numeric candidates. Commas are stripped and the audit uses decimal parsing for comparisons. The raw source has 8,792 examples: 93 comma-grouped final answers, 5 negative answers, no decimal or leading-zero answers, and no multiple `####` markers (as recorded by the candidate audit).

Adding one is not a correctness proof. Units, tolerances, rounding, alternate interpretations, and semantically equivalent formatting can matter. The correct candidate's source linkage is verified; all 3,000 generated candidates remain unresolved. Do not count any as wrong until independent arithmetic review or an auditable, independently validated procedure supports that judgment. `evaluation/datasets/adjudication/v1/` has source-match records and unresolved review queues; it does not supply independent solutions for the negatives.

### HotpotQA

`add_hotpot_negative_candidates()` in `evaluation/prepare_all_benchmarks.py` borrows a later answer in a prepared list whose alphanumeric-normalized form differs from the target gold answer. The donor ID is not retained. The 3,000 gold candidates match their target source rows, while all 3,000 borrowed candidates remain unresolved. All borrowed candidates are answers to some source question, which says nothing about their truth for the target question. The builder's normalization does not resolve aliases or semantic equivalence, answer scope, or accidental correctness.

The prior candidate audit found 203/3,000 borrowed strings appearing as a case-insensitive literal substring in target context. This is only a review-priority signal, not proof of correctness. Independent factual review must compare the candidate to the target question and supporting context; if the provided context is insufficient, retain `unresolved`. The framework being evaluated is not an acceptable sole judge.

### FEVER and MultiNLI

FEVER labels must remain three-way. `SUPPORTS` and `REFUTES` can support claim-verification decisions when evidence is available; `NOT ENOUGH INFO` means the benchmark does not supply enough evidence for either conclusion. It must not be converted into a false answer. FEVER records do not currently express the claim as a question with answer candidates, so this is an adjacent claim-verification population requiring an explicitly compatible adapter/protocol.

MultiNLI labels represent the relationship of a hypothesis to a premise, not correctness of a candidate answer to a user question. Mapping hypothesis to candidate and premise to reference would change the task and can reduce entailment to semantic similarity. It is not suitable for the present QA validation interface without a separately justified NLI research question and protocol.

## Evidence corpus compatibility

`app/verifiers/evidence_retriever.py` defines `DEFAULT_CORPUS_PATH = "data/evidence_corpus.json"` and `default_corpus_path()` reads `EVIDENCE_CORPUS_PATH` from environment or `.env`. Existing baseline documentation (`evaluation/docs/baseline_evaluation.md`) says the baseline run used `data/articles_13083.json`. The current indexed corpus manifests are:

| Corpus | File / index | Identity |
|---|---|---|
| Baseline configured corpus | `data/articles_13083.json`; `data/evidence_index/articles_13083/` | 13,083 articles; SHA-256 `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8`; index `idx-6d28c9c49dac`; chunk size 500; `all-MiniLM-L6-v2` |
| Retriever default corpus | `data/evidence_corpus.json`; `data/evidence_index/evidence_corpus/` | 500 articles; SHA-256 `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5`; index `idx-9c87422f0357`; chunk size 500; `all-MiniLM-L6-v2` |

These are distinct resources. The baseline docs establish its configured path, while the verifier's code default is the 500-article corpus. The effective path can vary with the process environment; each experiment must record the resolved path, corpus hash, and index version. The present audit did not inspect a live process's environment, so it cannot assert which path a future run will use.

| Dataset | Supplied evidence / source references | Corpus presence and retrieval | Evidence Verifier suitability |
|---|---|---|---|
| FEVER | Unified rows include evidence URLs/titles and sentence IDs, not sentence text. | Prior title check against the baseline 13,083-article corpus found 0/301 distinct FEVER titles present. This is a title-presence check, not a retrieval test. | Not suitable as evidence-supported benchmark evaluation with this corpus unless the source evidence is made available through an approved corpus. NEI remains a separate label. |
| GSM8K | Worked solution and canonical answer are in the benchmark record; no external evidence corpus identity is recorded. | Arithmetic derivation is available as reference material, but no evidence corpus match/retrieval finding establishes Evidence Verifier coverage. | Arithmetic may suit the Rule Verifier; evidence-verifier applicability is not established. If solution text is given to a verifier, call it reference-assisted and give all comparison methods the same permitted information. |
| HotpotQA | Unified rows include supplied distractor paragraphs and supporting-fact references. | Prior audit of 3,000 sampled records reported target context-title matches of 28/2,000 History, 7/500 Development, and 11/500 Final Test against the baseline corpus; all required supporting titles were not present as complete per-question support sets. This is title overlap, not retrieval success or evidence sufficiency. | Suitable for a reference-assisted condition using the per-question benchmark context if all methods receive the same context. Shared-corpus condition is weak and requires per-example retrieval/sufficiency measurement. |
| MultiNLI | Premise is source text for the NLI task. | Not audited as evidence retrieval. | Evidence retrieval is not the right QA evaluation criterion for the current task. |

Existing `evaluation/results/evidence_hotpotqa_results.json` is a tiny run whose baseline report describes use of each example's supplied HotpotQA context; it is not evidence that the shared configured index retrieves benchmark support. Report separately: corpus presence, retrieval success, and whether retrieved evidence is sufficient to establish the answer.

## Partition and leakage audit

`audit_datasets.py` reports no duplicate IDs within any unified partition. The prior exact partition audit in `evaluation/docs/existing_split_research_readiness.md` reports zero pairwise ID overlap and zero exact normalized question/claim overlap across History, Development, and Final Test for each benchmark. All candidate variants for a question are stored together in one row, so candidate pairs are not divided from their question across partitions. The unified rows contain no `group_id`; related-question, paraphrase, entity, or source-document cluster leakage has therefore not been ruled out. The processed FEVER/HotpotQA files do have group IDs, but their relationship to unified IDs/partitions is not demonstrated here.

The final-test partition is **exposed**. Existing candidate audit reports inspect its gold and generated candidate records. The existing full adjudication overlay includes final-test candidate IDs and answers. `evaluation/docs/candidate_adjudication_pilot.md` documents that pilot v1 selected 10 GSM8K and 5 HotpotQA Final Test cases and supplied reference answer/context. The currently present pilot directory listing did not include `pilot_v2_seed_20261101`; do not assume the earlier documented replacement pilot is available in this checkout. Exposure of Final Test through the audit and v1 pilot is already sufficient to rule out a protected unseen-holdout claim, regardless of v2.

Result files present include `evaluation/results/baseline/baseline_results.jsonl` (1,232 completed unique instances: 496 HotpotQA, 490 GSM8K, 246 FEVER), its smoke JSONL (8 instances), `evaluation/results/rule_gsm8k_results.json`, and `evaluation/results/evidence_hotpotqa_results.json`. These are prior experiment outcomes, not labels for new candidates. The latest inventory did not establish a result-to-final-test ID comparison for every JSON/CSV result, so do not infer that all result records are disjoint from Final Test without a direct ID-level audit.

## Recommended dataset scope

| Recommendation | Benefit | Limitation / condition |
|---|---|---|
| **GSM8K as the arithmetic population**, initially using gold candidates and only independently adjudicated alternatives | Clear arithmetic questions, worked derivations, canonical answers, stable raw source linkage; potentially compatible with rule-based and confidence verification | The current `gold + 1` negatives are all unresolved. Derivations can leak reference answers if not handled consistently. The project should adjudicate or generate candidates under a separately approved protocol before binary loss is calculated. |
| **HotpotQA as a factual multi-hop population**, using target context as a declared reference-assisted condition | Multi-hop QA, gold answer, supporting facts, and context are supplied; it directly exercises semantic/evidence verification | All borrowed candidates are unresolved and donor provenance is absent. Shared corpus support is sparse; per-example context evaluation is not the same as shared-corpus retrieval. Adjudicate answers and make context access identical across methods. |
| **FEVER as a separate claim-verification extension**, only if the team explicitly adapts the task and obtains evidence | Strong three-way claim labels with evidence references; useful for evidence-verifier behavior | It is not the current candidate-answer QA format, and the baseline corpus lacks cited titles per the documented check. Preserve `NOT ENOUGH INFO` as its own state. |
| **Exclude MultiNLI from current QA validation comparison** | Avoids conflating NLI with answer correctness | A separate, justified NLI protocol would be needed to use it. |

Do not use source-gold equality alone to mark alternatives wrong, and do not count the construction field `expected_correct` as an independently verified label. Correct benchmark gold candidates have canonical source provenance, but independent human or solver verification is not recorded. Generated GSM8K/HotpotQA alternatives must remain unresolved until adjudicated with evidence. Cases with insufficient/ambiguous context should remain unresolved or be excluded from binary correctness scoring by a predeclared rule.

## Unresolved issues, risks, and concrete next steps

1. **Candidate labels:** adjudicate 3,000 GSM8K and 3,000 HotpotQA alternatives independently. Use arithmetic derivation for GSM8K; target question plus cited support for HotpotQA. Preserve reviewer evidence, provenance, rationale, and disagreement. Do not use framework outputs as the judge.
2. **Donor provenance:** HotpotQA generation did not retain the borrowed-answer donor ID. Recover it only if the exact builder input ordering and source list can be reproduced; otherwise record donor as unknown rather than infer it.
3. **FEVER version/evidence:** pin exact source release and make evidence resource/version explicit. Assess per-row evidence availability and sufficiency, not just title match. Keep NEI distinct.
4. **Evidence configuration:** record effective `EVIDENCE_CORPUS_PATH`, corpus SHA-256, index version, retrieval query, returned passage IDs/scores, and sufficiency adjudication for every run. Test whether retrieval actually finds support; corpus/title presence alone is not enough.
5. **Grouping:** assign or verify related-example groups using source relationships and paraphrase/duplicate analysis before making leakage claims. Current unified files have no group IDs.
6. **Final Test:** preserve the existing file unchanged if desired, but classify it as previously exposed. For a confirmatory claim, establish a new custodian-controlled holdout from unexposed identities after group-level leakage review; freeze policy and comparison rules before access. Do not retroactively call the existing partition unseen.
7. **Results:** before comparing prior experiments to the final research protocol, audit each record's dataset ID, partition, candidate construction, corpus identity, verifier/policy configuration, completion/failure status, and timing. The 1,232-record baseline file is not automatically a research-ready comparison.

### Readiness conclusion

- **Ready with conditions:** raw benchmark source linkage; current History/Development memberships as existing artifacts; GSM8K and HotpotQA benchmark-gold candidate provenance; HotpotQA's supplied per-question context for a declared reference-assisted protocol.
- **Needs adjudication:** all 3,000 GSM8K synthetic and 3,000 HotpotQA borrowed candidates. None is independently verified incorrect in the available overlay.
- **Needs protocol/configuration work:** evidence corpus identity and retrieval sufficiency; FEVER task compatibility and source version; related-example grouping; full result metadata audit.
- **Not ready as a protected final evaluation:** existing Final Test is exposed through candidate auditing, full candidate adjudication records, and pilot v1 review preparation. Keep it frozen if useful for exploratory/fixed evaluation, label its status honestly, and prepare a separate protected holdout for confirmatory evaluation.
