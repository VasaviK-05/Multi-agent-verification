# Compound and Reference fitting verification — 2026-11-05

## Scope and inspected source

Fresh clone of `https://github.com/VasaviK-05/Multi-agent-verification`, initial
branch `main`, commit `f86e606a5757a695042af98e484d546637e629b8`.
All fetched remote branches were inventoried. Relevant fitting history is merged
through `c7be148` (#30), resource reconciliation through `68e2871` (#31), native
acceptance through `19e0a9f` (#32), and server dispatch through `cd3a142`.
The existing work is substantially newer than the task's interruption context.

Phase A concluded both approved amended policies already exist, are fitted and
frozen, and need no collection or replacement policy export. Phase B therefore
verifies them and records handoff requirements on
`codex/verify-compound-reference-fitting-20261105`. No experiment, threshold,
coverage target, probability, resource pin or production setting is changed.

A candidate is a proposed configuration/result; a fitted policy has a feasible
certified distribution; a frozen artifact binds that policy to immutable inputs;
a deployed policy additionally requires actual server configuration and compatible
execution evidence. Neither a filename nor `deployable_policy:true` proves the
last condition. Package `deployment_active:false` is metadata, not a loader gate.

## A. Compound

The original 48-group design was separately amended to 36 groups, 12 per role.
Study ID: `86d17f7baa56a0a7c3a1ffcfb4b5914aba643fa59c99d17e64f1a7f1f00431f6`.
History and Development each contain 48 whole-answer examples (four variants per
entity), 48 Evidence and 48 Rule calls, or 192 completed training calls total.
There were no generation calls, retries, failures or raw abstentions. Entity and
related-component inputs are grouped across roles. Dataset identities are the
study ID with `-history` and `-development`; the joint final reservation is
`4db49d1117d211c7362465bace159319957085c9dc7a6f2e1ffe5f57d36e3311`.

Evidence checks the submitted base fact; Rule checks the submitted derived sum
against that submitted base. Both obligations must be satisfied for acceptance;
a qualified rejection rejects; insufficient coverage/influence remains uncertain.
The eligible complete joint plan is E+R with either reputation-weighted
`log_odds_v1` or dependency-group `groups_v1` aggregation. This yields **2 rows**,
not 30 arbitrary subsets: the frozen component assignments require Evidence on
`base_fact` and Rule on `derived_sum`. Adding other teams would change the study.
Generic flexible enumeration still permits eligible teams of sizes 1–4.

Frozen History uses Beta(1,1), deduplicated directional component inputs:
Evidence 24 successes/0 failures -> Beta(25,1), mean 25/26; Rule 48/0 ->
Beta(49,1), mean 49/50. The irrelevant candidate in each component remains cold
Beta(1,1). All snapshots are bound in the component contract.

Estimated costs are Evidence 84.0705614464 ms and Rule 0.1225281352 ms;
budget 84.1930895816 ms. Minimum selected/informative rules are one per atomic
obligation, with the whole answer requiring both checks. No forced probability
floor exists. Loss is false accept=1, false reject=1, uncertain=.2. Historical
resource weight is 4.704037204857504e-6 per ms, reported separately; equal joint
plan costs make the primary minimax objective validation loss.

The original 90% fit is correctly infeasible: maximum clean coverage is 43/48,
89.583333%. Its matrix ID is
`4d7126a8d652a35045b2682e222e0fd767fef43a5b8b6d9d9e4f5cc074fe90c9`.
`fit_compound_85.py` records the previously authorized **post-development 85%**
amendment; it does not improve the recordings or alter payoffs.

Existing immutable artifact: `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`.

| Identity | Value |
|---|---|
| Policy | `0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532` |
| Freeze | `d327793b940b356a0e8cd418c9a6a7ae3d93c3f6a21035a0f36b0e29910ad0c0` |
| Matrix | `bd4918e38503ec6ab990c83d687c1bc648015823a5ca2fa9ad18473421ab9970` |
| Contract | `0b93b2782afbf1da65be0064dd7a0218f6e347abda1568f2da3d15daa1fbf3e6` |
| Original resources | `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb` |

Both rows of the **2×5** validation matrix, in clean/support/rejection/inflation/
suppression order, are `[.0208333333333, .75, .25, .0166666666667, .2]`.
The optimizer selected reputation-weighted E+R with probability 1; the
dependency-group alternative has probability 0. Selected strategy ID:
`9db6a209ad0c8f088765bf41f6f4d81b1d14fea51c615c71f3160960349899c6`.
Game value .75; worst action forced support. The 48 clean Development outcomes
contain 12 correct accepts, 31 correct rejects, five uncertainties and zero
incorrect decisions. Clean validation loss is **(5/48) × 0.2 = 0.0208333**;
clean coverage is 43/48; coverage slack .0458333333. Solver is optimal at 1e-8,
normalization residual and primal-dual gap zero. The matching fixed plan ties.

No remaining fitting work exists. Portable cell reconstruction uses the sealed
480 finalized Development outcomes and verifies their content ID/inventory.
Full raw-record fitting cannot be repeated verbatim from this public clone:
`preparation/study.json` and canonical `candidate/freeze.json` are intentionally
unpublished. Obtain exact canonical inputs from the custodian if a whole-freeze
rerun is required; public redactions must not masquerade as canonical inputs.

Runtime evidence: the reviewed scoped E/R transfer preserves policy bytes and
binds only required E/R resources (scope ID
`310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`).
Retained reserved results are 45/48 decisions, zero observed errors and three
uncertainties. Later historical native acceptance includes correct/wrong-math
requests and four native component calls. That is local direct execution, not
proof of the current teammate API or this machine's deployment.
Retained reserved timers average 155.146433333 ms Evidence and .176025000 ms
Rule (48 calls each). They do not recalibrate the frozen 84.193089582 ms budget.

## B. Reference

The oldest `reference` campaign was interrupted. A separately approved
`reference-current-v1` transition preserved 45 resource-equivalent non-Confidence
reports; 14 old Confidence records remain historical only. The replacement
record and interrupted unknown duration are explicitly accounted for. The latest
intended fit is `fit_reference_50.py`, not the older study/current scripts.

There are 30 grouped frames, ten each History/Development/Final-test, with two
answers per frame. Complete training contains 40 examples × four candidates =
160 executed calls: 65 directional and 95 abstentions. Dataset IDs are
`reference-fresh-v1-history`, `reference-fresh-v1-development`, and the reservation
`reference-fresh-v1-final_test`. Frozen training contains no final outcome payload.

History Beta priors are (1,1): Semantic 10 successes/10 failures -> (11,11),
mean .5; Confidence 12/1 -> (13,2), mean .8666667; Evidence and Rule have no
directional History observations and remain (1,1). Semantic requires legitimate
reference context; its neutral History makes its singleton uninformative and
uncertain. A selected name is not necessarily an informative contributor.

Both existing aggregations and eligible subsets of size 1–4 remain enabled.
Semantic comparison coverage requires Semantic in this frame; **8 subsets × 2
aggregations = 16 strategies**, including singleton, pair, triple and four-name
teams. Minimum selected=1 and minimum informative=1. No multi-verifier quota or
nonzero probability quota was introduced.

Measured training means (ms): Semantic 102.071357498, Evidence 63.826667508,
Rule .149432491, Confidence 16428.737125; budget 16594.784582497. Same 1/1/.2
decision losses; resource weight .1/budget. The reliability-first objective
minimizes worst validation loss, then expected attempt cost, epsilon 1e-8.
The stored cost-augmented matrix and its separate validation-values matrix must
not be confused when reporting the game value.

The original 90% requirement remains infeasible (maximum 60%). The approved
`reference_post_development_50_v1` changes only the floor to 50%, explicitly
chosen after observing Development. Old and amended training manifest, contract,
Development evaluation and payoff values are equal. The inherited
`summary.json:no_target_relaxation` flag is clarified by `fit-report-note.json`;
it must not be reported as an unchanged original floor.

Existing artifact: `artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json`.

| Identity | Value |
|---|---|
| Policy | `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda` |
| Artifact | `ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f` |
| Freeze | `94e3a7dcbe2b6ccb3d0155018f04419a9513abce8f3752aaeb32f1c38d2d4596` |
| Matrix | `90c7f9564573f410b648c7f3b09a23c59a2998da6df0d0f194f4fbab50fb5a13` |
| Resources | `7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb` |

The **16×5** game selects Semantic alone with probability 1/6 (strategy
`6b9707499750396bba9cc51f9681dee9ef6b0c3a9958e67d3c0f84f66ad9877e`),
and Semantic+Confidence with probability 5/6 (strategy
`9b8f912c18417466a3f39b8fcbfd1ead99adf476bb9acf08d076bd2cebe38955`),
both reputation-weighted. Other probabilities are zero. Optimal game value is
.391666666667, worst action forced rejection; clean loss .1, coverage .5,
expected attempt cost 13792.685628331 ms. Validation primal-dual gap is zero,
normalization residual zero, secondary cost gap 3.63798e-12; tolerance 1e-8.
The fixed pair has Development coverage .6, clean loss .08 and worst loss .43.
The mixture trades clean coverage for the modeled worst-case objective.

Reference fitting is complete and existing compatible recordings suffice for
offline Development reconstruction without Ollama. The original fit script
also needs unpublished canonical `seal.json`/`fit/freeze.json` for exact seal/
whole-source replay; do not overwrite the existing `fit` directory. Our check
replays the published training bundle and verifies the existing matrix/context.

Historical reserved evaluation is already complete, not remaining collection:
20 answers/10 groups, 80 calls and 100 generations. Cumulative campaign totals
include 255 starts, 254 completed calls and 372 generation starts. Published
expected clean coverage/loss are 66.67%/.066667 for the policy and 80%/.04 for
both fixed/greedy baselines. These are retained results only; no held-out
payload is read by the new verification script and none enters fitting.
Retained reserved means are 17903.410910 ms Confidence, 60.484205 ms Semantic,
54.540150 ms Evidence and .139675 ms Rule (20 calls each). These exclude model
initialization and resource attestation; they are not end-to-end latency or prices.

Reference live evidence is construction/service/binding with zero fresh calls.
Its historical recorded collection and replay are not evidence of current API
activation. New native execution requires passing environment checks and a
separate explicit call/generation authorization.

## C. Resource compatibility

The frozen Reference service is Ollama **0.40.14**, `llama3.2:3b`, digest
`sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`.
A target reporting 0.40.11 is rejected by `reference_intermediate`; this is a
live compatibility block, not a minimax failure. Current repository observations
record a matching 0.40.14 historical installation; they do not attest this Mac's
current service. No service probe or generation was performed here.

The Reference historical Evidence index ID is
`e802300251695e22ff0de258b39da818488722df347e04af20507e240442489b`;
the recorded logical serialization ID is
`1120818b811644ee5fc343d63498355dd0beb49776e0fd8f5dbc484e4a922e7d`.
`ReferenceObserver` accepts this exact serialization difference only after
physical index+receipt and every other required resource match, or a reviewed
relocation proof validates unchanged resources. This is not a fingerprint bypass.
`inspect_required` still rejects physical index/receipt changes and unproved
relocation. Both embedding and NLI model directories, corpus, index, receipt,
implementation/source capsule, semantic settings and actual instances are pinned.

The checked-in `adapter.json` names the original Windows model caches and ignored
`build/multitask-policy42` resources. Those are not a usable live-resource setup
in this fresh Mac clone. Temporary Python test dependencies differ from the
recorded collection environment; they enable offline software checks only.
No models, Ollama installation, index, receipt or scientific resource was changed.
These environment differences block live acceptance here, not the existing fit.
Compound scoped E/R execution has no Ollama dependency.

## D. Runtime path and handoff

`ValidationService` now handles `EXECUTION_MODE=game` and constructs the explicit
`FlexiblePolicyGameRuntime`; this supersedes the old handoff's missing-wiring
claim. `create_game_runtime` accepts one configured deployment source. Flexible
mode accepts only the reviewed `reconciliation/policies.json` path; `load_bundle`
checks exact bytes, then builds the frozen provider and explicit router registry.
No implicit filesystem discovery selects arbitrary policies.

Classification uses the question, requirements, domain/difficulty and reference
presence; Compound uses its declared catalog/template and Reference its bounded
paraphrase frames. Allowlist, signature and budget must resolve uniquely. The
dispatcher constructs route-specific native instances/observer (scoped E/R for
Compound, full reviewed Reference factory), calls `snapshot_for(actual_selector)`
before router dispatch, and fails closed on compatibility errors. Generic
`domain_routing.py` sparse/pool selection is not the category selector for these
two registrations.

The frozen policy is validated against context/contract, feasible strategy axis,
reputation and resource identity. A server-owned RNG samples cumulative fitted
probabilities. Only selected team calls execute; complete-team game mode disables
early termination. Aggregation dispatch honors reputation/dependency versions;
coverage, informative contributors, failures and post-call resource checks can
leave uncertainty. Compound aggregates each required obligation and then joins
their decisions, rather than flattening all reports into another baseline vote.

Audits preserve policy/artifact/strategy, bundle, validation, context/resource and
reputation identities, selected team, aggregation, attempts, component/binding
IDs, coverage/reasons and final status. `_validate_game` retains component reports
from `summary.attempts` without reaggregation. Existing server-boundary tests use
synthetic factories/reports: useful wiring evidence, not live activation proof.

Integration owner must:

1. Capture the actual running checkout/configuration/resource identities. Use
   `scripts/capture_reconciliation_target.py` with the actual target and adapter;
   inspect metadata without generating, and compare every required pin.
2. Configure `EXECUTION_MODE=game`, `GAME_FLEXIBLE_POLICY_PACKAGE_PATH` to the
   absolute reviewed package, `GAME_FLEXIBLE_ADAPTER_CONFIG_PATH` to the target's
   exact adapter, and leave the legacy bundle/artifact settings empty. Supply
   separate approved Compound/Reference relocation-binding settings if needed;
   the runtime deliberately ignores a generic inherited relocation binding.
3. Restore already approved exact resources or seek authorization for any external
   change; never copy a saved manifest to stand in for observed resources. A
   mismatching Ollama version requires owner action and approval, not solver work.
4. Obtain a separately bounded native execution authorization, then validate the
   actual same-process server selector/observer, both Reference branches, Compound
   structured-answer binding, incompatible-resource rejection, and real API audit
   persistence/frontend uncertainty display. The old eight-call acceptance budget
   is consumed and is not authorization to repeat it.

Compound answer is a string containing exactly decimal-string `base`/`derived`
JSON fields. Reference requires the legitimate source text as `context`. Input
formatting, API/DB/frontend and target deployment changes remain owner work.
No production configuration, API, DB, verifier, retrieval or orchestration code
was edited during this verification.

## E. Reproduction and acceptance

Run from the repository root using an environment with repository dependencies:

```sh
python -m scripts.verify_compound_reference_fits --output build/fresh-fit-audit.json
python -m scripts.verify_framework_delivery
python -m scripts.verify_reconciliation_package
python -m scripts.replay_remaining_policies --output build/fresh-category-replay
python -m pytest tests/test_reference_50.py tests/test_reference_transition.py tests/test_reference_transition_portable.py tests/test_compound_empirical.py tests/test_game_clean_coverage.py tests/test_reconciliation_execution.py tests/test_flexible_runtime_dispatch.py tests/test_singleton_compatibility.py -k 'not test_nonconfidence_transfer_preserves_authentic_report_timing_and_observation' -q
```

Acceptance: existing policy IDs/certificates validate; probabilities normalize;
Reference Development replay/matrix/context reproduce; Compound finalized cells
and coverage reproduce; all frozen artifact bytes remain unchanged; eligible
strategy sizes/aggregations remain intact; incompatible resources reject; no new
native verifier calls or generations; no Final-test payload enters fitting.
Exact canonical whole-freeze reproduction remains conditional on custodian files.
Live deployment success additionally requires separately authorized compatible
execution in the target server, which this report does not claim.

Both games use five actions: clean, forced support, forced rejection, confidence
inflation and suppression. Shared embedding/NLI and unresolved shared-unknown
dependencies prevent claims of independent corroboration. Small, bounded cohorts,
post-development floor selection and simulated report attacks limit external
validity. No universal accuracy, safety, superiority, deployment latency savings
or population guarantee follows from these studies.

Fresh run outcomes and limitations are recorded in the accompanying
`compound_reference_verification_20261105.json` and test result note below.

The first unadapted focused run produced 69 passes and two portability failures.
The publication-pinned transfer test resolves historical Windows separators
literally on POSIX. It remains byte-identical; a new portable wrapper executes
every original assertion with separator-normalized lookup and unchanged hashes.
The original entry is deselected in the command above because the wrapper
replaces it, not because transfer assertions are waived. The serialization test
now explicitly creates distinct physical/logical JSON bytes in its temporary
fixture instead of depending on Windows newline conversion. The affected
portable tests passed (15 tests, one original entry deselected).

Both existing delivery/package audits pass after these test changes. The
historical delivery audit verifies 484/487 original publication files unchanged
and the three already reviewed source overlays; all frozen artifact bytes and
resource pins match. It does not attest the newly added server integration files
as a historical native observation. Fresh category replay passed seven retained
cases and rejected its incompatible-resource fixture. The new fitting audit ran
twice with byte-identical output (SHA-256
`2a6625b1eb24a4980f474ff02192c9d1e8ab64e27b4b8216b020842d09c27f58`).
It validates existing certificates without solving/exporting another policy.

Final focused suite: **71 passed, one original Windows-specific entry deselected**,
196.68 seconds; its portable wrapper executes all original assertions.
`git diff --check` and Python compilation passed. No new policy was exported,
no inference or service requests were made, and nothing was merged or deployed.

Publication recheck of the existing verification commit: the clean-loss
explanation above was corrected from the recorded counts and frozen 1/1/.2
penalties; the numerical policy/matrix values were already correct. The audit
now emits those counts and recomputes decision loss from statuses and labels,
checking each recorded penalty. A focused recorded-outcome regression was added.
The machine-readable evidence includes these metrics and a separate
`publication_recheck` entry, preserving the initial run results above.

The publication recheck passed 19 focused tests (10.31 seconds), the recorded-fit
verification, and both delivery/package identity audits. The unchanged portable
wrapper calls the original transfer-test function with only separator-normalized
path lookup; every original assertion runs. The broader 71-test suite above was
not repeated because no fitting, runtime or production behavior changed. The
handoff now points to this delivery branch and recognizes the already implemented
`FlexiblePolicyGameRuntime`/`ValidationService` wiring. Remaining integration work
is target configuration, same-instance/resource attestation and separately
authorized API/DB-owner acceptance, not rebuilding the dispatcher. No remaining
documentation/testing work is identified for this completed framework scope.
