# Person 1 approval checklist

None of these decisions is approved. `evaluation/config/protocol_readiness.yaml` records `approved: false` for each corresponding item. Person 1 documents the options; the named owner must decide and record the decision (with approver and date) in that file and the relevant protocol document.

| # | Decision | Current state | Impact if left open | Options | Who approves |
|---|---|---|---|---|---|
| 1 | Research claim | Working wording in `research_objective.md` | Confirmatory reporting cannot be framed | Accept wording; narrow it (for example, GSM8K-only false acceptance); revise | Research lead / supervisor |
| 2 | Primary-outcome cost treatment | Code's worst case is cost-augmented (`mean_loss`) | Primary estimand ambiguous | Cost-augmented worst case; decision-only worst case plus separate cost; report both with one primary | Research lead |
| 3 | Loss weights | Unapproved pilot proposal: FA 1.0, FR 1.0, uncertain 0.2 | No validation loss, payoffs, or policies | Adopt the proposal; asymmetric FA > FR; sensitivity grid declared in advance | Research lead with team |
| 4 | Resource coefficient and cost scale | Proposal `0.1 / budget` (ms) varies with budget | Budget-sensitivity results not comparable | Fixed coefficient on a common Person 2 cost scale; coefficient 0 with cost reported separately | Research lead + Person 2 |
| 5 | Decision threshold | Engine default 0.55 on an uncalibrated signed score | Execution contract cannot be frozen | Freeze 0.55; select on Development only, then freeze | Research lead |
| 6 | Minimum contributors | Defaults easy 2 / medium 2 / hard 3; proposal overrides all to 2 | Strategy feasibility differs by configuration | Production defaults; proposal override; other declared rule | Research lead (game owner) |
| 7 | Coverage constraint | Expected-capability feasibility plus achieved-coverage guard; no percentage threshold | Unclear whether a Development coverage floor applies | No extra constraint; declared minimum Development coverage | Research lead |
| 8 | Budget levels (Experiment 2) | `experiment_contracts.json` → `budgets.values = null`, `minimum_count = 3` | Experiment 2 cannot run | About three levels chosen from Development Person 2 costs, then frozen | Research lead + Person 2 |
| 9 | Attack strength and suppression mode | Code: full-direction transformations; proposal: suppression `unavailable` | Experiment 1 scenarios not frozen | Keep `report_corruption_v1` as is; `abstention` suppression; target-group schedule | Research lead (game owner) |
| 10 | Dependency assumptions | Proposal: all verifiers in one shared-unknown group | Dependency-group aggregation and attacks rest on an assumption | Keep shared-unknown; document known shared resources; per-verifier independence | Game owner with verifier owners |
| 11 | Sample size and power | Development 400 groups (existing partition); Final Test 1,319 per benchmark (operational cap) | No power or precision claim possible | Accept operational sizes as exploratory; compute power after the Development pilot yields variance | Research lead / statistician |
| 12 | Final Test construction policy | All-gold, no negative class | False acceptance not estimable on Final Test | Accept and restrict claims; add negatives under an approved, independently adjudicated policy (new version) | Research lead |
| 13 | Human labels / adjudication | 871 unresolved queued; 0 reviewed | Binary set stays at 1,179; HotpotQA has no negatives | Run the blinded two-reviewer protocol; accept automated labels as-is with stated limits | Research lead + named reviewers |
| 14 | Acceptance of automated labels | `human_adjudication_claimed = false` | Label validity is a limitation of every result | Accept with disclosure; require review of a sample | Research lead |
| 15 | HotpotQA shared-context pairs | 15 History and 15 Development groups share context; 2 supporting facts | Possible related-question leakage into reputation | Accept as a limitation; build a new version removing one side using a label-blind rule | Research lead |
| 16 | Final Test custodian and OS protection | No custodian; inherited broad ACLs | Final Test cannot be called protected | Name a custodian who moves labels to a separately controlled account and verifies denial | Supervisor / custodian |
| 17 | License and citation | `dataset_info.json` license fields empty | Publication and redistribution terms unconfirmed | Confirm from the GSM8K and HotpotQA releases | Research lead |
| 18 | Verifier eligibility by benchmark | Not specified | Rule Verifier on HotpotQA may be scientifically meaningless | Declare an eligible verifier set per benchmark | Research lead + verifier owners |
| 19 | Evidence corpus for Evidence Verifier runs | Two corpora documented; research_v1 binds neither | Evidence results not reproducible | Pin corpus and index identity per run | Evidence Verifier owner |
| 20 | Person 2 roster size and Experiment 4 roster size | Ordered rosters generated; size not chosen | Cost collection and live validation cannot start | Choose *N* groups; take `group_rank ≤ N` | Person 2 / research lead |
| 21 | "700 results" artifact | Not found | Compatibility cannot be assessed | Owner supplies a path or run ID, or records that it does not exist | Teammate who produced it |
