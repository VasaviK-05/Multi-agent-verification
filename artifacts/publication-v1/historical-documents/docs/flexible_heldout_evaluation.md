# Held-out evaluation protocol and reproduction

Worktree: `<LOCAL_USER_HOME>/Multi-agent-verification/build/flexible-verifier-teams`; branch `codex/flexible-verifier-teams`; base `0b3595ef965d196f93916d10999c7fae63daf7af`. Existing uncommitted work and historical artifacts are preserved. No applicable AGENTS.md was found in the worktree or checked ancestor directories.

Freeze ID: `bcba68b5bd2857246fb3c4d9248f0eb2af4fd891b5b694335799826942ae519e`. See `artifacts/flexible-heldout-v1/freeze-manifest.json`, `evaluation-specification.json`, `precollection-seal.json` and `evaluation-code-seal.json` for identities, byte hashes, software versions, settings, exact reserved examples and analysis methods.

The two reservations each contain 40 examples in 20 paired groups; 80 examples and at most 320 full-roster calls total. The original roster order is semantic, evidence, rule, confidence. Only arithmetic and factual reservations are collected; no semantic cohort. Full-roster replay permits paired baselines but does not measure singleton deployment end-to-end latency.

The original resource-compatible checkout supplies unchanged verifier/retrieval/generation code and adapter configuration. The feature worktree supplies the opt-in held-out collection schema and flexible finalization. The runner explicitly loads the collector extension by its sealed path; it does not change the observer ROOT or relabel resources. Model/corpus/index/receipt, source and configuration identities must equal the frozen contract before inference. Local live service version and model digest must match; downloads, corpus expansion and index rebuilding are prohibited.

The original collector dispatches only `(question, answer, reference)` while recording label metadata separately. The new version `offline_heldout_recording_v1` permits only the exact reserved final roster and an explicit freeze ID. Held-out measurements retain final_test/heldout roles and cannot enter measurement calibration or training export. Existing recording request types retain their final-test exclusions.

Existing collect(), TimedVerifier, canonical report validation, observer checks and completeness checks are reused. Started and completed journals are flushed and fsynced. Resume requires identical request/setup and rejects any started attempt without an executed completion. Failed or abstaining completed attempts are retained, not selectively rerun. Each cohort is capped at 200 loopback generation requests and 700 metadata GETs; all non-approved HTTP requests are blocked. The existing confidence sampler has five samples and a 60-second timeout per sample; there is no new retry policy.

The frozen flexible candidates are identical to their development-best fixed baselines. The greedy comparison uses the existing selector initial_selected team, reputation-weighted aggregation and matching minimum-one coverage/contributor/threshold finalization. It retains the original greedy ranking, relative-cost heuristics and target-count defaults. It is a complete-team selection baseline, not a replay of the adaptive non-game stopping pipeline or an otherwise identical optimizer. No game-theory advantage may be inferred from beating that greedy configuration.

Minimum-two is a separate fixed-greedy-team contributor-contract ablation. All minimum-two fits remain infeasible; there is no fitted minimum-two policy to activate or compare as if selected probabilities existed.

The prepared corpus contains most test facts and references were pre-established. Reservations are source-known and procedural. Passing held-out questions does not establish unseen-document, reference-free or broad domain/difficulty generalization. The 90% coverage target constrains development only.

Final results are generated in `artifacts/flexible-heldout-v1/report.md` and `heldout-results.json` after both complete, compatible recording bundles exist. Percentile bootstrap intervals resample paired groups and paired methods. Zero-error intervals can be degenerate; neither those intervals nor these small constructed cohorts prove zero population risk.

Reproduction (a fresh collection requires separate authorization; use new output directories and never overwrite a freeze):

```powershell
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m scripts.flexible_heldout --source <LOCAL_USER_HOME>/Multi-agent-verification/build/multitask-policy42 --output artifacts/flexible-heldout-NEW
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m scripts.seal_flexible_heldout --frozen artifacts/flexible-heldout-NEW
# From original <LOCAL_USER_HOME>/Multi-agent-verification, run each authorized cohort:
.venv/Scripts/python.exe build/flexible-verifier-teams/scripts/collect_flexible_heldout.py --source <LOCAL_USER_HOME>/Multi-agent-verification/build/multitask-policy42 --frozen <LOCAL_USER_HOME>/Multi-agent-verification/build/flexible-verifier-teams/artifacts/flexible-heldout-NEW --cohort arithmetic
# Then factual; do not start it unless arithmetic integrity is complete.
# From the feature worktree, evaluate only after both collections complete:
<LOCAL_USER_HOME>/Multi-agent-verification/.venv/Scripts/python.exe -m scripts.evaluate_flexible_heldout --source <LOCAL_USER_HOME>/Multi-agent-verification/build/multitask-policy42 --frozen artifacts/flexible-heldout-NEW
```

Candidate policies remain offline. A later integration must use each frozen policy/context/contract together, verify actual resources, review this narrow evidence and obtain a separate activation instruction. No commit, push, merge, API activation, teammate algorithm, database or frontend change is part of this task.

arithmetic policy ID: `c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14`; context ID: `5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`; resource ID: `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.

factual policy ID: `0df33426333e0f7bbe6418fdf7900719dbda5182f68d50405b593b3341ec9d0d`; context ID: `d25662648b1266587bfa82698e78aace645f5160c91f05d5e235a4cefb2d782b`; resource ID: `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.


## Recorded evaluation implementation correction

The initial evaluator stopped before replay because Windows backslash source keys
were compared to a forward-slash collector exception. The first textual repair
also failed to replace the gate due raw CRLF handling; it again stopped before
replay. The final repair normalizes the path comparison, leaves every other
source/resource hash check intact, and accepts only the explicitly recorded
original-to-corrected evaluator hash chain. The collector remains separately
sealed and all decision code still matches its original freeze.

Original seals were preserved. See `evaluation-code-correction.json`,
`evaluation-code-correction-v2.json`, both retained evaluator source copies and
`evaluation-code-correction-v2.diff`. No metrics, policies, baseline rules,
thresholds, contributor/coverage rules, budgets, attacks, test reports or
reputations changed. The six focused tests include a regression proving that
Windows collector paths are recognized while a changed decision file is rejected.
The arithmetic clean result had already been inspected after candidate/spec
freeze; these repairs changed only evaluation plumbing, with no refit or inference.


Completed results are in `artifacts/flexible-heldout-v1/summary.md` (readable summary),
`report.md` (full metrics/intervals), `heldout-results.json`, and `final-verification.json`.
Arithmetic: 100% coverage and zero errors. Factual: 97.5% coverage, one false
rejection and one uncertainty. Both candidates exactly tie their development-best
fixed strategies. Greedy coverage is 87.5% and 90%, respectively. Paired coverage
difference intervals are [5,22.5] and [0,15] percentage points. Recommendations
remain limited to offline consideration and more independent evidence before
broader adoption; simulated attacks still expose singleton vulnerability.
