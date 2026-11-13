# Source lineage and supersession

Canonical location: docs/research_v1-recording-handoff/. The original consolidation base is 4c2a2eb9ea1afd953e44f5194b2cc1a6e9b95a1a. Final review fetched and compared remote main 3e8769075420b4bf3e565bf46854f55a77a4a35f read-only; no main working-tree update or merge occurred. See final-review.md. This avoids the unrelated Experiment 1 commits on e38a96d and preserves main's optional runtime journal hooks.

| Original | Canonical authority | Resolution |
|---|---|---|
| A TECHNICAL-VALIDATION / durable-attempt-lifecycle | file_journal implementation, tests and filesystem-support.md | Retain tested primitives and CLI wiring; add actual synthetic boundary validation. Do not duplicate the journal. |
| B recording-config / scope / resources / contract | Same named canonical files | Preserve authentic hashes, raw IDs/tuples and all pending approvals. Historical setup remains evidence, not a fabricated live binding. |
| A + B old readiness and handoff drafts | final-review.md and tabmayee-handoff.md | Old missing-package/import/durability statements describe earlier stages only. |
| A calibration investigations | archive/package-a/calibration-identity-investigation.md | 464 exact timing rows including 8 warmups; 24 unresolved question-only-trim matches, not verified canonicalization. |
| B verbatim-input rule | input-contract.md and input_contract.py | Additive game-owned offline question validation, no content transformation; all identifier and independent-label protections remain. |
| B missing confidence tag/sample count | resource-compatibility.json | Freeze records llama3.2:3b / 5 samples; live service/config custody still unverified. |
| B dirty-working-tree ownership check | ownership.py + owned-files.json | Check committed/staged/unstaged/untracked changes against pinned main; clean tree is valid. |
| A + B overlapping decision/blocker prose | decisions-required.md + blocker-register.csv | One current authority; original registers retained for evidence, not duplicate active instructions. |

archive/original-manifest.json records SHA-256 for every original A/B file. Archived files are not altered to repair old paths or findings. The complete current source manifest identifies new engineering bytes separately from historical 662bd5c app digest ecb12d8934a3d55dd745887ecf9b3c164ea308f3b07eaa895a6d69f246e87e6c. No historical equivalence is manufactured. Any future request needs its own truthful code/environment/config identity and approval.
