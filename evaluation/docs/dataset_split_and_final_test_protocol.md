# Research data splitting and final-test protection protocol

## Scope and read boundary

This audit inspected the unified History and Development records, verified subset v1, controlled negative candidates v1, their manifests/summaries, data preparation and baseline code, offline reputation/policy code, and existing exposure documentation. No Final Test example record was opened. No dataset, experiment result, adjudication record, or existing manifest was changed. No split was generated and no research experiment was run.

The existing documents `evaluation/docs/existing_split_research_readiness.md`, `evaluation/docs/final_test_manifest.md`, and `evaluation/docs/existing_results_audit.md` document prior Final Test exposure. The exposed `unified/final_test.json` is not an unseen or protected holdout. The protocol below concerns a future, separate custodian-controlled holdout.

## 1. Existing data inventory relevant to splitting

| Artifact | Observed population | Labels/groups and use |
|---|---:|---|
| `evaluation/datasets/unified/history.json` | 8,000 records: 2,000 each FEVER, GSM8K, HotpotQA, MultiNLI | GSM8K/HotpotQA each have 2 candidate variants per question. Unified rows lack explicit related-group IDs and label provenance. |
| `evaluation/datasets/unified/development.json` | 2,000 records: 500 each benchmark | Same schema and candidate-label limitation. It is the input to the current baseline runner. |
| `evaluation/datasets/verified_subset/v1_seed_20261104/` | Per benchmark: 100 questions / 200 candidates; 80 History, 20 Development | GSM8K: 91 verified correct, 0 verified incorrect, 109 unresolved. HotpotQA: 100 verified correct, 0 verified incorrect, 100 unresolved. Exact-question `related_group_id` values are present; both candidate variants are retained together. |
| `evaluation/datasets/verified_negative_candidates/v1/` | Per benchmark: 50 generated candidates; 40 History, 10 Development | All 50 per benchmark are labeled `verified_incorrect` under their construction-specific procedures. Candidate records retain source `dataset_id` but do not carry their own `related_group_id`; the parent group is recoverable by joining to verified subset v1. |

The subset manifests identify the benchmark versions, source IDs, partition membership, selection seed, and source hashes. The verified subset quality check reports unique candidate IDs, unique question groups with both variants retained, History/Development-only membership, and no Final Test read during subset construction. The negative-candidate validator additionally reports unique candidate IDs, source IDs, and related groups within each benchmark, and matching source hashes.

`app/game/offline/arithmetic_pilot.py` is a separate constructed arithmetic fixture (its own summary describes 20 groups per role). It is not a source-backed GSM8K/HotpotQA sample and cannot be counted toward benchmark group availability or used to claim an external holdout is protected.

### Observed identity and candidate checks

- In the unified History and Development files, GSM8K and HotpotQA have zero normalized exact-question duplicates within each partition and zero normalized exact-question overlap between History and Development. This is an exact-text check, not semantic related-question clustering.
- The verified subset has 100 source question IDs and 100 exact-question groups per benchmark, with 80 History / 20 Development. Its validator confirms both candidate variants remain on their question group.
- All 50 controlled negative candidates per benchmark map to a source question in verified subset v1. Their 40/10 partition counts follow the source question. The selected negative groups are unique within each benchmark.
- All 50 GSM8K controlled candidates normalize to the same answer as the existing unresolved `candidate_1` (`gold + 1`) for their question. They are the same candidate content, newly supported by a stronger verification basis; do not count each as a second independent candidate or outcome. The HotpotQA explicit-negation candidates are additional answer variants and must be attached to the same source question group as their gold and borrowed variants.
- The unified file has no group IDs. The subset group IDs are based on exact normalized question identity and do not rule out paraphrases, shared facts/entities, or broader related-question leakage.

### Candidate-label caveat and current baseline

The unified `candidate_answers[].expected_correct` values are generation annotations for the synthetic GSM8K and borrowed HotpotQA answers; the existing split readiness and result audits do not establish them as independent correctness labels. The subset instead records `verified_correct`, `verified_incorrect`, or `unresolved` with a validation basis. In development, this yields 19 source-verified GSM8K correct candidates among 20 question groups and 20 source-verified HotpotQA correct candidates among 20 groups. The controlled negative set adds 10 incorrect candidates per benchmark in Development; those candidates are on those same 10 groups, not 10 new independent groups. GSM8K's 10 negatives replace/resolve the matching unresolved candidate content rather than increasing the unique candidate count.

`evaluation/baseline/adapters.py::_candidates` maps `expected_correct` directly to accept/reject, and `run_baseline_experiment.py` runs on unified Development. It does not read the verified-subset adjudication statuses or negative-candidate validation records. Therefore current baseline results cannot be treated as a label-corrected comparison on this subset. The baseline adapter sends each HotpotQA example's supplied context through the request; its own note says the Evidence Verifier instead retrieves from the configured corpus. A future comparison must declare one evidence condition and make each method's permitted information explicit and comparable. GSM8K worked solutions are audit provenance and must not be passed to a verifier unless the condition is explicitly reference-assisted and is identical for every method.

## 2. Partition responsibilities

| Partition | Permitted purpose | Prohibited use |
|---|---|---|
| **History** | Estimate verifier reputation from independently labeled historical examples and complete verifier-attempt records under a frozen update rule. | No Final Test identities, labels, candidates, outputs, or statistics. Do not include an example/group also used in Development. |
| **Development** | Construct payoff matrices; fit game policies; select baselines and aggregation restrictions; choose thresholds, budgets, attack strengths, coverage constraints, and other configuration; estimate compute feasibility. | No Final Test outcomes or tuning based on a custodian's protected results. |
| **Final Test** | One frozen confirmatory evaluation under the approved protocol, after code, policies, configuration, metrics, comparison rules, and analysis plan are frozen. | No reputation estimation, fitting, baseline selection, threshold/budget/attack tuning, candidate selection, or repeated peeking. |

This separation matches the offline path in `app/game/offline/records.py`: `history_reputation()` uses the History partition; `TrainingManifest` contains only History and Development outcomes plus an outcome-free `FinalTestReservation`; and `app/game/offline/evaluation.py::construct_payoffs()` fits on Development while `evaluate_final_test()` evaluates the already frozen policy. The runtime reputation repository can load persistent database feedback, so research runs must use the isolated offline History-derived snapshot rather than ambient persisted reputation.

Every group—including all candidate variants and any paraphrase/related-question cluster—must have one partition assignment. If a group is used for History reputation, no member or candidate of that group may enter Development policy fitting or Final Test. The same question may be evaluated under multiple predeclared attack/budget/method conditions; those are paired repeated measurements, not additional independent questions.

### Partition use across the four planned experiments

| Experiment | Development use | Protected evaluation use |
|---|---|---|
| Clean and attacked performance | Select compatible baselines and freeze attack implementations/severity and policy settings | Evaluate all declared clean/attack conditions on the same held-out groups |
| Budget sensitivity | Choose the budget levels and feasible strategy comparisons | Evaluate every frozen budget condition on the same held-out groups |
| Aggregation/dependency ablation | Fit the joint policy and each restricted ablation under matched data/settings | Compare frozen variants on paired held-out groups |
| Live runtime validation | Select supported runtime cases and configure non-outcome operational checks | Use a separately predeclared runtime case set or the frozen held-out roster; report measured latency separately from attempt-cost estimates |

If the live-runtime cases are drawn from Final Test, they remain protected until the runtime configuration and measurements are locked. Do not select only successful or convenient cases after observing outcomes.

## 3. Compatibility of the current verified and negative subsets

### Suitable as a development pilot with conditions

The subset has stable source dataset IDs, explicit partitions, exact-question group IDs, provenance, and separate status values. The negative set can be joined by `dataset_id` and partition. The benchmark-context-assisted HotpotQA records retain relevant supporting paragraph text and support references; this is not shared-corpus retrieval. GSM8K worked solutions support arithmetic audit but should remain hidden from ordinary verifier inputs unless a reference-assisted condition is declared.

The History/Development groups are disjoint in the subset. Thus the existing subset can serve as a small development-only pilot after candidate-label integration, input-condition normalization, and complete verifier-attempt collection. Do not treat the negative JSONL as an independent new question sample. For GSM8K, reconcile its 50 repeated `gold + 1` texts to the already present candidate record; for HotpotQA, append/identify the explicit-negation variant under the original question group. Preserve a single canonical candidate identity per distinct answer and retain source IDs/provenance.

### Not yet a complete offline research manifest

The subset and negative-candidate JSONL files contain answer-validation data, not the offline `Example` recordings required by `app/game/offline/records.py`. Each recording requires independent binary label provenance, all required verifier `Attempt` records, execution/configuration IDs, a complete-team cache contract, and stable example/question/group identities. The offline manifest validators reject split leakage by example, group, question, content, and run identity. An approved annotation mapping must decide whether the current source replay and constructed contradictions qualify as `independent_ground_truth` under the `Example.label_method` contract; they are not human adjudications.

The current baseline code is not a ready adapter for these files: it consumes the old boolean `expected_correct` field. A versioned adapter and annotation join are needed before baseline/policy comparisons, but this audit does not implement them.

## 4. Sample-size and statistical assessment

The verified subset provides only **20 independent Development question groups per benchmark** (40 total across GSM8K and HotpotQA). Its candidates do not double the independent sample size. In Development, the controlled negative set covers 10 groups per benchmark; the other candidate variants are not new groups. History provides 80 groups per benchmark, but those groups estimate reputation and cannot be counted again as Development or final evaluation observations.

The broader unified Development files contain 500 questions per benchmark, but their synthetic/borrowed candidate labels have not been independently established and the unified rows lack group IDs. Their raw count is not a verified policy-fitting sample size. The current baseline result audit describes 1,232 completed Development-side records from the old pipeline; it is not evidence that the verified subset is adequate and is not compatible with corrected labels/configuration by default.

**20 Development groups per benchmark cannot be declared adequate for policy fitting from the available evidence.** No power or precision claim is possible: the team has not supplied a minimum effect of interest, target confidence-interval width, variance/correlation estimates at group level, planned independent group counts by outcome/condition, policy-search complexity, or allowable compute budget. The four-condition attack matrix, multiple strategies, and candidate pairing further reduce the effective support of each cell. Use a development pilot to estimate uncertainty and runtime, then approve the population and analysis plan; do not borrow Final Test outcomes to decide whether the sample is sufficient.

For paired comparisons, compute method/condition differences on the same question group. Form confidence intervals by resampling entire related-example groups (stratified by benchmark if declared), carrying all candidate variants and all paired conditions together in each resample. Do not bootstrap candidate rows independently. Report the number of independent groups and unresolved labels in every metric denominator. The final-test analysis plan must define the interval procedure and treatment of unresolved/failure cases before release.

## 5. Existing leakage and exposure risks

1. The original unified Final Test is documented as exposed through prior dataset/candidate audits and pilot v1 review preparation. Do not access its rows again for this protocol and do not call it an unseen holdout.
2. Unified History/Development have no broad related-example cluster IDs. Exact text and ID checks do not detect paraphrases, linked questions, common evidence, or source-document dependence.
3. Source-question candidate pairs must remain grouped. Controlled negatives are tied to their parent source question. Counting candidate rows as independent observations inflates sample size.
4. The GSM8K negative set duplicates candidate text already present as unresolved in the subset. Duplicate answer strings must be reconciled before evaluation.
5. Unified `expected_correct` can silently score unsupported negatives as ground truth; the existing baseline adapter uses it. Do not use baseline outputs as corrected-label results without revalidation.
6. HotpotQA has two distinct evidence conditions: supplied benchmark context and shared-corpus retrieval. Current artifacts and baseline adapters do not establish a single uniform condition across all verifiers.
7. The source-preparation scripts load broad upstream splits to construct candidate records. Existing repository access and data-preparation history are not an access-control or custody log.

## 6. Protected holdout procedure (design only; do not execute yet)

The existing exposed Final Test identities must be excluded from any future protected set, but this audit did not read those records or recover their IDs. `dataset_audit.md` records GSM8K `main` with 7,473 train and 1,319 test rows, and HotpotQA distractor with 90,447 train and 7,405 validation rows. The current generator assigns 2,000 GSM8K train rows to History and 500 to Development, and samples 500 GSM8K test rows for its exposed Final Test; it assigns 2,000 HotpotQA train rows to History and 500 validation rows each to Development and exposed Final Test. Thus nominal unassigned source counts exist (4,973 GSM8K train rows and 88,447 HotpotQA train rows outside those History/Development memberships, plus other unused source rows), but this arithmetic is not an exposure audit. The generation script loads/maps whole source splits, the raw sources are in the shared repository, and there is no complete research-team access ledger. This audit cannot certify any remaining identity as previously unexposed; it also does not identify or exclude the exposed Final Test IDs because those records were not opened. The repository alone therefore cannot certify a new protected pool.

Before creating a holdout:

1. **Name a data custodian** who is not selecting policies or comparing methods. Resolve whether a source pool can be certified unexposed. Prefer a newly authorized source/version kept in custodian-only storage if existing benchmark examples have already been inspected. If using the same releases, the custodian—not the development team—must reconcile source IDs against all previously exposed records, pilots, audits, result files, and development memberships without returning identities or labels to developers.
2. **Approve population and grouping first.** Fix benchmark/version, candidate construction and label provenance, allowed context condition, verifier interface, and eligibility rules. Group by source question ID; join all correct, controlled-negative, borrowed, and paraphrase variants; add related-example/source-document links where discoverable. Split entire connected groups.
3. **Select at group level.** Use an approved seed and versioned algorithm; stratify only on predeclared source metadata (benchmark, difficulty, label/candidate condition). Keep all candidates and evidence for a question together. Check no group, question, candidate, content identity, or source ID crosses History/Development/Final Test. Do not open the exposed Final Test to perform this check; the custodian should use a separately maintained exposure ledger.
4. **Seal identity and labels.** The custodian stores source IDs, group-to-partition map, labels/answers, candidate strings, and evidence in a restricted location. A development-facing manifest contains only non-outcome custody receipt, dataset version, algorithm/seed, opaque reservation ID, aggregate counts, and hashes; do not publish test identities, questions, answers, or labels. Hashes support integrity but do not protect data that developers can read.
5. **Freeze before release.** Before any held-out payload or outcome is released, hash and record the source commit, executable code, policy artifact, reputation snapshot, verifier/model/configuration versions, evidence corpus/index, threshold, budgets, attacks/severities, aggregation/baseline rules, metric implementation, randomization/integration procedure, and statistical analysis plan. Require a custodian-signed freeze receipt.
6. **Evaluate once.** The custodian validates the frozen receipt, releases or executes the reserved payload, records integrity/failure checks without disclosing outcomes during execution, and returns the predeclared aggregate/per-example result package only after the run is complete. Any tuning after seeing outcomes requires a new protected set and must be disclosed.

`TrainingManifest` / `FinalTestReservation` in `app/game/offline/records.py` and `evaluate_reserved_final()` in `app/game/offline/evaluation.py` provide useful structural safeguards: training has no final outcomes, reservation keys are checked against the released payload, and final evaluation requires a frozen artifact/readiness check. These are validation contracts, not filesystem access control; operational custody still needs separate permissions and an audit log.

## 7. Reproducibility and custody requirements

For each partition, record benchmark release/version, original split and source IDs, candidate IDs and construction version, group IDs and grouping edges/reasons, label status/source/method, context condition, evidence resource/index hashes, software commit, and a SHA-256 digest. Record the grouping and normalization implementation version, seed, sampler, strata, and full group-to-partition ledger in custodian storage. Keep source files immutable and generated partitions versioned.

For every run, bind the manifest ID to actual source/result files, complete verifier attempt/failure ledger, reputation priors and History-derived snapshot, policy/payoff matrix, thresholds, loss/cost scale, resource limits, attack specification, environment, and metric code. Save expected-instance rosters and explicit reasons for skips; do not infer missing results as failures or successes. Preserve every predeclared condition and report undefined selective risk when decision coverage is zero.

## 8. Outstanding decisions

| Decision | Current finding | Required before holdout/fitting |
|---|---|---|
| Research population | GSM8K and HotpotQA v1 are small H/D development subsets; FEVER is a different claim task; MultiNLI is not current QA interface | Approve benchmarks and whether a separate FEVER protocol is in scope |
| Correctness basis | Subset labels mix source-linked/replayed gold answers and construction-specific negative checks; not human adjudication | Approve which methods meet the offline independent-ground-truth contract and how unresolved labels are handled |
| Candidate identity | GSM controlled negatives duplicate v1 `candidate_1`; Hotpot explicit negatives add a variant | Reconcile canonical IDs; keep every variant on parent group |
| Evidence condition | Hotpot benchmark-context-assisted and shared-corpus conditions are not equivalent | Choose one condition or preregister separate matched conditions for all methods |
| Grouping | Exact-question keys exist only for subset; no semantic related-example graph | Audit paraphrases, entities, and shared sources; approve grouping resolution rules |
| Development size | 20 groups per benchmark; 10 with a controlled negative per benchmark | Set precision/power or feasibility target and acquire/approve more eligible Development groups if needed |
| New holdout eligibility | Residual source rows exist nominally, but prior broad source access and absent access ledger prevent unexposed-status certification | Custodian must attest an unexposed source pool or obtain a new restricted source/version |
| Holdout size/seed/strata | Not selected | Approve using Development-only estimates and compute constraints; custodian records seed and group allocation |
| Custody/freeze | Existing Final Test is exposed; no new holdout exists | Appoint custodian, configure restricted storage/access log, freeze evaluation receipt before release |
| Analysis plan | Paired group-level comparisons are appropriate; formal power inputs absent | Predeclare paired CI method, resampling strata/replicates, unresolved/failure handling, and multiplicity policy |

## Readiness conclusion

The current verified subset and controlled negative candidates can support a **small development pilot after candidate identity reconciliation and a versioned adapter**, but they do not establish that 20 Development groups per benchmark are adequate for policy fitting. The existing History/Development memberships are distinct at the exact-question/group level available in v1; broader related-example leakage is not ruled out. Existing baseline scores are tied to the old `expected_correct` annotations and are not label-corrected comparisons.

The existing Final Test is exposed and cannot be reused as a protected holdout. Although source releases contain nominally unused identities, this repository and its scripts do not establish that any pool is previously unexposed. A custodian must attest access history or obtain a new restricted source before any protected split is generated. No split was created by this audit.
