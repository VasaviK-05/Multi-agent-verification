# Comprehensive research-readiness audit

Read-only audit of the working tree. No empirical experiment was run. No Development recordings were collected. Sealed Final Test labels and candidate texts were not opened, printed, or scored. This document is an audit, not an approval.

Inspection date: 2026-11-13. HEAD at inspection: `30c425e`.

## A. Executive summary

**Overall readiness: not research-ready.** The repository can support continued review. It cannot support authorized Development collection, empirical Experiment 3, or Final Test scoring.

| Bucket | Count | Requirements |
|---|---:|---|
| Fully satisfied | 0 | — |
| Partially satisfied | 5 | 1 task populations, 3 datasets, 4 evidence corpus, 5 Final Test custody, 6 protocol |
| Missing or blocked | 2 | 2 verifier/resource freeze, 7 collection and scoring authorization |

Experiment 3 is **ready for approval only**. `assess()` returns `READY_FOR_APPROVAL` with an empty blocker list. It is not ready for collection authorization, Development collection, or an empirical run. The four Experiment 3 approval records are `NOT_AN_APPROVAL`. Collection authorization is `NOT_AUTHORIZED`.

Most critical blockers:

1. No signed protocol, corpus, dependency, or collection authorization. Eligibility approval does not authorize collection.
2. Verifier snapshots, prompts, hardware, seed, timeout, retries, and the cost unit are `UNKNOWN`. The process `.env` points `EVIDENCE_CORPUS_PATH` at a directory, which `EvidenceRetriever` rejects because it requires a JSON file.
3. The declared dependency model puts all four verifiers in one failure group. No measured dependence exists.
4. Final Test v2 remains `NOT_AUTHORIZED`, with designated non-independent custody and no operating-system label boundary.
5. No `evaluation/datasets/verifier_attempts/research_v1/` directory exists. Protocol readiness still records zero complete Attempts and zero Offline Examples. Person 3 observations are zero.

## B. Seven-requirement readiness matrix

| Priority | Requirement | Status | What the repository actually supports | What blocks full satisfaction |
|---|---|---|---|---|
| 1 | Supported task populations | Partially satisfied | Four verifiers exist, with narrow demonstrated scopes. Direct arithmetic is a Rule pattern. GSM8K and HotpotQA are the exploratory research populations. | No verifier is verified, by recordings, on the approved 372-group roster. FEVER and MultiNLI are not that roster. |
| 2 | Verifier / resource compatibility | Blocked | Code defaults and historical study packages name models. Experiment 3 collection names the same four classes and leaves hashes unknown. | Configuration is not frozen, not reproducible as a research snapshot, and not the configuration of a research recording. |
| 3 | Approved research datasets | Partially satisfied | Unified 8,000 / 2,000 / 2,000 counts still match. Exploratory Development eligibility is approved: 744 candidates, 372 groups. | Benchmark-population approval is false. Synthetic incorrect labels are not human-verified. Collection is not authorized. |
| 4 | Development evidence corpus | Partially satisfied | `development_evidence_corpus_v1` matches SHA-256 `f76c6ce1…`, 1,844 articles, index bound to that hash. Coverage was measured. | Status `PROPOSAL_NOT_APPROVED`. Not frozen. Most HotpotQA questions miss the 0.78 retrieval gate. FEVER is not covered. |
| 5 | Final Test custody | Partially satisfied | v2 manifest `e572093a…` is `NOT_AUTHORIZED`, enabled false, 600 groups, 1,200 candidates. Exposure and leakage audits record `passed: true`. | Custody is the dataset creator, `NOT_INDEPENDENT`. `operating_system_protection` is false. Release and scoring are not authorized. |
| 6 | Scientific protocol approval | Partially satisfied | Experiments 1–4 have written proposals. Experiment 3 has a specification, analysis contract, and validator. | Every scientific `approved` flag in `protocol_readiness.yaml` is false. No protocol is frozen or executed empirically. |
| 7 | Collection and scoring authorization | Blocked | Authorization templates and roster pointers exist. | No signed collection or scoring record. History and Development collection are unauthorized. Final Test release is a separate, also unauthorized, gate. |

## 1. Supported task populations

Statuses mean: **VERIFIED** — the verifier implements the task and a test or recording shows a meaningful decision on that population; **PARTIALLY VERIFIED** — a real code path or a narrow recorded run exists, and it does not establish the research population; **UNSUPPORTED** — the implementation abstains or the task is outside the verifier; **UNKNOWN** — the files do not show whether a meaningful configuration was used.

Executing without crashing is not VERIFIED.

| Verifier | Direct arithmetic | GSM8K | Direct facts | HotpotQA | FEVER | Evidence-grounded check |
|---|---|---|---|---|---|---|
| Semantic | UNSUPPORTED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNKNOWN | PARTIALLY VERIFIED |
| Evidence | UNSUPPORTED | UNSUPPORTED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNSUPPORTED | PARTIALLY VERIFIED |
| Rule | VERIFIED | UNSUPPORTED | PARTIALLY VERIFIED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED |
| Confidence | PARTIALLY VERIFIED | PARTIALLY VERIFIED | PARTIALLY VERIFIED | UNKNOWN | UNKNOWN | UNSUPPORTED |

### How each cell was judged

**Rule.** `app/verifiers/rule_verifier.py` computes answers only for listed patterns: `What is 25 + 17?`, sum/difference/product wording, comparisons, one adult-status sentence, and format or range checks. Structural passes are validity, not correctness. A GSM8K word problem matches none of those patterns and is `unsupported`, which the decision layer reads as abstention. `evaluation/docs/baseline_evaluation.md` records that abstention on the word-problem run. The older `evaluation/results/rule_gsm8k_results.json` (1,000 rows, 500 questions) is a single-verifier script result on unified Development, not a research_v1 recording and not evidence that word problems are solved. Direct factual questions outside the adult-status and format rules are unsupported. HotpotQA multi-hop questions and FEVER claims are unsupported. The Rule verifier does not retrieve evidence.

**Semantic.** `SemanticVerifier` embeds `all-MiniLM-L6-v2` and compares an answer with reference text. It abstains when reference text is missing. The module states that cosine similarity is resemblance, not factual correctness. Thresholds 0.5 and 0.3 are uncalibrated. A HaluEval note in the module (800 pairs, knowledge passage as reference) shows weak separation and is not a GSM8K or HotpotQA result. Semantic verification of GSM8K or HotpotQA is partial only when the same reference is supplied to every method. It is not a verified correctness verifier for those benchmarks. FEVER has no recorded semantic-reference protocol in the research configuration. An evidence-grounded semantic check exists only as similarity to supplied text.

**Evidence.** The pipeline is retrieval, relevance and topic gates, then `cross-encoder/nli-deberta-v3-small`. Defaults `min_retrieval_score` 0.45 and `min_nli_score` 0.50 are described in code as uncalibrated. GSM8K is explicitly `not_applicable_arithmetic` in the Development corpus preparation: worked solutions were not added, and none of the 187 eligible GSM8K questions retrieved a chunk at cosine ≥ 0.78. Direct facts are partial: frozen Compound study packages bind Evidence to a small allowlist of area and population prompts, not to an open factual population. HotpotQA is partial: the new corpus contains every supporting title for 185 eligible questions, retrieval returns a supporting title for 184, and only 19 also clear cosine 0.78. One question remains a retrieval miss. That is coverage of supplied paragraphs, not a recorded Evidence Verifier decision on the roster. FEVER is unsupported on the corpora that were measured: `articles_13083.json` contained 0 of 185 eligible HotpotQA supporting-title sets in full and, in the earlier unified audit, 0 of 301 distinct FEVER titles. The new corpus is HotpotQA reference paragraphs only. No FEVER sentence text was added.

**Confidence.** `ConfidenceVerifier` counts `support` / `reject` / `unsure` judgments. The default provider is `SelfConsistencyJudge`: five Ollama samples, temperature 0.8, 60-second timeout, model default `llama3.2:3b` at `http://localhost:11434/api/generate`. Numeric answers use exact `Decimal` comparison, so direct arithmetic and GSM8K have a defined labeling rule in code. Agreement is not accuracy. The research collection record sets the generator model, weight hash, and prompt hash to `UNKNOWN`, so the research configuration is not the code default. No research Attempt shows that this provider ran on GSM8K, HotpotQA, or FEVER. Confidence does not check a corpus. Prose evidence in `context` is ignored unless the string is a judgment list.

Question-difficulty analysis and adaptive selection exist in the orchestrator. They do not create a verified task population. A verifier that works on a direct sum is not thereby capable of GSM8K. A verifier that retrieves a HotpotQA paragraph is not thereby capable of FEVER.

## 2. Verifier / resource compatibility

| Item | Declared for Experiment 3 collection | Actually in the implementation | Frozen for this research protocol | Used by a research recording | Tests or recordings |
|---|---|---|---|---|---|
| Semantic | `SemanticVerifier`, `all-MiniLM-L6-v2`, weight hash `UNKNOWN` | Same class and model name. Weights are downloaded by `SentenceTransformer` unless a snapshot is injected. | No | No | Unit tests and historical Reference replays. Not the 372-group roster. |
| Evidence | `EvidenceVerifier`, NLI `cross-encoder/nli-deberta-v3-small`, weight hash `UNKNOWN` | Same names. Defaults: retrieval floor 0.45, NLI floor 0.50, chunk 500 words, embedding `all-MiniLM-L6-v2`. | No | No | Implementation tests and a 10-row HotpotQA result on supplied context. Not an approved Attempt. |
| Evidence corpus | `development_evidence_corpus_v1`, file SHA-256 `f76c6ce1…`, index `idx-c1dc6980912b` | Code default file is `data/evidence_corpus.json` (`668b48aa…`, index `idx-9c87422f0357`). `.env` sets `EVIDENCE_CORPUS_PATH` to the corpus **directory**. That path is not a file, so a default `EvidenceRetriever()` raises `FileNotFoundError`. | Corpus file is not approved | No | Index loads when the JSON file is passed explicitly. |
| Rule | `RuleVerifier`, `rule_version_hash` `UNKNOWN` | Deterministic patterns above. No model. | No | No | Pattern tests. GSM8K word problems abstain. |
| Confidence | generator `UNKNOWN`, hashes `UNKNOWN` | Default Ollama `llama3.2:3b`, 5 samples, temperature 0.8, timeout 60 s. A historical Reference package records Ollama 0.40.14 and digest `sha256:a80c4f17…`. `evaluation/docs/runtime_configuration.md` says 0.40.11 is incompatible. | That digest belongs to the old Reference package, not Experiment 3 | No research_v1 Attempt | Historical Reference replays. Current host compatibility is not established. |
| Dependency groups | `provisional_shared_unknown_v1` | One group: semantic, evidence, rule, confidence | Provisional, `approved: false`, `empirical_evidence: none` | Not measured | Synthetic two-group fixture is labelled not empirical. |
| Timeout, retries, warmup, seed, hardware | null / `UNKNOWN` / `PENDING_APPROVAL` | Confidence timeout default 60 s. Other verifiers have no research-wide timeout in the collection file. | No | No | Not a research recording. |

External dependencies visible in code: SentenceTransformers (`all-MiniLM-L6-v2`), a Hugging Face NLI cross-encoder, FAISS, and a loopback Ollama generate API. No cloud API key is part of the declared research configuration. The collection adapter schema can name loopback Ollama, and `evaluation/docs/verifier_attempt_recording_protocol.md` says `VERIFIER_COLLECTION_ADAPTER_CONFIG` is unset and the factory refuses network downloads. This audit did not find a filled adapter for the exploratory roster.

The dependency configuration is the failure-group error the protocol warned about. `shared_unknown` cannot separate an independent failure from a correlated failure. The validator blocks any attempt to mark the synthetic two-group registry as empirical.

`evaluation/docs/runtime_configuration.md` describes a different checkout: branch `tanmayee-main-integration-review`, HEAD `9b8959d6`. That document is a historical runtime note. It is not the configuration of HEAD `30c425e`.

## 3. Approved research datasets

### Counts that still match

Recomputed from the unified JSON files, counting the `benchmark` field only:

| File | Rows | FEVER | GSM8K | HotpotQA | MultiNLI |
|---|---:|---:|---:|---:|---:|
| `evaluation/datasets/unified/history.json` | 8,000 | 2,000 | 2,000 | 2,000 | 2,000 |
| `evaluation/datasets/unified/development.json` | 2,000 | 500 | 500 | 500 | 500 |
| `evaluation/datasets/unified/final_test.json` | 2,000 | 500 | 500 | 500 | 500 |

`evaluation/docs/dataset_and_candidate_readiness.md` still describes 12,000 candidate rows for GSM8K and HotpotQA together: 3,000 source-linked gold matches and 3,000 unresolved synthetic or borrowed candidates per benchmark, and zero independently adjudicated incorrect labels in adjudication v1. FEVER remains a three-way claim label. MultiNLI remains NLI, not a candidate-answer task. This audit did not reopen those candidate strings. The documented figures are unchanged in the audit documents, and the partition sizes above still match.

Verified subset `v1_seed_20261104`, as recorded in `evaluation/docs/dataset_split_and_final_test_protocol.md`: 100 questions and 200 candidates per benchmark, 80 History and 20 Development. GSM8K 91 verified correct, 0 verified incorrect, 109 unresolved. HotpotQA 100 / 0 / 100. Combined: **191 correct, 0 incorrect, 209 unresolved**. That subset is not the current research roster.

research_v1 files still present, line counts unchanged from `evaluation/docs/research_v1_inventory_and_provenance.md`: History candidates 1,240, Development candidates 810, History prepared 701, Development prepared 478. License fields were recorded as empty. That roster is `research_v1_person1_v1`. It is not the exploratory eligibility roster.

### What is actually approved

`evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json`:

- Status `APPROVED_BY_RESEARCH_LEAD`, approver role Research Lead, date 2026-11-13.
- Scope: Development eligibility for `research_v1_exploratory_v1` only.
- 744 candidates, 372 groups: GSM8K 187 `VERIFIED_CORRECT` and 187 `SYNTHETIC_INCORRECT`; HotpotQA 185 and 185.
- 15 groups quarantined for shared context. Exact identifier overlap with History is 0. Semantic clearance is `NOT_CLAIMED`.
- Body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`.
- `collection_authorized`, `recording_authorized`, `final_test_authorized`, and `frozen_protocol` are false.
- Label protocol `provisional_automated_labeling_v1`. Human-verified incorrect count is not claimed. `HUMAN_VERIFIED_INCORRECT` is not the synthetic class.

`evaluation/config/protocol_readiness.yaml` still has `approved_benchmarks.approved: false`, `candidate_label_policy.approved: false`, and `label_audit.approved: false`. The observed candidate list is GSM8K and HotpotQA. FEVER and MultiNLI are not approved research populations for this protocol.

`evaluation/docs/experiment1_readiness_report.md` still says exploratory HotpotQA Development is 200 / 200. That is the pre-quarantine snapshot. The approved manifest is 185 / 185. Reports that cite 200 HotpotQA Development groups are stale.

The unified Final Test file is an older exposed partition. It is not Final Test v2 and it is not a protected holdout.

## 4. Development evidence corpus

| Check | Result |
|---|---|
| Identity | `development_evidence_corpus_v1` |
| File | `evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json` |
| SHA-256 recomputed this audit | `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b` (1,345,040 bytes) |
| Index manifest corpus hash | same SHA-256, chunk size 500, embedding name `all-MiniLM-L6-v2` |
| Recorded index id | `idx-c1dc6980912b` |
| Approval | `PROPOSAL_NOT_APPROVED`, approver null, frozen false |
| Approval record | `evaluation/config/experiments/approvals/experiment3_corpus_approval_record.json` is `NOT_AN_APPROVAL`, freeze status `NOT_FROZEN` |

The index exists. Existence is not approval and not suitability.

Coverage, from `evaluation/docs/development_evidence_corpus_preparation.md`, was measured on the approved roster:

- HotpotQA: supporting titles present for 185 / 185; retrieved for 184 / 185; retrieved and cosine ≥ 0.78 for 19 / 185; 165 title hits sit below that gate; 1 miss (`HotpotQA:hotpot_5a84bda45542992a431d1a96`).
- GSM8K: 187 questions marked not applicable. No external evidence was added.
- Gold-answer strings of length at least 4 occur in the question's own paragraphs for 177 / 185. That is source-paragraph overlap, not a copied label field.
- URLs are `DERIVED_FROM_TITLE_NOT_FETCHED`. Publication date and embedding-weight hash are `UNKNOWN`.
- The 13,083-article and 500-article corpora do not cover these supporting-title sets (2 and 0 questions with at least one supporting title). They were not modified.
- No official verifier attempts were recorded. The topic gate was not run on the 165 below-gate hits.

The corpus can support a **reference-paragraph retrieval study** for 185 HotpotQA Development questions, with the gate failure reported. It cannot support a claim that Evidence verification is adequate for HotpotQA, and it does not support FEVER. It is not approved, not frozen, and not what a default retriever loads from the current `.env`.

## 5. Final Test custody

Final Test v2 remains sealed. This audit read manifest metadata, the custodian appointment, and custody documents. It did not open the label file.

| Field | Value read from the v2 manifest or appointment |
|---|---|
| Dataset | `research_v1_final_test_v2_exploratory_v1` |
| Manifest content hash | `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` |
| Status | `NOT_AUTHORIZED`, `enabled: false` |
| Groups / candidates | 600 / 1,200 |
| Evaluation authorization | `PENDING` |
| Label release | `NOT_AUTHORIZED` |
| Confirmatory use | `NOT_AUTHORIZED` |
| Custody | `DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR`, `NOT_INDEPENDENT` |
| OS protection | `false` on the appointment |
| Human approval and adjudication | `DEFERRED` |
| Human-verified labels | 0 |
| Retired partition reused | false |
| Exposure audit | `passed: true`, overlapping groups 0, paragraph-overlap groups 0, 157 files checked |
| Leakage audit | `passed: true`; the audit records that retired Final Test labels were not opened |

Independent custody is documented as absent. The appointment file states that the appointment does not authorize evaluation or label release. `read_custodian_labels` is a code gate. A process with filesystem access can still read the Git-ignored custodian directory. No release authorization record was found.

The retired provisional Final Test (`research_v1_final_test_provisional_v1`) stays disabled. Its custody document records 807 of 2,638 groups as previously exposed and records inherited Windows modify/read permissions. It must not be used as a holdout.

The unified `final_test.json` (2,000 rows) is a separate, already exposed file. Prior audits and an adjudication pilot used Final Test cases from that era. That exposure does not by itself show that v2 labels were used for tuning. The v2 exposure audit records zero overlapping groups. This audit did not re-execute that scan and did not score v2.

No Final Test scoring authorization exists. Experiment protocols prohibit Final Test for development fitting, reputation, and Experiment 3.

## 6. Scientific protocol approval

| Experiment | Document status | Machine-readable status | Implemented | Executed empirically |
|---|---|---|---|---|
| 1 | `PENDING_APPROVAL` | `approved: false`, `collection_authorized: false` | Comparison code and a synthetic/preparation path | No research_v1 Attempts. Exploratory work was declared possible; confirmatory evaluation was not. |
| 2 | `PENDING_PERSON2_COSTS_AND_APPROVAL` | budgets null, `approved: false` | Protocol text | No. Blocked on Person 2 costs. |
| 3 | Specification `PENDING_APPROVAL`; readiness `READY_FOR_APPROVAL` | `approved: false`, `frozen: false`, `collection_authorized: false` | Validator, analysis, SVG figures, synthetic fixture | Synthetic fixture only. Empirical run not started. |
| 4 | `PENDING_PERSON2_AND_PERSON3` | `approved: false` | Protocol text | No. |

`evaluation/config/protocol_readiness.yaml` leaves benchmark, source, label, verifier eligibility, evidence, loss, threshold, budget, attacks, metrics, statistics, sample size, and license approval all false. Attempts and offline examples are 0. Policy fitting is false.

Experiment 3's specification states the two research questions, the three aggregations, pairing on `related_group_id` and attack, the approved eligibility hash, and a missing-data rule. Loss weights, resource coefficient, decision threshold, verifier budget, suppression mode, bootstrap count, confidence level, and seed stay null in the specification. Recommendations live only in `experiment3_settings_proposal.json` as `PROPOSED_PENDING_APPROVAL`. The resource coefficient and the budget have no recommended number.

Attack scenarios in the proposal are clean, forced support, forced rejection, confidence inflation, and suppression unavailable. They are report transformations. They are not approved.

Reputation update policy is `PENDING_PERSON3` with `observations_count` 0. There is no exported policy for this protocol.

The protocol that is implemented is the prerequisite and analysis contract. The protocol that would be executed is not approved and has no empirical rows. `evaluation/docs/research_protocol_readiness.md` still says a mixed-label v2 "is planned but not built." That sentence is false: v2 exists and is unauthorized. `evaluation/docs/experiment1_protocol.md` still says the exploratory audit is provisional and does not authorize the run. Eligibility is now approved; collection is still not authorized. The authorization conclusion holds. The "provisional audit" wording is stale.

## 7. Collection and scoring authorization

| Authorization question | Repository answer |
|---|---|
| Development collection for Experiment 3 | `NOT_AUTHORIZED`. Record `experiment3_collection_authorization_record.json` has approver null and date null. |
| Exact dataset and split | The pending configuration names `research_v1_exploratory_v1`, partition Development, eligibility body hash `f2cc0fd1…`. That pointer is not a signature. |
| Exact question and candidate population | 372 groups and 744 candidates in the eligibility manifest. The collection record does not approve them for recording. |
| Exact verifier configuration | Hashes `UNKNOWN`. Not an exact configuration. |
| History collection | No separate signed History collection manifest. History remains the reputation partition in the protocol text, and Attempts are absent. |
| research_v1 recordings | `evaluation/datasets/verifier_attempts/research_v1/` does not exist. Feasibility pilots are documented as `BLOCKED_PREFLIGHT` with zero verifier calls. |
| Baseline freeze before evaluation | Historical Reference and Compound packages are frozen for their own allowlists. They are not the Experiment 1–4 protocol and are not authorized as this study's baselines. |
| Scoring | No scoring authorization. Final Test `confirmatory_use` is `NOT_AUTHORIZED`. |
| Separation of History/Development collection from Final Test release | The documents and the eligibility manifest list Final Test release as something eligibility does not authorize. Both gates are currently closed. |

Scripts, tests, proposal files, readiness status `READY_FOR_APPROVAL`, and the approved eligibility manifest do not authorize collection or scoring.

## C. Cross-requirement consistency

| Check | Finding |
|---|---|
| Dataset populations vs verifier capability | The approved roster is GSM8K word problems and HotpotQA. Rule does not solve GSM8K word problems. Evidence is not applicable to GSM8K and is below its own gate for most HotpotQA questions. Semantic and Confidence have no research recording on these 372 groups. FEVER and MultiNLI remain in the unified files and are outside the approved roster. |
| Verifier configuration vs protocol | The protocol names four verifiers and leaves snapshots unknown. Code defaults and `.env` disagree with each other and with the collection file. |
| Corpus approval vs corpus in use | The prepared corpus hash matches its index manifest. Approval is not granted. `.env` points at the corpus directory, which the retriever cannot open. The code default remains the 500-article corpus. |
| Dataset approval vs manifests | The eligibility approval matches manifest `research_v1_exploratory_eligibility_approved_v1` and hash `f2cc0fd1…`. It does not approve the unified files, research_v1's 478-candidate roster, FEVER, MultiNLI, or Final Test. |
| Protocol approval vs settings | Settings, loss, threshold, budget, attacks, and bootstrap values are proposals. The specification keeps them pending. No approval record is signed. |
| Recordings vs collection manifests | The collection manifest is pending and the Attempts directory is absent. Nothing matches an approved recording configuration because none is approved. |
| Collection authorization vs approved protocol | The authorization template says it may be signed only after protocol, corpus, and dependency approval. None of those signatures exist. |
| Final Test vs Development | v2 exposure and leakage audits record a pass. Custody is not independent. Development eligibility explicitly does not authorize Final Test. |
| Baselines frozen before evaluation | Package-local policies are frozen for old allowlists. Experiment baselines are not frozen for this protocol. Evaluation is not authorized. |
| Readiness documents agree | They do not. See the contradictions below. The live Experiment 3 validator and the Experiment 3 readiness report agree: `READY_FOR_APPROVAL`. |
| Approval records signed | The only signed research approval found for this protocol family is Development eligibility. Experiment 3 protocol, corpus, dependency, and collection records are unsigned templates. |
| Approval hash vs current bytes | Eligibility and the Experiment 3 template hashes were the hashes of the current unsigned artifacts at the last readiness preparation. Signing has not happened, so a stale signature is not in force. The corpus approval template cites the restored corpus hash, which this audit recomputed. |
| Experiment marked complete without a run | Experiment 3 empirical status is not complete. Synthetic results are labelled `SYNTHETIC`. Older runtime and baseline documents describe historical runs on other populations. Those runs are not Experiment 3. |

### Contradictions

- `evaluation/docs/research_protocol_readiness.md` says Final Test v2 is planned and not built. The v2 manifest exists and is `NOT_AUTHORIZED`.
- `evaluation/docs/experiment1_readiness_report.md` reports HotpotQA exploratory Development as 200 correct and 200 synthetic incorrect. The approved eligibility manifest, after quarantine, is 185 and 185.
- `evaluation/docs/experiment1_protocol.md` calls the exploratory audit provisional. The eligibility manifest is approved for Development eligibility and still forbids collection.
- `evaluation/docs/runtime_configuration.md` identifies a different branch and commit from HEAD `30c425e`.
- Three evidence locations are live at once: code default `data/evidence_corpus.json`, `.env` directory `evaluation/artifacts/person1/development_evidence_corpus_v1/`, and the collection file's `corpus.json`. Only the last is the prepared research corpus, and it is not approved.
- `shared_unknown` asserts one failure group while the Experiment 3 heatmap needs independent and correlated columns. The decision package says the heatmap is not estimable. That is consistent. Treating the one group as a measured dependence would not be.
- Unified files still contain FEVER and MultiNLI at 500 Development rows each. The protocol's observed research populations are GSM8K and HotpotQA. Using the unified Development runner would mix populations the eligibility manifest does not approve.

## D. Experiment 3 decision

Experiment 3 is genuinely **ready for approval**. It is not collection-ready and not execution-ready.

Before any Development collection, the research lead still has to accept or replace the proposed loss weights, threshold, suppression mode, bootstrap settings, and sample-size statement; choose a resource coefficient and one budget after a cost unit exists; approve and freeze the corpus; approve a dependency design that does not pretend `shared_unknown` was measured; and sign collection authorization. Person 2 then has to fill the unknown verifier snapshots and record Attempts. Person 3 then has to export a reputation policy. Final Test scoring stays unauthorized after all of that, until a separate release authorization exists.

This audit does not grant any of those approvals.
