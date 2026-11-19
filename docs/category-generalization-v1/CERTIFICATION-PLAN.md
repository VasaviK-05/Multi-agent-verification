> **19 November 2026 update:** [engineering review v3](ENGINEERING-ACCEPTANCE-v3.md)
> supersedes prior implementation/testing blockers and the mandatory-new-fit
> interpretation. Compatible unseen instances now reuse the unchanged fitted
> policy through an opt-in scope; exact routes retain precedence. Confidence has
> a new game-only v5 consistency output contract. No new empirical certification,
> fitting or deployment occurred. Original findings below remain historical.

# Category policy study v2 — proposal, not execution authorization

All counts below are proposed ceilings for a **new** study, not actual observations
or approved calls. Existing Final Test datasets, source identities and published
results are not consumed or changed. Runnable manifests, source/resource locks,
independent labels/custody and approved numerical budgets remain to be supplied.

## Input, answer, applicability and dependency contracts

| Family | Supported input and candidate-answer contract | Eligibility/dependencies | Existing policy sufficient? |
|---|---|---|---|
| Rule arithmetic | Full matches of existing symbolic binary +, -, *, / and supported word arithmetic patterns; Decimal numeric candidate, including malformed/wrong answers; division uses existing answer-precision rule | Arithmetic obligation; actual Rule parser and original source/Decimal semantics. Division by zero is uncertainty/unsupported, not correct arithmetic. More complex expressions, comparisons and structural checks are excluded from this first output-coverage contract | No. New contract-bound task identity, independently labeled operand/operator families and new scoped artifact required |
| Evidence facts | Bounded factual QA grammar and entities/relations supported by the **configured** frozen corpus/index; short factual/numeric candidate, wrong and unsupported candidates retained for evaluation | direct_fact obligation; exact corpus/chunks/index receipt, embedding/NLI snapshots, retrieval parameters, evidence/claim-quality guards. Non-covered queries must abstain. Corpus presence alone does not certify answer evidence | No. Historical factual artifact does not certify unseen distribution. New fit/evaluation under pinned corpus needed |
| Semantic comparison | Single-frame `Paraphrase this reference: ...`; supplied reference must equal source, candidate paraphrase or contradiction | semantic_comparison obligation; non-label external reference, frozen embedding model/comparison mode/thresholds; reputation, informative contributors and dependency grouping. Supports measured reference resemblance; no guarantee of factual equivalence | No. Frozen bounded-reference frame artifacts are not broadened. New independent frame/entity/relationship groups and scoped fit needed |
| Confidence participation | Existing eligible question/candidate pairs in the above families; native provider path, no injected context judgments | Must be feasible and receive genuine positive minimax mass in a compatible policy; unchanged sampler/model/prompt/seeds/temperature/n_samples/timeouts, service identity and shared NLI dependencies. Agreement is not independent factual evidence | No. New combination artifacts/evaluation required; selection cannot be guaranteed if the empirical minimax solution excludes Confidence |
| Standalone Confidence consistency | Bounded consistency question/answer distribution, with external ground-truth labels; candidate strings handled by unchanged native agreement labeler | **Blocked technically**: current finalizer cannot achieve consistency coverage. A separately versioned game-owned report/coverage execution adapter must recognize valid native judgment provenance without claiming factual truth or changing verifier algorithms | No. Requires reviewed coverage-contract implementation AND fresh policy fitting/evaluation |
| Multi-verifier atomic categories | Same question/answer contracts; union of certified obligations, compatible resources/references | Enumerate feasible subsets x both aggregations, with frozen dependencies/reputation/budgets/minima. Complete selected team executes, no fallback/early stop; missing evidence/contributors still uncertain | No. Each new exact category/profile/budget context requires its own compatible matrix/artifact; strategies within one context are evaluated together, not separately fitted by hardcoded team |
| Fact-plus-calculation components | Existing source-backed descriptors and `{base, derived}` answer binding only | Existing ComponentPolicy, catalog and source manifests; arithmetic question is produced by existing component binder. New entities/sources need their own category/component certification | Existing exact routes retained only. A general component-source scope is not implemented by flattening it into atomic categories |

Scope must identify operator/numeric ranges, language, grammar, candidate length,
corpus-supported relations, reference frames and model-specific limits BEFORE
seeing held-out outcomes. A broad regex or free-text name cannot establish those
scientific boundaries. Changes in scope produce a different input-contract hash.
Malformed/wrong answers must not be filtered into favorable test subsets.

## Precisely required artifact profiles

For a minimal one-domain/one-fixed-difficulty/one-budget-per-profile study:

| Input family | Reference profiles | Participant/informative profiles | New artifacts |
|---|---|---|---:|
| Arithmetic | absent, valid external | (1,1), (2,2) | 4 |
| Factual | absent, valid external | (1,1), (2,2) | 4 |
| Semantic | valid external only | (1,1), (2,2) | 2 |
| Standalone consistency | absent, valid external | (1,1), (2,2) | 4, blocked pending achieved-output contract |

Target: **14 new profiles/artifacts**, ten using currently recognized achieved
obligations and four technically blocked. These are proposed profiles, not an
assertion all are feasible or statistically certifiable. Profile (2,2) is a
separate multi-participant study, not a requirement added to old policies. If no
team has two informative contributors, record infeasible; do not lower the guard.
Confidence participation in arithmetic/factual/reference profiles is evaluated
inside those policies; it does not require an extra hardcoded Confidence policy.

Each artifact package needs the new input-contract JSON; separate history and
calibration identity; empirical per-attempt recordings; all feasible team x
aggregation matrix rows; original minimax formulation and full solution; frozen
reputation/dependency snapshot; exact budget/cost units; complete execution and
resource contracts; development and untouched test reports; baseline report;
reviewed applicability declaration and report bytes; reproducible custody/source
manifest. Reports bind input_contract_id, artifact_id, dataset_id, exact strategy
IDs and role as required by the new runtime. Include uncertainty and limitations.

Every additional domain, grammar/profile, budget, candidate resource set,
reference condition or contributor contract that changes compatibility requires
its own artifact. Thus 14 is a bounded target, not a universal total. A genuinely
mixed fact-plus-calculation category additionally requires a separately reviewed
ComponentPolicy/certification package; that package is outside this atomic count.
Multiple overlapping budget profiles are not installed simultaneously by the
initial category dispatcher; select one reviewed deployment configuration.

Historical artifacts are retained as baselines/exact-route policies only. New
contract hashes deliberately prevent substituting their old task bindings. There
is no current evidence justifying reuse for newly certified distributions.

## Dataset design and real-attempt accounting

Per target profile, reserve **80 history + 120 development + 200 untouched test
cases = 400 cases**, grouped by question/semantic family so sibling answers,
paraphrases, inverse arithmetic forms and shared evidence sources cannot cross
splits. Each case has one candidate answer. Operator/entity/relationship/reference
families, exposure audits, correctness/uncertainty labels and source support need
independent review. Historical questions/previously exposed Final Test groups are
excluded from new untouched test selection.

Proposed strata per profile:

| Split | Correct candidate | Incorrect candidate | Ambiguous/uncertain | Unsupported | Resource unavailable | Total |
|---|---:|---:|---:|---:|---:|---:|
| History | 32 | 32 | 8 | 4 | 4 | 80 |
| Development | 48 | 48 | 12 | 6 | 6 | 120 |
| Untouched test | 80 | 80 | 20 | 10 | 10 | 200 |

Resource failures, missing evidence/reference, timeouts and insufficient
contributors must be separately tagged; do not manufacture reports for absent
resources. Additional diagnostic cases may be necessary; they require revising
the cap and plan BEFORE execution. Semantic contradictions distribute changed
numbers, negation, entities and relationships across incorrect cases with novel
held-out families. No native semantic contradiction results currently exist.

Measure each eligible verifier ONCE per case through the existing recording
contracts. Replay complete team outcomes and aggregations offline to fit matrices
and compare strategies; do not repeat native calls for every subset/baseline.
This reuse must be disclosed as paired offline evaluation, not independent runs.
Resource-unavailable/ineligible attempts reduce actual calls, never become fake
native outcomes. Do not retry started/ambiguous attempts automatically.

After artifact freeze and independent evaluation, propose **10 additional unseen
live-game demonstrations per profile**, spanning both outcomes, uncertainty and
safeguards. They are separate from fitting; selected teams follow genuine policy
probabilities. Ten does not guarantee a rare mixed-strategy action is sampled:
if demonstration of all claimed positive-mass teams needs more calls, propose a
separate bounded extension. Do not change the mixture or search seeds using test
labels to force a desired team. All realized positive-mass teams must execute
completely; no requirement that every theoretical subset be selected.

At most four eligible native verifiers with a reference, three without (Semantic
is unavailable). Proposed n_samples=5 is the existing adapter value; verify the
actual future resource contract before authorizing any count:

| Stage | Cases/requests | Max real verifier attempts | Max Ollama generations |
|---|---:|---:|---:|
| Initial development-only pilot (not held-out, not certification) | 40 reference-backed cases | 160 | 200 |
| Ten currently achievable profiles: history/dev/test | 4,000 | 14,400 | 20,000 |
| Ten-profile live-game demonstration ceiling | 100 | 360 | 500 |
| All fourteen target profiles: history/dev/test | 5,600 | 20,000 | 28,000 |
| Fourteen-profile live-game demonstration ceiling | 140 | 500 | 700 |
| All fourteen profiles plus demonstrations | 5,740 | **20,500** | **28,700** |

Ten profiles comprise six reference-present and four reference-absent profiles:
400*(6*4+4*3)=14,400. Fourteen comprise eight present and six absent:
400*(8*4+6*3)=20,000. Demo counts substitute 10 for 400. Confidence generations
are 5 per case if selected/collected, at most 14*410*5=28,700. These are bounded
maximums, NOT actual call counts, and do not include the initial pilot twice:
pilot data may only enter Development if the preregistered exposure/split plan
explicitly permits it; otherwise keep it separate and add its 160/200 caps.
Standalone consistency profiles cannot be run under the current finalizer.
The exact runnable manifest must replace ceilings with explicit per-case attempts.

## Costs and execution limits

Existing published all-candidate cost estimates are in **milliseconds**, not
money: arithmetic 21,258.335; factual 15,965.046; reference 16,594.785 ms/case.
They are historical estimates on different resources/distributions, not a new
calibration certificate. Using the largest as an illustrative upper *point
estimate* gives about 14.2 minutes for the 40-case pilot and 33.9 hours for 5,740
full-study cases. These are not worst-case bounds and exclude setup/evaluation.

Proposed separate pilot cap: 40 cases, 160 attempts, 200 generations, **2 hours
wall-clock**, no retries. Proposed eventual full-study cap: the manifest counts
above and **72 hours wall-clock**, no retries. An external supervisor may stop the
campaign at its wall-clock ceiling; it must not finalize an incomplete selected
team as a normal decision. Resumption follows durable attempt custody; an
ambiguous start is not repeated. No new per-team early termination is introduced.

The existing sampler timeout is 60 seconds PER generation, so 5 samples can take
300 seconds. 28,700 generations could consume 478.3 hours in timeout bounds alone;
a 72-hour campaign ceiling may abort well before completion. Evidence/Semantic
native inference lacks a proven per-call wall bound here. No hard token limit is
configured by the sampler; adding one would change its contract and is excluded.
Actual CPU/RAM/energy/token/cost forecasts need the approved resource lock and a
pilot. Expected external API spend is zero only for the proposed local-only
adapter, but hardware/electricity costs are unknown. No dollar budget or successful
completion guarantee is fabricated. Record measured wall/process time, samples,
tokens when available, failed-attempt costs and initialization separately. Reject
resource drift; do not reuse old calibration on changed models/hosts silently.

## Metrics and proposed acceptance gates

Preregister definitions, group-level confidence intervals and thresholds before
new held-out labels are accessed. The following are proposals requiring scientific
review, not silently installed policy/threshold changes:

* Confusion counts: correct accept, correct reject, false accept (incorrect
  candidate accepted), false reject (correct candidate rejected), uncertain.
  Report conditional rates AND all-case denominators, per category/profile/team,
  correctness stratum and failure mode. Abstention cannot be counted as rejection.
* Supported correct/incorrect coverage: fraction with all required achieved
  obligations and enough informative contributors; report expected selection
  coverage separately from achieved/public-decision coverage. Proposed minimum
  achieved supported coverage 90%; preserve explicit uncertainty on unsupported,
  missing evidence/reference, failed resources and insufficient contributors.
* Proposed false-accept one-sided 95% upper bound <=5% per profile; false-reject
  and correct-accept/reject rates plus intervals must also be reported. With 80
  incorrect cases and zero false accepts, the binomial upper bound is about 3.68%,
  but grouping and subgroup analysis can reduce effective sample size. Do not
  infer certification from this nominal sample count; increase independently
  held-out groups if the predeclared inference plan requires it.
* Decision loss: the existing declared loss configuration (including uncertainty
  cost), clean and attack-conditioned losses, worst-case empirical loss and
  confidence intervals. Freeze loss/attack identities before testing.
* Costs: measured per-attempt and per-team sums, cost per directional/correct
  decision, generation counts, p50/p95 elapsed times, timeout/failure/abstention
  costs, estimate errors and selected-budget violations (must be zero).
* Compare minimax against development-selected best feasible pure team/aggregation,
  best feasible single verifier, uniform feasible mixture, existing heuristic
  strategy and always-uncertain baseline. Equal cost/resource/minimum/coverage
  rules apply; infeasible baselines are reported, not repaired. Use paired
  recordings and group-respecting uncertainty estimates, not cherry-picked best
  held-out strategy. Strong baseline outcomes can invalidate certification.
* No routing/identity/probability/resource/expected-behavior regression for any of
  the 69 existing exact questions. No unsupported scope promoted because routing
  happened to succeed. Semantic contradiction false acceptance is a substantive
  limitation even when routing is correct. Never tune existing thresholds to pass.

## Exact next actions and blockers

1. Authorize/provide an isolated functional test environment; run all prepared
   boundary, policy-package, routing, guard and planning regressions. Dynamic
   backward-compatibility capture must pass before release. Current pytest count
   is zero; no release gate is satisfied by syntax checks alone.
2. Review the new engine/adapter and fill integration tests with real immutable
   artifact fixtures and instance-bound observers. Test mismatched artifact/task,
   reports/resources, budget, candidate/reference changes, failures and frozen
   probabilities without native inference. New runtime is not deployed.
3. Agree whether Confidence acceptance means informative participation or also
   standalone consistency. For standalone, implement/review a new game-owned
   achieved-output/execution version; keep all historical finalization semantics.
   This is a technical blocker, not a reason to loosen a coverage guard.
4. Produce the enumerated supported scopes, history/dev/held-out reservations,
   source custody, label adjudication, local resource lock, cost model and exact
   per-verifier call plan. Approve feasibility/minima and evaluation thresholds.
5. Obtain separate approval for the bounded pilot only. No inference is currently
   authorized. Use pilot outcomes to finalize an independently approved fitting
   and untouched-evaluation campaign; no production/published artifact edits.
6. Fit NEW compatible empirical profiles, freeze matrices/mixtures/resources,
   evaluate untouched groups and strong baselines, issue actual reviewed reports
   and applicability packages only for passing distributions. Explicitly label
   infeasible/failed/uncertified profiles.
7. Separately approve live-game unseen-question demonstrations, then separately
   review deployment activation. No merge to main is performed by this work.
