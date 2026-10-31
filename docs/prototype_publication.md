# Prototype source publication and ZIP handoff

This feature branch publishes the completed owned analyzer/task-history, informative
contributor, versioned game/solver, offline recording recovery/readiness, empirical
study and prototype packaging work. Existing collection/calibration/fitting contracts
are preserved. No DB/API/frontend or teammate verifier/retrieval/generation changes
are part of this publication.

## Supplied artifact, separate from Git

The integration owner obtains the already supplied `multitask-prototype42-v1.zip`
from the study owner. Its local deliverable is `build/multitask-prototype42-v1.zip`;
see the original chat handoff or request an out-of-band copy of those exact bytes.
The repository has no approved remote artifact-storage convention. No release asset
was uploaded and no ignored build file was force-added. Cloning the source does
not download the ZIP, private recordings or external resources. Do not rerun
collection/fitting to recreate this supplied deliverable.

Bundle ID: `98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34`.
ZIP SHA-256: `99516fbe460e816c68601509ca7e202cbcd3880d8d4250ec655f422244ec657c`.

```powershell
Get-FileHash -Algorithm SHA256 PATH_TO_SUPPLIED_ZIP
.venv/Scripts/python.exe -m app.game.offline.prototype validate --bundle PATH_TO_EXTRACTED_DIRECTORY
```

The loader must print the exact bundle ID and both artifact IDs documented in
[the complete prototype handoff](multitask_prototype_bundle.md). The archive contains
sixteen hash-verified files and its extracted layout has been loaded successfully.
Original content-addressed policy bytes and their historical revision/provenance
are unchanged; the later source publication does not rewrite that provenance.

## Restricted engineering scope

Arithmetic uses the approved50% expected clean-development coverage policy; factual
uses the approved experimental25% policy. Both require reference context and are
restricted to their40 prepared question identities. Unseen questions fail safely;
this is not open-domain verification. Semantic equivalence has no supported decisive
policy or deployed diagnostic entry.

Every positive-probability plan contains two verifiers. Rule, Evidence and Confidence
are materially selected across the two policies, not necessarily together. Always-
abstaining plan probability remains approximately39.394% arithmetic and33.333%
factual; all zero and tiny probabilities remain serialized without pruning.
Similarity, judgment agreement and signed aggregate scores are not calibrated
correctness probabilities. Development data and simulated attacks establish no
held-out superiority or unseen-question guarantee.

Integration requires compatible external model, corpus/index/build-receipt, local
service/configuration and implementation resources plus a live resource observer.
Models/corpus are not bundled. Loading validates expectations, not live readiness.
Pin the bundle ID, use the actual analyzer/router/provider and legitimate selector,
provide caller RNG and observer, preserve three-outcome finalization and explicit
safe failures. No API activation or scope expansion is authorized here.

## Verification for this publication

Executed now: bundle/file hashes, exact artifact IDs, numerical certificates and
compatibility via the public loader; original-vs-bundled policy bytes; ZIP member
bytes and extracted-directory loading;40-question scopes; three historical artifact
reloads and seven stored preservation hashes. AST parsing and privacy/conflict scans
reviewed all candidate source/tests/docs. The only path scan matches in committed
candidates are explicitly synthetic rejection fixtures, not private-machine paths.
Whitespace and staged-diff checks are required before commit.

Reused completed evidence:130 focused package/task/runtime/three-outcome/reliability
tests passed;11 retained-report execution traces demonstrate acceptance, rejection
and uncertainty;14 safe-failure checks cover reference/resource/budget/scope/tasks.
Their saved records bind the exact bundle ID, and current application bytes match
the sealed source digest. These are prior results, not tests rerun for publication.
No fresh inference, calibration, fit, final evaluation or production write occurred.

The historical evidence baseline failures were repaired upstream and later probes
passed; no baseline failure is reproduced in these publication checks. Private/raw
study inputs, all build outputs, caches and the ZIP remain outside Git. The pre-
existing `docs/game_empirical_build_audit.md` remains uncommitted and untouched:
it is a historical local audit containing a private-machine link.

## Exact reviewed files in this source publication

- `app/decision/coverage.py`
- `app/game/artifacts.py`
- `app/game/execution_contract.py`
- `app/game/finalization.py`
- `app/game/models.py`
- `app/game/offline/collect.py`
- `app/game/offline/collection.py`
- `app/game/offline/evaluation.py`
- `app/game/offline/replay.py`
- `app/game/policy.py`
- `app/game/research/readiness.py`
- `app/game/research/specification.py`
- `app/game/solver.py`
- `docs/game_policy_build.md`
- `scripts/run_factual_diagnostic.py`
- `app/analysis/task_analyzer.py`
- `app/game/coverage_contract.py`
- `app/game/offline/budget_sensitivity.py`
- `app/game/offline/coverage.py`
- `app/game/offline/prototype.py`
- `app/game/offline/reliability.py`
- `app/game/prototype_bundle.py`
- `app/game/reliability_contract.py`
- `app/game/research/evidence_validation.py`
- `app/game/task_conditioning.py`
- `docs/factual_coverage_exploration.md`
- `docs/factual_policy42_results.md`
- `docs/factual_reliability_first.md`
- `docs/multitask_policy_results.md`
- `docs/multitask_policy_workflow.md`
- `docs/multitask_prototype_bundle.md`
- `docs/multitask_uncertainty_tradeoffs.md`
- `scripts/factual_coverage_analysis.py`
- `scripts/factual_policy42.py`
- `scripts/factual_reliability_analysis.py`
- `scripts/multitask_policy42.py`
- `scripts/multitask_uncertainty_report.py`
- `scripts/multitask_uncertainty_sweep.py`
- `scripts/package_multitask_prototype.py`
- `scripts/validate_multitask_prototype.py`
- `scripts/validate_uncertainty_sweep.py`
- `tests/test_game_clean_coverage.py`
- `tests/test_game_evidence_validation.py`
- `tests/test_game_prototype_bundle.py`
- `tests/test_game_reliability_first.py`
- `tests/test_game_task_conditioning.py`
- `tests/test_game_three_outcomes.py`
- `docs/prototype_publication.md`
