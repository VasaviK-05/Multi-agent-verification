> Historical PR35 document. Current approved-eligibility compatibility and Handoff A: [eligibility-approved-v1/tabmayee-handoff.md](eligibility-approved-v1/tabmayee-handoff.md). Original text below is preserved; original identity is pinned in [historical-identities.json](eligibility-approved-v1/historical-identities.json).

# Scientific decisions and approvals required — canonical register

Nothing in this proposal is frozen. The technical input-boundary conflict is resolved by verbatim_question_text_v1 without changing source tuples; this is not scientific scope or label approval. See input-contract.md and blocker-register.csv. Exact current engineering results are in final-review.md. Source manifests document deferred human approval/adjudication. Calibration's local freeze covers timing inputs only. The historical person3 protocol is not research_v1 approval.

## Required before collection

| Decision | Concrete proposal / evidence | Responsible owner |
|---|---|---|
| Dataset/population | All 774 exploratory Development rows, 387 groups; use exact IDs in development-scope.json. No approved rows documented. Keep 374 GSM8K /187 groups and 400 HotpotQA /200 groups distinct in analysis. | Research lead / game owner |
| Label estimand | Independently adjudicate; alternatively explicitly approve provisional exploratory analysis with suitable separate label contract. No zero-review independent-ground-truth claim. | Research lead + dataset custodian |
| Split custody | Source audit reports ten Development questions overlapping previously exposed processed Final Test and History/Development shared context. This is source metadata only; no held-out payload opened. Custodian must decide admissibility and supply outcome-free reservation; identify affected groups without exposing outcomes. Scope must be regenerated if exclusions change. | Dataset custodian / research lead |
| Analyzer and requirements | Freeze per-question domain/task, QuestionAnalysis/context/scoring versions and known supported requirements. Proposed arithmetic for GSM8K and fact/retrieval for HotpotQA require review, not benchmark-name inference. | Game owner |
| References | Null GSM8K; approved exact structured-context rendering for HotpotQA, shared across candidates; never gold/labels. Select reference-assisted estimand explicitly. | Research lead + game owner, Raunak validates behavior |
| Complete candidate roster | confidence, evidence, rule, semantic; prerequisite exclusions preserved, not dropped. No strategy budget pruning during collection. | Game owner + research lead |
| Live compatibility | Match recorded manifest/setup or obtain explicitly reviewed new calibration. Literal model/service/prompt/sampling config and corpus suitability still missing. | Tabmayee + Raunak |
| Input correspondence | Original calibration request/reference serialization required. Source candidate identities alone do not prove timing content identities. Rehearsal uses original candidate IDs and different source hashes. | Producing data/runtime owner via Tabmayee |
| Recorder | Prerequisite-aware factory, exception translation, durable starts/completions/checkpoints, resume and duplicate handling; synthetic crash checks. | Tabmayee; game owner for any separately reviewed offline collector fixes |
| Collection control | Explicit study authorization, timeout/rate/concurrency/call-spending limits, randomness/reset, immutable request digest. | Research lead + Tabmayee |

## Required for replay/payoffs/fitting after recording

| Setting | Defensible options; all remain unapproved | Owner |
|---|---|---|
| Team minima | Propose explicit selected=1, informative=1 to permit singleton strategies. Compare selected/informative=2 if redundancy is the scientific target; test feasibility separately. Positive influence and History reputation >0.5 are required by informative contributor semantics; a cold prior 0.5 cannot satisfy it. | Game owner / research lead |
| Execution/coverage | Propose v4 + task_output_contract_v2 + informative_history_influence_v1; v3/factual_output_contract_v1 is a distinct scoped alternative. Explicit minima require informative contributor semantics and resource binding. | Game owner |
| Aggregation | Evaluate reputation_weighted and dependency_group with explicit implementation versions/source hashes; no existing policy reused. | Game owner |
| Dependencies | Derive approved compromise pathways from authentic resources: shared embedding semantic/evidence and shared NLI evidence/confidence; inspect shared implementation/config before finalizing. Full-registry connected components retain bridges even when unselected. Unresolved candidates share shared_unknown. | Game owner with Raunak resource attestation |
| Reputation | Approved independently labelled History reports only; task-isolated priors/snapshots, no Development feedback. Choose Beta priors explicitly; absent authentic History records block fitting, not raw Development recording. | Game owner |
| Budget | No approved hard budget found. Options: preregister a latency grid near measured feasible subset sums, e.g. about 108 ms (Evidence alone), 179 ms (Evidence+Semantic), 15,105 ms (all four); or predeclare a service-level budget. These are illustrative settings, not new measurements. Respect task coverage and actual eligible roster. | Research lead / game owner |
| Cost penalty | Choose lambda=0 for validation-only objective with hard budget, or an approved lambda per ms with declared tradeoff (e.g. willingness to trade a loss amount for 1,000 ms). Do not import historical unitless lambda. Freeze before payoff optimization. | Research lead / game owner |
| Decision and loss | Approve threshold, FA/FR/uncertain penalties, clean Development finalized-coverage floor, weighting of groups versus examples and benchmark strata. Engine default 0.55 is not study approval. Equality at signed threshold stays uncertain; all achieved requirements and informative minima also gate public status. | Research lead / game owner |
| Failure/fallback | Propose all_selected_returned; uncertain when returned coverage/contributor requirements fail. No prefix early stop or replacement strategy. Numerical aggregation fallbacks are separate and must retain diagnostics. | Game owner |
| Attack game | report_corruption_v1, clean plus four actions per dependency group; choose suppression=unavailable or abstention explicitly, retain preservation behavior and audit. This is report corruption, not corpus poisoning. No attacks during raw collection. | Research lead / game owner |

Fitting-only budget, losses, reputation snapshot and fitted policy are not prerequisites for collecting raw complete-roster reports. Freeze the recording obligations first; do not fill unknown scientific values with historical defaults. Any changed reference/resource population invalidates implicit calibration portability and needs review before using those costs.
