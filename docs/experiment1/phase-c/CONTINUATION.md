# Experiment 1 Phase C — recovery and specification continuation

**Updated decision: two exact training originals recovered; ten required originals and the execution-source ZIP remain unresolved. All four cohorts remain blocked for numerical scoring.** This report supersedes the earlier 12-missing-original conclusion without changing the historical audit snapshot.

## Git preservation and focused local commit

Active branch: `codex/evidence-poisoning-phase1`; HEAD: `e38a96d367610065e3679ec22fa162cfcc94daf5`. Phase 1 `6480ba7` and Phase A `9f8b64a` are intact; Phase B is commit `e38a96d`. One registered worktree exists. All Phase C files were untracked at the start; no staged changes were present.

```text
## codex/evidence-poisoning-phase1
 M app/game/offline/collect.py
 M app/game/offline/collection.py
 M tests/preparation_fixtures.py
?? app/game/offline/file_journal.py
?? app/game/research/prospective.py
?? docs/experiment1/phase-c/
?? docs/research_v1-precollection-proposal/
?? research/
?? tests/test_offline_file_journal.py
?? tests/test_prospective_collection.py
?? tests/test_prospective_evaluation.py
```

Local commit plan: `Preserve Experiment 1 Phase C recovery and comparison audit` on isolated branch `codex/experiment1-phase-c-audit`, parent `e38a96d367610065e3679ec22fa162cfcc94daf5`. Its entire tree diff is restricted to `docs/experiment1/phase-c/`. The active branch, HEAD and real index remain unchanged; a separate temporary index prepares the local commit. A local source-preservation branch `codex/experiment1-historical-input-source` will anchor the reflog-accessible `1277e9d` publication commit. No whole source checkout or restricted payload materialization is needed.

Proposed future PR scope: **Phase C audit documentation, read-only audit utilities, machine evidence, validation results and prerequisite ownership handoff only**. Base on the Phase B line (`codex/experiment1-retrospective-phase-a` currently points at the same `e38a96d`); do not target a base that would accidentally include unrelated implementation commits. No push, merge or PR creation is performed. The active checkout retains its untracked documentation copies; their committed versions live on the audit branch.

## Recovery investigation

Extended the prior audit to 3666 Git named-object entries reachable through **refs plus reflogs**, 93 unreachable tree objects, six discovered local checkouts and 21 ZIP containers. Checked ignored files, Downloads, Documents, Desktop, attachment storage and `/private/tmp`. ZIP directories were inspected and raw containers hashed; no ZIP member payloads were opened by the extension. Other checkout object-name searches found no exact canonical originals. `.Trash` was inaccessible (`Operation not permitted`); no global or remote absence claim is made. Anonymous unreachable blobs were not opened because they lack a safe role/path identity.

The earlier Phase C search used local refs/path logs without reflogs. **Including reflogs locates commit `1277e9d3ce91f1395e3deed7e7202748a5a04672`**, published 1 November 2026 by Vasavi Gayathri Kasina with message “Publish original owned study inputs and preservation handoff.” Publisher identity is known; original producer/custodian responsibility still needs confirmation. No fetch/network recovery was used.

| Required file | Discovery and authenticity decision | SHA-256 of found bytes |
|---|---|---|
| `build/multitask-policy42/arithmetic/training-manifest.json` | `1277e9d3ce91f1395e3deed7e7202748a5a04672:build/multitask-policy42/arithmetic/training-manifest.json`. Exact historical training bytes; locator hash, typed manifest/reservation, History/resource binding match current policy. Whole-freeze custody still incomplete. | `c87d65246015919c02d86c4c83f39e0ded6ede02d25aa551a034b66a738ed485` |
| `build/multitask-policy42/arithmetic/development-evaluation.json` | `1277e9d3ce91f1395e3deed7e7202748a5a04672:build/multitask-policy42/arithmetic/development-evaluation.json`. Genuine older Development record found, **rejected as current-policy equivalent**. | `e146f2adafe5cfde34395aa4478e2f584d68c597f96a7f8e4efbd7c7c9c87a97` |
| `artifacts/flexible-heldout-v1/freeze-manifest.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/flexible-heldout-v1/precollection-seal.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/flexible-teams-v1/input-hashes.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/compound-study-36-v1/preparation/study.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/compound-study-36-v1/preparation-seal.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/remaining-category-studies-v1/compound-85/candidate/freeze.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `build/multitask-policy42/factual/training-manifest.json` | `1277e9d3ce91f1395e3deed7e7202748a5a04672:build/multitask-policy42/factual/training-manifest.json`. Exact historical training bytes; locator hash, typed manifest/reservation, History/resource binding match current policy. Whole-freeze custody still incomplete. | `9be8da9773eaced47faae3ff49e4e1536391be21824bb29f1e2c664cf5fd6e3c` |
| `build/multitask-policy42/factual/development-evaluation.json` | `1277e9d3ce91f1395e3deed7e7202748a5a04672:build/multitask-policy42/factual/development-evaluation.json`. Genuine older Development record found, **rejected as current-policy equivalent**. | `fb00b72373e64d08f3566c119a12a19e35af0994bbbb32d1036dbe498ffe86b9` |
| `artifacts/remaining-category-studies-v1/reference-50-v1/seal.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/remaining-category-studies-v1/reference-50-v1/fit/freeze.json` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer. Provenance not authenticated. | Not found; registered expected hash retained in machine register |
| `artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` | No authentic original found in inspected sources. Custodian: research lead/original publication or study producer (Tanmayee coordinates source custody). Provenance not authenticated. | Not found; registered expected hash retained in machine register |

All 12 original canonical paths remain absent in the active checkout: recovery is by authenticated Git object identity, not by silently populating ignored build paths. The two exact training files each contain 40 History and 40 Development examples plus outcome-free final reservation metadata. No Final Test partition, labels or report was opened. The known original source ZIP hash has no match among the 21 inspected containers.

### Why the two older Development records cannot close the gate

Both are typed `role=development`, name the matching training manifest and use the same attack declaration. However their execution contracts lack `team_requirements`; the current frozen policies require minimum selected/informative contributors of one. Their source-evaluation IDs fail the current policy binding:

| Cohort | Older candidate content ID | Required `clean_coverage.source_evaluation_id` |
|---|---|---|
| arithmetic | `b1101768d7a2ba0ea44da68708767c2301a54a3006be9f9116f4b471cef3e76d` | `a59218d2a00b4f09c4ef6e444682d3e20381ebd45b8c5bc76a89b923ed6658df` |
| factual | `28268477feeadf614f121eb138718a9c304a7b9bd4f6522400343bfff7d1750c` | `ee242866bcaff592167ec3ba21723c82c916b576b49187c27dbc7b643a04effc` |

These are related, non-equivalent historical records. No contract field, content ID, report or evaluation was edited, regenerated or reconstructed. The correct original minimum-one Development evaluations remain requested. The training-file hashes match the previously noncanonical locator, but this does not promote the missing whole freeze, seals or public audit views into originals.

`research_v1` candidate, rehearsal, calibration, eligibility and evidence-poisoning records were kept separate. A pre-existing factual training copy under `research/evidence-poisoning-phase1/followup/recovered/` is only a locator; the original Git object is the authenticated source used here. No unrelated tree was edited.

## Original comparison specifications versus retrospective expansion

Original protocol metadata supports the historical method declarations below. Missing canonical seals/freezes prevent complete independent authentication that every original definition was fixed before Final Test. “Historical documented” therefore does not mean newly certified preregistration.

| Method | Arithmetic / Factual | Compound-85 | Reference-50 |
|---|---|---|---|
| Full frozen minimax | Existing full policy and certificate; 100% Rule / Evidence singleton, reputation | Existing joint policy and certificate; 100% Evidence base fact + Rule derived sum, reputation on both obligations | Existing mixture: stored `0.16666666666666663` Semantic and `0.8333333333333334` Confidence+Semantic, reputation |
| Coverage-aware greedy | Historical captured complete selector team: Confidence+Rule / Confidence+Evidence, reputation. Complete-team comparator, not adaptive stopping | **Unavailable**; no independently defined comparable component executor | Historical captured Confidence+Semantic row exists; whole freeze missing |
| Development-selected fixed | Historical coverage-eligible worst validation loss, then declared tolerance/cost/ID rule. Same row as full policy for these two cohorts | Historical fixed joint plan documented; exact canonical study/freeze needed to authenticate selection | Historical coverage-eligible selection rule documented; authoritative frozen selected identity **unknown** |
| Uniform over feasible rows | Expanded retrospective method, no complete real freeze | Expanded retrospective method, no complete real freeze | Expanded retrospective method, no complete real freeze |
| Aggregation-restricted games | Expanded retrospective methods; exact restricted numerical certificates missing | Expanded retrospective component methods; restrictions must apply to every obligation; certificates missing | Expanded retrospective methods; certificates missing |

The implementation also includes a separately named clean-Development fixed baseline. It is a retrospective expansion, not a replacement for the historical worst-case Development baseline. No baseline was selected anew. No restricted LP was solved on empirical inputs. The exact full-policy probabilities, including zero rows, remain unchanged.

### Contract consistency

| Cohort | Feasible rows | Development coverage floor | Decision threshold | Minimum selected / informative | Resource coefficient (per ms) | Budget (ms) |
|---|---:|---:|---:|---|---:|---:|
| arithmetic | 16 | 0.9 | 0.55 | 1 / 1 | 4.704037204857504e-06 | 21258.33526502247 |
| factual | 16 | 0.9 | 0.55 | 1 / 1 | 6.263683617787064e-06 | 15965.046464995248 |
| reference | 16 | 0.5 | 0.55 | 1 / 1 | 6.025989641677816e-06 | 16594.78458249673 |
| Compound-85 | 2 joint rows | 0.85 | 0.55 per obligation | 1 / 1 per obligation | 4.704037204857504e-06 | 84.19308958157974 joint plan |

False-accept and false-reject weights are 1.0; uncertainty weight is 0.2 in every cohort. Atomic resource coefficients equal the respective original 0.1/budget calibration. Compound retains its declared inherited coefficient and equal joint-plan costs; it must not be recalibrated to 0.1/current joint budget. The original reliability-first validation objective, tolerance/epsilon and secondary attempt-cost tie-break remain authoritative. Decision-only loss and cost-inclusive loss must be separately labelled; the original Arithmetic/Factual report defines decision loss without resource penalty.

All 16 atomic rows derive from frozen feasible teams and the two existing aggregations; they are not newly enumerated from current verifier availability. The two Compound rows retain the Evidence/Rule obligation split and common reputation or dependency-group aggregation. Capability requirements, task isolation, unknown dependency handling, binding to the submitted answer, recorded resources and complete-team finalization remain enforced.

Fixed strategy selection requires each row to meet its Development coverage floor. Captured greedy is retained as specified even if it misses the distribution floor. Uniform means exactly 1/N over frozen feasible rows; it is not coverage-filtered or reweighted to help the game. Coverage compliance must be disclosed. Stored Development coverage diagnostics (arithmetic from already frozen rows only, no replay):

| Cohort | Full mixture | Captured greedy | Uniform diagnostic, not a prepared comparison |
|---|---:|---:|---:|
| arithmetic | 1.0 | 0.875 | 0.9375 |
| factual | 0.975 | 0.9 | 0.9375 |
| reference | 0.5 | 0.6 | 0.3 |
| compound | 0.8958333333333334 | unavailable | 0.8958333333333334 |

Reference uniform would miss its 0.50 floor; Arithmetic greedy misses 0.90. These limitations must be reported, not repaired by changing definitions. Full-policy coverage constraints are preserved rather than imposed retrospectively as eligibility filters for unrelated methods.

Original statistics stay separate: Arithmetic/Factual 10,000 paired group resamples, seed 20261102; Compound 1,000, seed 1102; Reference 1,000, seed 1103. Expanded Phase A reporting remains retrospective, 95% intervals / 5,000 repetitions / seed 20261112. Compound 0.85 and Reference 0.50 are explicitly post-Development amendments, not unchanged original 0.90 settings.

## Exact readiness mismatch diagnosis

Expected reporting commit `9f8b64aa18cbd25292699888b2ee1f5ff0ca554e`; observed `e38a96d367610065e3679ec22fa162cfcc94daf5`. That difference is the Phase B documentation/input-contract-test commit, not an executable application change. Expected source fingerprint `411491fc3951e75328299896118842778f755401f87c297659ad8b163baa0c4b`; observed `ae5f0f93a1c9d5f4b895d9e93d018e43e0701539383e5200bd370a3487aa853c`.

Both Phase A and Phase B source trees reproduce expected fingerprint `411491fc3951e75328299896118842778f755401f87c297659ad8b163baa0c4b` **when the 14 reviewed `.gitattributes` CRLF checkout rules are honored**. A raw Git-blob fingerprint `98a7e37ace90f7833c3229da7f32a92adee93b1189baaebc07b04aa710887309` is not the checkout identity and must not be mistaken for incompatible verifier edits. No source normalization was applied to the historical fingerprint or actual checkout.

Exactly four application source differences explain today’s checkout mismatch:

| File | Expected SHA-256 | Observed SHA-256 |
|---|---|---|
| `app/game/offline/collect.py` (modified_working_tree) | `06de808a7e950aa3cec1904275ee13947a3c015b6ee7fa5807d95505a419319a` | `e238f010654a8c0d799836f444334bd13d0cfb66a6f8f9929f65fa4462564d7d` |
| `app/game/offline/collection.py` (modified_working_tree) | `79023cafef880223ea800d86e43001d8ab0e35b05b49e3f76a782a1a7ddf954b` | `3eea07eff4bc7b8ca7d2bdf468e642e4b6c8f35c8d2e2f959e2ac95a11e2b9bd` |
| `app/game/offline/file_journal.py` (added_untracked) | `None` | `8c30ce5e73fe5e72403336fb30c23f169739099d62e1555ab479c418afc588f7` |
| `app/game/research/prospective.py` (added_untracked) | `None` | `397c28d7d7fba922cc0658823da79d6dc43f271f5dd78ec784c526c37a077dc4` |

The two modified collector files introduce journal/durable-write behavior and sink-before-append ordering; the added file journal/prospective modules also enter the fingerprint because it includes all `app/**/*.py` and top-level `scripts/*.py`. The changed `tests/preparation_fixtures.py` is outside that fingerprint but is part of the current test environment. No teammate-owned code was modified in this audit.

Expected and observed reporting environment **match exactly**: Python 3.12.0, NumPy 2.1.3, SciPy 1.15.2, Pydantic 2.11.3. No `reporting_environment_mismatch` was reported. This does not establish the original verifier/model/native runtime environment: collection metadata separately names source revision `2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`, application-source digest `daf466121a83c800b1116f97c6a07d62685fd1b18d4a7100f47bde0c819a441a`, and the missing custody ZIP. Current external resource compatibility is unobserved, not a measured failure.

| Failure class | Current finding |
|---|---|
| Missing historical originals | Ten unresolved required records plus execution-source ZIP; two training originals recovered in Git only |
| Source revision | `source_commit_mismatch`; Phase B commit differs from candidate source revision |
| Source bytes | `source_bytes_mismatch`; four unrelated dirty/added application files |
| Reporting environment | Exact match, no environment gate failure |
| Original runtime/resources | Recorded identities validate; complete execution-source custody/current resource attestation unavailable |
| Baseline specification | Expanded comparison freezes absent; Reference fixed identity unverified; Compound greedy unavailable by design |
| Final Test authorization | No current exact-manifest release/scoring approval; reserved inputs remain unopened |

Restoration recommendation: use a new isolated source checkout of the recorded Phase A revision with its attributes and pinned reporting dependencies; verify the exact checkout fingerprint before any reporting. For original collection/runtime reproduction, obtain and authenticate the original source ZIP and file map; never assume a clean commit alone reproduces its working source. Keep this audit branch separate from the exact source checkout. No identity check or historical manifest was weakened to obtain a pass.

## Cohort readiness and validation

| Cohort | Evidence advanced | Remaining scientific blockers | Scoring authorized |
|---|---|---|---|
| Arithmetic | Exact History/Development training manifest recovered and current binding validated | Correct minimum-one Development evaluation, three shared canonical freeze/seal/index files, reviewed research specification and expanded comparison | No |
| Factual | Exact History/Development training manifest recovered and current binding validated | Same missing evaluation/custody gates; evidence specification and expanded comparison | No |
| Compound-85 | Existing complete History/Development component bundles and transfer source checks retained | Canonical study, preparation seal, candidate freeze, complete component comparison and execution-source custody | No |
| Reference-50 | Existing authentic training bundle/manifest and Development evaluation retained | Canonical seal/fit freeze, authoritative fixed identity, reviewed specification and expanded comparison | No |

All six **untouched existing candidates exit 2** with `source_commit_mismatch`, `source_bytes_mismatch` and four cohort blocker entries. They still describe absent canonical paths; the new recovery evidence does not silently update their old reason strings or authorize scoring. Original Semantic remains infeasible/excluded (0.90 floor, maximum stored coverage 0.575, no policy).

Focused validation rerun: **38 passed in 272.92 seconds** across the three Experiment 1 test files; **2 passed, 42 deselected in 4.32 seconds** for the two uncertainty checks. Total **40 passed**, no test failures. Metadata-only assembly revalidated 39 unchanged allowed files; fresh readiness made zero inference/optimization calls and read no final payloads. The new investigation additionally parsed only the four named historical training/Development Git blobs for provenance checks.

Existing isolated dependencies and the explicit optional-model guard were reused; model construction raises, and pytest guards forbid socket/psycopg2 connections. Fake synthetic fixtures and synthetic solver checks are software validation, not historical refitting or empirical collection. Initial audit utility assertions caught and rejected the incompatible Development candidates; a component-ID serialization assumption was corrected in the audit utility only. No reporting implementation change was needed. Machine records are in `readiness-current.json`, `comparison-contract-audit.json`, `mismatch-investigation.json`, `recovery-investigation.json` and `other-checkouts-search.json`.

## Owner handoff and next scoring gate

`OWNERSHIP-HANDOFF.md` supplies concrete requests and acceptance evidence for Vasavi (game/reporting/baselines), research lead/custodian (originals/splits/authorization), Raunak (verifier/evidence resources), Tanmayee (execution source/runtime/collector), and Samika (persistence only if an application-persistence claim is required). No teammate was contacted and no teammate-owned component was edited.

**Immediate next action:** the original custodian must supply the two current-policy-bound minimum-one Development evaluations and eight missing canonical metadata originals, plus the execution-source ZIP. Preserve the two recovered training blobs through the local recovery-source ref; review/materialize them only in an isolated assembly checkout. Then validate full provenance, resolve genuine baseline specifications, and reconcile the exact source/environment. Expanded Development-only preparation requires its own explicit retrospective approval if no authentic existing comparison freeze can be supplied. Only a successful readiness check plus explicit release/scoring authorization for the exact manifest can unlock numerical scoring. No verifier run, refit, policy resampling on restricted inputs or Final Test access is a substitute.
