# Configurable research-scale candidate dataset protocol

## Audit and implementation plan

The repository already contains a 100-question-per-benchmark pilot, controlled GSM8K negatives, identity reconciliation, and a label-preparation adapter. The pipeline reuses their exact-question normalization, rational arithmetic replay, supporting-context extraction, canonical row construction, and offline label mapping. It does not rebuild the pilot or replace its records. The scale-up builder reads only unified History/Development, raw GSM8K train, raw HotpotQA train, the configured prior reconciled dataset, and the selected YAML configuration. It does not open unified Final Test, GSM8K test, or HotpotQA validation.

The existing pilot has 100 groups per benchmark (80 History / 20 Development), 450 candidate records combined, and 291 label-preparation rows plus 159 unresolved exclusions. Its 50 GSM8K controlled candidates reconcile to existing candidate identities; they are not extra observations. The pilot has no genuine verifier Attempts or complete offline Examples and is not sufficient for policy fitting. Existing split and result documents report prior exposure of the old Final Test; that partition is not a protected holdout.

Implementation sequence: (1) read and validate the prior reconciled rows; (2) pin their group IDs and partition assignments; (3) deterministically sample only new exact-normalized groups from H/D source records; (4) construct candidates and apply only existing conservative validation rules; (5) run the existing offline label adapter; (6) write a new immutable version with source/output hashes; and (7) validate the full group roster, statuses, identities, and partition assignments.

## Sources, versions, and limits

| Benchmark | Source | Version recorded by repository | Eligible local source rows used |
|---|---|---|---|
| GSM8K | `evaluation/datasets/raw/gsm8k/train/` plus unified History/Development | `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866` | Existing unified H/D rows map to source train IDs; train contains 7,473 records. The test split is not opened. |
| HotpotQA | `evaluation/datasets/raw/hotpotqa/train/` plus unified History/Development | `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab` | Existing unified H/D rows; raw train has 90,447 records. Development context comes from the existing unified Development record. Validation is not opened. |

The locally stored dataset metadata does not declare license text or citation fields (they are empty). Source release/version identifiers are recorded, but licensing and citation should be confirmed against the benchmark release before redistribution. Every build hashes the explicit H/D JSON files, train-split files, prior reconciled files, and configuration. It never hashes a directory that might include a forbidden split.

## Allocation and current build

`evaluation/config/research_dataset.yaml` is the source of truth for v1 targets:

| Benchmark | History groups | Development groups | Total groups |
|---|---:|---:|---:|
| GSM8K | 300 | 200 | 500 |
| HotpotQA | 300 | 200 | 500 |
| **Combined** | **600** | **400** | **1,000** |

The 100 existing groups per benchmark are retained (80/20), so v1 adds 220 History and 180 Development groups per benchmark. Configurations for 2,000 and 5,000 combined groups are provided in `evaluation/config/research_dataset_2000.yaml` and `evaluation/config/research_dataset_5000.yaml`. The 5,000 target uses all 2,000 History and 500 Development source groups per benchmark in the current unified H/D artifacts. It is an upper bound for this exact source pool, not an assertion that the data are sufficient for statistical power or method fitting. The canonical machine-readable manifest is `evaluation/datasets/reconciled_candidates/research_v1/manifest.json`; `evaluation/docs/research_dataset_manifest.json` is a matching snapshot for documentation/discovery and should be refreshed after building a later canonical version.

The builder deterministically selects from eligible source groups with the configured seed and a partition/benchmark offset. Existing source IDs, candidate IDs, group IDs, and partition assignments are retained. New rows preserve the full originating unified record, including source metadata and the preprocessor's `expected_correct` generation annotation; the pipeline does **not** use that annotation to assign correctness. Each source question is one independent group, regardless of its candidate count. Candidate records are reported separately. Exact normalized text deduplication is enforced; semantic paraphrases, shared entities, common evidence sources, and broader related-question leakage cannot be ruled out by the current schema. The manifest lists selected question/candidate IDs and partitions; the summary reports generation-method counts, duplicate checks, and group overlap.

**Actual v1 counts:** recorded in `evaluation/datasets/reconciled_candidates/research_v1/validation_summary.json` and repeated in the final build report. The generated full version has 1,000 independent groups, 2,050 candidate records, 964 verified-correct, 215 verified-incorrect, and 871 unresolved candidates. History has 600 groups / 1,240 candidates (GSM8K 600; HotpotQA 640); Development has 400 groups / 810 candidates (GSM8K 400; HotpotQA 410). See the manifest for benchmark-by-partition counts. A candidate count is never presented as an independent question count.

| Benchmark | Partition | Independent groups | Candidate records | Verified correct | Verified incorrect | Unresolved |
|---|---|---:|---:|---:|---:|---:|
| GSM8K | History | 300 | 600 | 277 | 124 | 199 |
| GSM8K | Development | 200 | 400 | 187 | 91 | 122 |
| HotpotQA | History | 300 | 640 | 300 | 0 | 340 |
| HotpotQA | Development | 200 | 410 | 200 | 0 | 210 |
| **Combined** | **History + Development** | **1,000** | **2,050** | **964** | **215** | **871** |

“Candidate records” include answer variants; for HotpotQA, the preserved pilot includes extra explicit-negation variants. Status counts sum to candidate records, not independent groups.

## Candidate generation and label quality

### GSM8K

Each selected question retains its source-derived benchmark answer and `gold + 1` candidate from the existing unified candidate construction. For new groups, the official train worked solution is hashed and its tagged equations are replayed with exact rational arithmetic using `build_verified_subset.replay_gsm_solution`. The gold candidate is marked `verified_correct` only when the source final answer and complete replay agree. A generated alternative is marked `verified_incorrect` only when the existing narrow rule in `build_verified_negative_candidates.validate_gsm_discrete_count_negative` applies: exact integer result, discrete “how many” question, no ratio/rounding cues, and complete worked-solution replay; the candidate must also equal the distinct exact integer `gold + 1`. Otherwise it remains `unresolved`. This rule is construction-specific and does not estimate natural model-error prevalence or independently re-solve the problem semantics.

The original v1 GSM8K candidate IDs and stronger reconciliation statuses are copied unchanged. The v1 `gold + 1` candidate identity is not duplicated. Gold solutions and arithmetic traces are label provenance only; they are not included in the prepared verifier input fields.

### HotpotQA

The benchmark gold candidate can be `verified_correct` when it matches the benchmark answer and every supporting-fact reference maps to non-empty supplied context. This is benchmark-context-assisted validation, not shared-corpus retrieval. The alternative remains `unresolved`, even when it is a borrowed answer or differs from the reference answer. The builder tries to recover the donor by replaying the existing partition-ordered borrowing rule and records the donor ID only when it finds a deterministic match. Exact match and token F1 are diagnostics; they never decide factual correctness. No new HotpotQA negative is automatically labeled incorrect.

Existing v1 HotpotQA candidate records and source statuses are preserved, but the 50 pilot explicit-negation candidates previously marked `verified_incorrect` are **unresolved in this derived research version**. Their prior active status, method, evidence, and source record remain recorded. The earlier literal-negation/context-presence check does not by itself establish that a candidate is wrong for the target question. No source artifact is altered.

No human adjudication is fabricated. `verified_correct`, `verified_incorrect`, and `unresolved` remain separate. Any unresolved candidate is written to `unresolved_candidates.jsonl` and the offline adapter's `excluded_unresolved.jsonl`; it has no binary `answer_is_correct` label.

## Offline preparation and attempt compatibility

The builder calls `build_offline_examples.prepare_rows` and `make_summary` on the reconciled rows. Output files under `evaluation/datasets/offline_examples/research_v1/` are label-preparation records only. Each contains a deliberately narrow `verifier_input` object with the question, candidate answer, benchmark, and (for HotpotQA) supplied supporting-context passages. Gold answers, worked solutions, labels, and replay traces remain in separate provenance fields and are not members of `verifier_input`. No `Attempt`, verifier report, validation ID, execution configuration, runtime cost, or `app.game.offline.records.Example` is created. The label method `independent_ground_truth` is structurally accepted by the existing Pydantic contract, but the research team must approve whether the source-replay and controlled-construction methods qualify scientifically.

Future genuine verifier collection must join on stable `candidate_id`, benchmark-qualified `question_id`, and `related_group_id`. The recorder must capture real verifier identity, completion/failure state, report provenance, adapter/configuration versions, execution and validation IDs, and the cache contract required by `Attempt` and `Example`. It must use identical permitted input context across comparison methods. GSM8K worked solutions and correctness-provenance fields must remain hidden from verifier requests. For HotpotQA, declare the benchmark-context-assisted condition explicitly and keep it distinct from shared-corpus retrieval.

The current outputs contain **zero complete verifier Attempts and zero complete offline Examples**. They are not ready for reputation estimation, payoff construction, or policy fitting.

## Incremental versioning and commands

Build and validate v1:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py build --config evaluation/config/research_dataset.yaml
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py validate --dataset-dir evaluation/datasets/reconciled_candidates/research_v1
```

Scale to 2,000 combined groups:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py build --config evaluation/config/research_dataset_2000.yaml
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py validate --dataset-dir evaluation/datasets/reconciled_candidates/research_v2
```

Scale to 5,000 combined groups:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py build --config evaluation/config/research_dataset_5000.yaml
.\.venv\Scripts\python.exe evaluation/data_preparation/build_research_dataset.py validate --dataset-dir evaluation/datasets/reconciled_candidates/research_v3
```

Every output version is immutable: the builder refuses to write into a non-empty output directory. For another target, create a new YAML config, set target group counts, a new `dataset_version` and output paths, and point `incremental.base_dataset_dir` at the immediately preceding reconciled output. Expansions preserve prior IDs/groups/partitions and sample only the additional groups. Changing a config without executing `build` does not create or expand data. After any new reconciled version, regenerate offline preparation as part of the same build; do not carry forward stale prepared rows.

## Final Test protection

The YAML config sets `final_test.enabled: false` and `source: null`. The builder rejects any config that enables Final Test. It reads no Final Test records or identities. The old Final Test is documented as exposed and cannot be repurposed as an unseen holdout. A future confirmatory set requires a genuinely protected source or a custodian-certified unexposed pool, group-level identity exclusion, restricted custody, and a frozen code/policy/configuration/metric receipt before release. This pipeline creates no reservation or test split.

## Limitations and readiness

- The current exact-normalized deduplication does not find semantic paraphrases or all shared-source dependencies.
- The current v1 History/Development labels include automated source matching/replay and a small number of construction-specific negatives; they are not human adjudications.
- Borrowed HotpotQA alternatives remain unresolved. Hence the factual negative coverage can be low or zero among newly added groups.
- The 5,000-group option consumes the available unified H/D question groups; it does not create independent data beyond those sources.
- The pipeline does not establish sample-size adequacy, power, verifier execution quality, policy validity, or protected test separation.
- Final Test remains disabled and prior exposure is documented.

Before verifier recording, approve the label-method basis, input/context policy, and unresolved handling; then collect genuine complete-team executions. Before policy fitting, validate all `Example`/`Attempt` records and `TrainingManifest` leakage checks, use History only for reputation and Development only for payoff/policy/configuration selection, and demonstrate sufficient group-level Development support for the planned analyses. A new custodian-controlled Final Test remains a separate prerequisite for confirmatory evaluation.

## Build validation record

The small incremental pilot completed with 220 groups and 490 candidate records; its validator passed. The configured 1,000-group build completed with the counts above; its validator passed. A second build with identical selection/generation settings but separate output paths produced byte-identical candidate, summary, and offline-preparation files. The v1 reconciled-candidate, controlled-negative, and offline-preparation validators also passed after the build. The relevant automated test selection passed **168 tests**. No test inspected a Final Test dataset record.
