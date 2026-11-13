# Research readiness completion report

## Executive summary

The seven readiness requirements now have implementations, documents, configurations, validation scripts, and tests. None of the new packages is an approval or an authorization. Development eligibility was already approved and was not re-signed. Experiment 3 remains `READY_FOR_APPROVAL`. Development collection is not authorized. Final Test v2 stays sealed. No empirical experiment was run and no research recording was created.

What was implemented: task-population contracts that refuse unsupported success; a canonical evidence-file path; structural failure groups; dataset, corpus, and custody auditors; collection and scoring guards; a readiness checker.

What was documented: verifier compatibility, resource declaration, dataset roster correction, corpus suitability, protocols for Experiments 1–4, a protocol index, custody rules, this report, and the dashboard.

What was tested: `tests/test_research_readiness.py`, `tests/test_experiment3_prerequisites.py`, and `tests/test_experiment3_visualizations.py`.

What was frozen: nothing. Configurations are declared and pending. The canonical corpus path and hashes are recorded. Model-weight hashes, hardware, the cost unit, and the random seed stay unknown or null.

What was approved: no new approval. The existing Development eligibility approval remains the only signed eligibility decision.

What remains pending: research-lead approval of settings, corpus, dependency, and protocols; Person 2 snapshots and costs; Person 3 reputation policy; independent Final Test custody; collection authorization; Final Test release.

Current Experiment 3 status: `READY_FOR_APPROVAL`.

## Seven-requirement completion matrix

| Requirement | Implementation | Documentation | Tests | Approval | Authorization | Final status |
|---|---|---|---|---|---|---|
| Task populations | Contracts and unsupported handling | `verifier_task_compatibility.md` | Population, word-problem, evidence, and confidence tests | PENDING | Not applicable | TECHNICALLY_READY |
| Verifier and resource configuration | Canonical corpus file, source hashes, structural groups | `verifier_resource_freeze.md` | Path and failure-group tests | PENDING | NOT_AUTHORIZED | READY_FOR_APPROVAL |
| Datasets and labels | Count, overlap, and eligibility audit | `dataset_research_readiness.md` | Roster and overlap test | Eligibility already approved; broader approval PENDING | NOT_AUTHORIZED | READY_FOR_APPROVAL |
| Evidence corpus | Hash and coverage audit without loading the retriever | `evidence_corpus_readiness.md` | Corpus integrity test | PENDING | NOT_AUTHORIZED | READY_FOR_APPROVAL |
| Final Test custody | Metadata-only check and path refusal | `final_test_custody_protocol.md` | Seal and refusal tests | PENDING | NOT_AUTHORIZED | NOT_AUTHORIZED |
| Scientific protocols | Experiments 1–4 specified against the 185-group HotpotQA roster | Protocol documents and index | Protocol text test | PENDING | NOT_AUTHORIZED | READY_FOR_APPROVAL |
| Collection and scoring | Manifests, schemas, and refusal guards | Collection and scoring packages | Unauthorized collection and scoring tests | PENDING | NOT_AUTHORIZED | NOT_AUTHORIZED |

## Artifact inventory

Created:

- `app/verifiers/task_compatibility.py`
- `evaluation/research_readiness/canonical.py`
- `evaluation/research_readiness/guards.py`
- `evaluation/research_readiness/audit.py`
- `evaluation/research_readiness/check.py`
- `evaluation/scripts/check_research_readiness.py`
- `evaluation/scripts/audit_research_datasets.py`
- `evaluation/scripts/evaluate_evidence_corpus.py`
- `evaluation/scripts/validate_final_test_custody.py`
- `evaluation/config/research_v1/` verifier, resource, environment, dataset, corpus, custody, collection, baseline, scoring, and protocol files, plus `readiness_status.json`
- `evaluation/docs/verifier_task_compatibility.md`
- `evaluation/docs/verifier_resource_freeze.md`
- `evaluation/docs/dataset_research_readiness.md`
- `evaluation/docs/evidence_corpus_readiness.md`
- `evaluation/docs/scientific_protocol_index.md`
- `evaluation/docs/research_readiness_dashboard.md`
- `evaluation/docs/research_readiness_completion_report.md`
- `evaluation/artifacts/research_readiness/evidence_coverage_summary.json`
- `tests/test_research_readiness.py`

Updated:

- `app/verifiers/evidence_retriever.py` so a directory setting resolves to `corpus.json`
- `.env` and `.env.example` so `EVIDENCE_CORPUS_PATH` is the corpus file
- `tests/test_verifiers.py` so the inheritance test uses the small test corpus and does not rewrite the research index
- Experiment 3 specification, collection configuration, dependency configuration, dependency decision, and the three affected approval-record hashes
- Experiment 1–4 protocol documents, the Experiment 3 specification note, both readiness reports, the corpus preparation note, the Final Test custody protocol, the research_v1 freeze note, and the protocol-readiness note that had said v2 was never built

The eligibility manifest, corpus bytes, and index files were not modified.

## Implementation results

Rule verification now has an explicit item contract. `What is 25 + 17?` is a verified arithmetic check. A GSM8K word problem that is not one explicit expression returns `UNSUPPORTED` and `UNSURE`. The GSM8K population remains unsupported because word problems are not that pattern.

Semantic verification requires reference text and records that similarity is not correctness. Evidence verification returns insufficient evidence when the gate is missed and does not treat FEVER or GSM8K as supported by the HotpotQA paragraph corpus. Confidence records that agreement is not correctness and that the research generator hash is unknown.

The evidence path used by `default_corpus_path()` is the 1,844-article corpus file. The 500-article and 13,083-article corpora stay labeled historical. Their recorded hashes still match.

Failure groups follow shared code resources. They are provisional and unmeasured. The synthetic two-group fixture remains unusable as empirical dependence.

Dataset counts were recomputed: unified 8,000 / 2,000 / 2,000; eligible 744 candidates and 372 groups; HotpotQA 185. Sealed Final Test identifier overlap was 0. Labels were not opened.

## Test results

Command:

`python -m pytest tests/test_research_readiness.py tests/test_experiment3_prerequisites.py tests/test_experiment3_visualizations.py -q --tb=line`

Result: 38 passed, 0 failed, 0 skipped.

Also run: `python -m evaluation.scripts.check_research_readiness`, `python -m evaluation.scripts.evaluate_evidence_corpus`, and `python -m evaluation.scripts.validate_final_test_custody`. All exited 0. Experiment 3 `assess()` returned `READY_FOR_APPROVAL` with no blockers.

## Research readiness

| Layer | Status |
|---|---|
| Technical readiness | Task contracts, path resolution, audits, and guards are in place. Weight snapshots are not pinned. |
| Dataset readiness | Development eligibility is approved. Broader population approval and adjudication are pending. |
| Scientific approval | Pending for protocols, loss, threshold, budget, corpus, and dependency. |
| Collection authorization | Not authorized. |
| Final Test custody | Sealed. Designated-creator appointment only. Independent verification is PENDING. Release and scoring are not authorized. |
| Execution readiness | Not ready. |
| Empirical completion | Not complete. |

## Remaining external decisions

| Decision | Role | Supporting document | Required evidence | Blocks |
|---|---|---|---|---|
| Accept or revise loss, threshold, suppression, bootstrap settings, coefficient, and budget | Research lead | `experiment3_settings_proposal.json` | Signed protocol record with accepted settings | Collection and execution |
| Approve and freeze the corpus with its coverage limits | Research lead | `evidence_corpus_approval_package.json` | Signed record whose hash matches the corpus file | Collection |
| Approve structural failure groups as a stress model, not a measured correlation | Research lead | `experiment3_dependency_configuration.json` | Signed dependency record | Collection |
| Authorize History and Development collection | Research lead | `collection_authorization_package.json` | Signed authorization after the three approvals above | Collection |
| Supply model digests, prompt hashes, hardware, seed, timeout, and cost unit | Person 2 | `verifier_config.json` | Observed values, not invented numbers | Execution |
| Export a reputation policy | Person 3 | `experiment3_reputation_policy_inputs.json` | Observations from authorized recordings | Experiment 4 and empirical reputation claims |
| Appoint an independent Final Test custodian and authorize release | Independent custodian and research lead | `final_test_release_authorization_template.json` | A real appointment and a separate scoring signature | Final Test scoring only |

Unresolved candidate adjudication is also external. This work did not invent reviewer decisions.

## Experiment 3 decision

`READY_FOR_APPROVAL`. The validator blockers are empty. The experiment is not collection-ready, not execution-ready, and not empirically complete.

## Final checklist

Completed:

- Task compatibility matrix and tests
- Unsupported results cannot remain successful verifications
- Canonical evidence file path
- Structural failure groups with no measured-dependence claim
- Dataset count and roster reconciliation, including HotpotQA 185
- Corpus and index hash checks
- Final Test metadata check with labels unopened
- Protocols 1–4 aligned to the canonical roster
- Collection and scoring refusal guards
- Readiness status file and dashboard
- Approval templates left unsigned

External:

- Research-lead signatures
- Person 2 measurements
- Person 3 policy
- Independent custody and Final Test release
- Any human adjudication of unresolved candidates
