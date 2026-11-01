# Explicit adapter inputs for offline preparation

The preparation entry points require an explicitly supplied configuration:

```powershell
.venv/Scripts/python.exe -m scripts.factual_policy42 prepare --root PATH_TO_NEW_STUDY --adapter-config PATH_TO_REVIEWED_ADAPTER.json
.venv/Scripts/python.exe -m scripts.multitask_policy42 prepare --adapter-config PATH_TO_REVIEWED_ADAPTER.json
```

Python callers use `prepare(root, adapter_config=path)` for factual preparation
and `prepare(adapter_config=path)` for multitask preparation. There is no implicit
draft/template lookup. The committed `docs/verifier_project_adapter.template.json`
describes the existing `project_collection_adapter_v1` shape and can be used as an
explicit starting point; it is never selected automatically. Supply all fields
explicitly, including settings that have model-contract defaults, to avoid silent
sampling/execution choices. No credentials or machine-specific paths belong in
committed fixtures; tests create a temporary fully synthetic configuration.

Configuration validation uses the existing AdapterConfiguration schema before
reading study inputs or creating preparation outputs. Missing/unreadable/malformed
JSON, duplicate keys/nonfinite constants, absent fields and invalid schema/settings
fail with actionable `--adapter-config` messages and nonzero CLI status, without
creating a study output directory. Preparation intentionally rebinds only its four
new output locations: corpus, index directory, index receipt and service observation.
Model locations and every scientific/collection setting remain as supplied.
This retains the workflow's previous output layout; it does not create resource
identities or claim resources are ready. Nullable snapshot fields remain nullable
under the existing draft contract. Actual resource availability/hashes and readiness
still require the separate existing resource-preflight/index/collection phases.
Preparation performs no resource inspection, model loading or inference.

## Verified defect and related audit

Previously factual preparation implicitly read the ignored local
`docs/studies/factual-feasibility-draft-v1/adapter.draft.json` after writing its
preparation outputs. The working-tree test passed when that file happened to exist;
a tracked-only baseline export reproduced FileNotFoundError. Explicit adapter input
and early validation fix that reproducibility defect. This does not explain or
change any policy decision, probability, contributor guard, calibration or runtime
behavior. Existing historical artifacts are not regenerated.

The directly related multitask preparation also implicitly copied the prior
campaign's `adapter.json`. It now uses the same explicit validated input. Its
documented historical source snapshots and predeclared exclusion audit remain
required inputs to that specific campaign; this change does not turn it into a
new dataset/preparation framework or change source selection.

Other owned preparation tools (`prepare_factual_study_draft`,
`prepare_factual_team_pilot`, `prepare_broader_cost_measurement`) already require
`--adapter-config`. Draft filenames in their output-package protocols and in the
diagnostic collector's explicitly selected `--study-dir` are intentional producer
outputs, not an automatically discovered repository input. Older historical docs
refer to local draft paths and require their producer/review step; those are not
tracked input fixtures. The older draft/broader-cost CLIs can create an output
directory before all input validation finishes; this is a separate audit finding,
not the hidden configuration dependency fixed here. No teammate-owned adapter,
verifier, retrieval, generation, DB, API or orchestration code is changed.

## Regressions

The original seeded preparation test retains all deterministic equality,
grouped-answer, split separation and40-example metadata reservation assertions,
using a temporary synthetic adapter file. Additional tests cover explicit settings,
valid CLI preparation, missing/invalid configuration and failure before output
creation for both entry points. They do not load real reserved payloads or private
resource paths. A tracked-only source export plus only the reviewed patch verifies
that ignored local study files cannot mask dependencies.

Validation on 2026-11-01:

- Original test: working tree passed because the ignored draft existed; a clean
  tracked HEAD export failed with FileNotFoundError at the late draft-file read.
- Patched focused/related selection:73 passed in the working tree and73 passed in
  a fresh tracked HEAD export plus exactly the nine reviewed fix files. The export
  has no ignored study directory/configuration, `.env`, cached models or historical
  build inputs; synthetic multitask source inputs are created only in pytest temp.
- Full-suite guarded collection:1510 tests. The complete guarded run used a fresh
  export and blocked real model construction, external/service sockets and production
  database connections, while allowing Windows' internal asyncio socket pair.
  Result:1477 passed,23 failed,8 errors,2 existing skips. Baseline under the identical
  guard:1451 passed,24 failed,8 errors,2 existing skips. Failure-ID comparison shows
  the seeded preparation failure resolved and **no new failing test IDs**.
- Thirty remaining failure/error cases require prohibited live model/service
  resources; the other is the unchanged upstream
  `test_low_semantic_keyword_collision_is_ineligible_before_nli`, whose
  `data/articles_13083.json` is absent from tracked sources. The existing skips cover
  unavailable corpus and real Ollama checks. No skip/de-selection or assertion
  relaxation was added. An unguarded full-suite pass cannot be claimed within the
  no-inference/no-private-resources constraint. Earlier guarded sandbox attempts
  stopped on Windows asyncio/pytest infrastructure; they are not preparation
  regressions. Completed comparison records are local under
  `build/preparation-fix-full-comparison.json`.
- `git diff --check` passes. The supplied ZIP, selected policy bytes and original
  untracked local audit match their preservation hashes. No stored artifacts,
  policy probabilities or runtime/decision contracts were changed.

Focused command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_evidence_validation.py tests/test_factual_preparation_config.py tests/test_factual_study_draft.py tests/test_factual_team_pilot.py tests/test_pilot_preparation_cli.py tests/test_game_task_conditioning.py -q
```

Changed files are the two preparation scripts, shared
`scripts/preparation_config.py`, the original preparation test, synthetic
`tests/preparation_fixtures.py`, new `tests/test_factual_preparation_config.py`, this
document and the two updated factual/multitask command handoffs. No commit, push,
merge, fitting, inference, recollection or recalibration was performed.

## Exact guarded-suite reconciliation for publication

The saved baseline and patched results were compared by full pytest node ID,
not inferred from totals. Exactly one baseline failure disappeared:

```text
tests/test_game_evidence_validation.py::test_seeded_preparation_groups_variants_and_preserves_holdout
```

No new failure/error IDs appeared. The following30 cases were **blocked**, not
passed or diagnosed as implementation defects: the audit deliberately denied real
model construction, service sockets and production database connections. Their
identical node IDs occur in both baseline and patched exports.

```text
call tests/test_evidence_retriever.py::test_default_index_dir_is_keyed_to_the_corpus_stem
call tests/test_evidence_retriever.py::test_index_is_rebuilt_when_the_corpus_changes
call tests/test_evidence_retriever.py::test_index_is_reused_when_the_manifest_matches
call tests/test_evidence_retriever.py::test_tiny_corpus_never_answers_from_the_full_index
call tests/test_evidence_retriever.py::test_k_is_clamped_to_the_index_size
call tests/test_evidence_retriever.py::test_scores_are_cosine_similarities
call tests/test_evidence_retriever.py::test_term_weights_rank_rare_terms_above_common_ones
call tests/test_evidence_retriever.py::test_alaska_retrieval
call tests/test_evidence_retriever.py::test_einstein_retrieval
call tests/test_evidence_retriever.py::test_retrieval_recall
setup tests/test_evidence_verifier.py::test_real_label_map_is_checked
setup tests/test_evidence_verifier.py::test_correct_capital_answer
setup tests/test_evidence_verifier.py::test_wrong_capital_answer
setup tests/test_evidence_verifier.py::test_incorrect_artificial_intelligence_answer
setup tests/test_evidence_verifier.py::test_who_question
setup tests/test_evidence_verifier.py::test_topic_outside_corpus_is_an_abstention
setup tests/test_evidence_verifier.py::test_unrelated_answer
setup tests/test_evidence_verifier.py::test_multi_claim_answer_with_an_unsupported_sentence
call tests/test_self_consistency.py::test_real_nli_separates_agreeing_and_disagreeing_regenerations
call tests/test_validation.py::test_validate_endpoint
call tests/test_validation.py::test_validate_with_context
call tests/test_validation.py::test_orchestrator_pipeline
call tests/test_validation.py::test_wrong_addition_is_a_rule_rejection
call tests/test_verifiers.py::test_all_verifiers_inherit_base
call tests/test_verifiers.py::test_verifier_output_conforms_to_schema
call tests/test_verifiers.py::test_every_verifier_sets_decision_and_score_meaning
call tests/test_verifiers.py::test_semantic_verifier_correct_answer
call tests/test_verifiers.py::test_semantic_verifier_wrong_answer
call tests/test_verifiers.py::test_semantic_verifier_paraphrased_answer
call tests/test_verifiers.py::test_semantic_verifier_without_context
```

The genuine baseline fixture failure, distinct from those guard blocks, is:

```text
tests/test_evidence_verifier.py::test_low_semantic_keyword_collision_is_ineligible_before_nli
```

It raises FileNotFoundError for `data/articles_13083.json` in both tracked-source
exports. No retrieval/verifier code or assertion was changed to hide it.
The two pre-existing conditional skips are:

```text
tests/test_evidence_verifier.py::test_t_s_eliot_supported_by_real_corpus
tests/test_self_consistency.py::test_real_ollama_self_consistency_on_easy_fact
```

The first lacks its real corpus; the second cannot reach Ollama under the audit's
service-connection block. These are not new skip markers or deselections. The full
suite was not rerun for publication: its saved failure records were reconciled,
and the focused73-test preparation selection was rerun in a fresh tracked HEAD
export with only this reviewed patch.

Integration requires a real, reviewed adapter JSON supplied explicitly via
`--adapter-config`. The synthetic fixture is only a contract test, not a usable
resource setup. This preparation fix has no remaining integration blocker; the
separate missing upstream corpus and live-resource checks remain unavailable.
