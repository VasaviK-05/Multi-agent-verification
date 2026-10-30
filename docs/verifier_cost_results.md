# Measured verifier costs: local campaign and code review

The approved 2026-10-28 cost-only campaign completed **344 real attempts**:
86 each for semantic, evidence, rule and confidence. The request audit recorded
**430 local generations and four local metadata GETs**, all returning HTTP200.
There were no raised verifier failures/timeouts, retries, missing observations,
warmups, exclusions, downloads or paid services. Reports/abstention counts were
not retained by this existing cost-only collector. A returned call is not a claim
about its judgment, correctness or absence of internally handled provider errors.

The existing `mean_attempt_wall_time_ms_v1` estimator includes every measured
call and its first-call effects. Millisecond estimates (mean / median / nearest-rank p95):

- Semantic: **30.955616 / 28.301850 / 39.269800**, n86, execution failures0.
- Evidence: **42.124591 / 23.433650 / 147.836000**, n86, execution failures0.
- Rule: **0.132202 / 0.082050 / 0.161200**, n86, execution failures0.
- Confidence: **11831.109355 / 11469.350850 / 12696.482000**, n86, execution failures0.

These costs describe the **arithmetic-heavy sample (80 arithmetic, six factual)
and observed local setup**, not universal verifier costs. They estimate sums of
attempt wall times, not money, CPU time or concurrent request latency. This short,
reference-assisted convenience sample does not characterize long-form answers,
structural rules, large corpora or production concurrency. Earlier arithmetic and
six-example diagnostic observations were not pooled into this campaign.

## Availability and original identities

**The empirical bundle is not pushed.** The repository ignores `build/` and has no
established tracked empirical-calibration bundle convention. Original files include
absolute host paths and machine-specific resource/approval references. They remain
intact locally; no redaction, relocation or force-add changed their content identities.
Teammates get code, templates, tests and this metadata, not the calibration bytes.

The exact repository-relative local run directory is:
`build/verifier-cost-calibration-proposal-20261028-v2/run-20261028-01/`.
Its file-by-file sizes and SHA256 digests are in
[verifier_cost_artifacts.local.json](verifier_cost_artifacts.local.json).
That inventory contains metadata only; no model, index, request payload or final outcome.

- Calibration ID: `1a2abc5663193e025f9c7e62805dbad5e9d6b720a1a6895b7f40e91f779ab992`.
- Setup fingerprint: `93029e22dfadd1babdfb360f70252113ede0ca17f58bf106ee18b44aea8a9750`.
- Input digest: `4d927ec6749561b66742d4189f3b8353e489a778f27931ded75aa92108a687cc`.
- `calibration-v1.json` SHA256: `87d0818b0684e4f7405c52e0a96502b70f500a8761d0efaf44480f7e45967b84`.
- `measurements.json` SHA256: `62b13ccdac1cdb9cfa28f7a23018b75f6b95aad6073ba52133112dc52d01c5a3`.

The calibration reloads, recomputes its identity/estimates and agrees with linked
measurements, reservation and frozen-file hashes. The freeze records genuine
user-approved **procedural** custody, not independent third-party custody.
Final-test contents/outcomes were never collected/opened for this campaign.

Measured code revision is `224a2e59792b7ee0183bfa64aed0481dcad57d78`; dirty-source
digest is `23f3a89528f61462bae2ce94ef333eb87df9a6c4555db836c263b3541ccf603f`.
That digest includes unfinished local offline modules. The reviewed commit is not
the measured source tree: provenance validation was tightened during review, and
unrelated pilot modules are omitted. Do not rewrite historical provenance or claim
this artifact calibrates a changed setup. Fresh collection after code/resource
changes requires its own setup binding and authorization.

## Included dependencies and deliberate exclusions

The calibration loader needs reviewed pre-existing offline-builder work:

- `app/game/offline/records.py`: outcome-free reservation and TrainingManifest,
  split validation and history-only reputation loading.
- `app/game/offline/evaluation.py`: training-only binding, metrics, explicit solver
  tolerance and separate guarded release validation for reserved final records.
- `app/game/policy.py`: optional explicit tolerance, preserving the existing default.
- `app/game/research/specification.py` and `readiness.py`: dedicated training schema
  and readiness support, preserving evidence and scientific gates.
- `app/game/offline/build.py` and `tests/test_game_build.py`: offline loading,
  validation and synthetic builder checks. No empirical policy is fitted here.

Collection/calibration code comprises `app/benchmark/{collect_costs,prepare_collection,
project_adapter}.py`, `app/game/offline/{timing,calibration,collection,collect,
recording_adapters,prepare_calibrated_context}.py` and the existing benchmark timer
alias. Preparation templates and optional runtime requirements are included.

Separate arithmetic-pilot implementation/proposal/fitting work, study drafts with
host-specific paths, fixed-campaign runners and generated build outputs remain
uncommitted. The arithmetic-only adapter portion of recording_adapters and the
diagnostic runner's request-budget test are also excluded from staging; their
working-tree bytes remain intact. The labelled/report and diagnostic contracts
remain separate; diagnostic observations cannot be promoted to calibration/training.

Review found and regression-tested two provenance gaps: one run could identify
different examples/purposes across verifiers, and measurement export did not
revalidate saved pre/post observations. Both now reject inconsistent inputs.
Neither fix changed verifier algorithms or historical empirical bytes.

No API/database/persistence/startup/frontend integration, baseline-ranking change,
production reputation change, empirical policy fit or PR is part of this delivery.

## Source validation for delivery

Tests were run against a fresh `git checkout-index` snapshot, so excluded local
pilot modules/runners could not satisfy imports accidentally. The command selected:
`test_cost_calibration`, `test_project_collection_adapter`, `test_game_collection`,
`test_diagnostic_collection`, `test_game_build`, `test_game_offline`,
`test_game_research`, `test_game_foundation`, `test_game_runtime`,
`test_game_completion`, `test_verifier_selector`, and `test_offline_benchmark`
under `tests/`, with `python -m pytest ... -q`.

That run had 514 passes, one demonstrated baseline failure, and two Windows sandbox
rename failures. The two exact synthetic publication tests passed outside the
sandbox: `tests/test_game_build.py -q -k test_cli_end_to_end_never_opens_final_outcomes`.
Thus 516 distinct selected tests passed; one baseline failure remains. Earlier
overlapping subset counts (83 passes after the provenance fixes) are not added.

The baseline `test_cli_unresolved_template_is_read_only_and_reports_digests` compares
the actual Git revision to hard-coded `9d21eba...`; an unchanged HEAD archive at
`224a2e5...` reproduced the failure. No test was weakened or skipped to make it green.
The same unchanged archive separately reproduced the three known evidence probes
(strong support/rejection become uncertainty, conflict becomes no_relevant_evidence),
with the neutral control passing. Verifier/analyzer algorithms were not changed.

Staged/working-tree `git diff --check` passed. The complete reviewed source inventory
was scanned for private-key/token patterns and absolute user-directory paths, with
no findings. Optional model/runtime dependencies are explicit in
`requirements-verifier-collection.txt`; no dependency installation or collection ran
as part of review. New tests and all builder tests use synthetic fixtures only.

Additional included test files are `tests/test_cost_calibration.py`,
`tests/test_game_collection.py`, `tests/test_project_collection_adapter.py`, and the
dependency-independent portion of `tests/test_diagnostic_collection.py`.
The seven verifier JSON templates and the three verifier workflow guides are
included, alongside the result summary and metadata-only local artifact inventory.

Exact remaining local work: `app/game/offline/arithmetic_pilot.py`,
`app/game/offline/pilot_proposal.py`, `docs/arithmetic_pilot42*.md`,
`docs/game_empirical_build_audit.{json,md}`, `docs/studies/`,
`docs/verifier_collection_blockers.json`, `docs/verifier_cost_missing_inputs.json`,
`scripts/prepare_broader_cost_measurement.py`, `scripts/prepare_factual_study_draft.py`,
`scripts/run_factual_diagnostic.py`, `tests/test_arithmetic_pilot.py`,
`tests/test_factual_study_draft.py`, `tests/test_pilot_abstention_contract.py`, and
the excluded sections of `recording_adapters.py`, `test_diagnostic_collection.py`,
and `docs/game_policy_build.md`. All ignored build artifacts remain local as well.
