# Empirical compound producer: implementation and blocked study

The owned producer is implemented and tested. **No new empirical compound policy
or development/test result was produced:** the existing compatible numeric corpus
has 38 entity groups, or 36 after excluding the previously explored Bahrain and
Belgium. The requested 16 history / 16 development / 16 reserved-test design needs
48. Preparation rejects this shortfall before assigning partitions or invoking a
verifier. The study was not silently reduced. New empirical attempts: **zero**.

## Evidence for the blocker

`artifacts/compound-empirical-v2/audit/source-manifest.json` validates each numeric
fact against the actual retained corpus and the independent source snapshots.
Population labels use the cached GeoNames population column; area labels use the
cached countries JSON area field, matching the original fact construction. Entity
names/ISO identities and exact decimal values must agree. Disagreements are
rejected, not repaired by changing a fact. Source hashes and copied independent
records are retained. This is snapshot truth, not a claim about current populations.
Empirical study construction and reload also reconstruct the manifest from the
actual raw files and verify their hashes; a modified embedded record with an
unchanged claimed file hash is rejected.

`audit/capacity.json` records all eligible entity IDs. `preparation/predeclared-intent.json`
records the requested bounds, four variants, candidate assignments, original loss,
threshold, dependency model and budget rule before any new outcomes. The original
intent remains intact. `preparation/blocked.json` records that no valid study or
partitions were created. The final producer additionally names its objective
`worst_validation_then_equal_plan_cost_v1`: primary worst-case validation loss,
with the secondary call-cost objective constant for the sole feasible call plan.

`other-local-corpus-inventory.json` checks other non-fixture local configurations.
The root/worktree numeric corpus copies contain the same 38 entities and do not
create additional independent groups. The older factual corpus has 60 capital
facts, not supported numeric facts; the small test corpus is not research data.
No compatible alternative with 48 supported numeric entities was identified.

The read-only local preflight succeeded, including existing model/index receipts.
Its full resource manifest ID is
`e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`,
matching the frozen atomic manifests. It reads local files and saved service
metadata; this does **not** attest a currently running service or a combined live
deployment. No models were loaded for research collection, no generation or paid
provider was called, and no corpus/index was modified or rebuilt.

## Completed producer

`app.game.offline.compound` supplies the following explicit stages:

1. `prepare`: validates a `SourceManifest`, requires 48 unique entities, excludes
   prior probe/smoke entities, commits deterministic entity ordering and assigns
   exactly 16 groups to each partition. Shared entity identities cannot appear in
   different partitions or be multiplied by adding measures/increments/templates.
   Identical actual component questions cannot cross splits under different entity
   names; an allocation with such leakage is rejected before inference.
2. `requests`: derives component inputs and independently labelled variants from
   the question and sealed source. The four whole-answer variants are correct,
   wrong arithmetic, wrong base with internally correct arithmetic, and both wrong.
   Whole correctness is the conjunction of the two required component labels.
   All variants of an entity remain together. Reserved requests require a freeze.
3. `collect_partition`: invokes the existing `collection.collect`, timing,
   resource-observation, completeness and failure machinery. The journal wrapper
   fsyncs starts/outcomes, retains all completed failures, and refuses ambiguous
   in-flight retries. Resume reuses completed outcomes without re-executing them.
   Current-session invocations are counted separately from retained attempts.
4. `Training`: validates exact regenerated request identities, source/study links,
   component bindings, roles, actual resource observations, returned payloads,
   completeness and timings. Reserved or diagnostic recordings cannot enter it.
5. `build_contract`: constructs component-specific history statistics only from
   supported history outcomes. The first directional observation per component
   and bound input is used, so repeated identical checks are not
   additional reputation evidence. Abstentions/failures do not update history.
   Every training call's timing is retained, including execution failures.
   Mean actual history/development attempt times estimate each planned call;
   test timings never enter these estimates. The predeclared budget is their sum.
6. `construct_payoffs`: replays actual development reports through the same pure
   `finalize_component` / `join_components` functions used by component execution.
   Existing report-corruption adapters target every affected verifier identity
   across all components consistently. These simulations are distinguished from
   real upstream failures. No atomic recordings or diagnostic reports are converted
   into empirical joint payoffs.
7. `fit`: uses the existing minimax solver and its numerical certificates, with
   the unchanged 90% finalized clean-development coverage constraint. The matrix
   contains primary validation loss. Resource-weighted loss is also reported using
   the original declared loss configuration. Both legitimate aggregation strategies
   have exactly the same call cost, so the secondary cost objective is constant.
   An unequal-cost extension is rejected rather than silently changing objectives.
   Infeasibility yields no policy and does not lower coverage or alter penalties.
8. `export_candidate` / `load_candidate`: revalidate source-bound training and exact
   payoff construction, verify the solver certificate and empirical provenance,
   export/reload policy/contract/matrix/context obligations, seal the development-best
   fixed baseline and all evaluation code, and check inventories. Synthetic inputs
   remain synthetic and cannot be relabelled as empirical by the exporter.
9. `evaluate_frozen`: accepts only the reserved recordings matching the frozen
   study/setup/candidate, without fitting or updating costs/reputation. It reports
   whole-answer and component metrics, wrong-base variant results, coverage,
   false acceptance/rejection, uncertainty, selective risk, decision/resource loss,
   simulated attacks and actual timings/failures. Entity-cluster bootstrap intervals
   use a fixed seed and 1,000 replicates, retaining the four related variants as a
   cluster. Sixteen known-source groups provide limited precision; a degenerate
   zero-error bootstrap is not proof of zero population risk.

The only authorized useful assignments are **Evidence for the fact and Rule for
the calculation**. Semantic does not supply either required check, and Confidence
generation is forbidden. There are two valid aggregations, one distinct team,
and no evaluated triple. Unregistered collector roster slots have no invocation,
timing or fabricated report; they preserve the existing exact resource-roster
validation. Only the actual planned calls are charged. Compound singleton
baselines are explicitly infeasible. No comparable component greedy executor is
invented. A successful fit here would not establish strategic advantage beyond
fixed Evidence+Rule, regardless of its policy probabilities.

## Separate V2 input and execution contract

`app.game.component_sources` defines a finite source-backed descriptor catalog and
`fact_plus_sum_binding_v2`. It accepts:

`What is the <area|population> of <catalog entity>, and what is that <same measure> plus <bounded plain decimal increment>[ square kilometres]? Give both values.`

Area requires the stated unit; population omits it. Entity/measure pairs must exist
in the explicit catalog. Names may contain bounded ASCII letters, spaces,
apostrophes and hyphens. Numbers use the existing bounded plain-decimal grammar,
without exponent notation. Answer JSON still requires exactly decimal-string
`base` and `derived` fields, rejecting duplicates, missing/extra fields, booleans,
nonfinite numbers and ambiguous prose. Source facts establish independent labels;
the parser/dispatch catalog contains descriptors, not correct values.

The factual answer is built from the submitted `base`; the arithmetic question
uses that same submitted value plus the question increment, with `derived` as its
answer. Exact Decimal arithmetic constructs study labels. No true base is inserted
into verifier inputs. An opt-in component analyzer types these validated checks,
including multiword entities, without changing the original task analyzer.

V2 binds catalog identity, assignment obligations and the full actual resource
manifest into the contract/policy IDs. Constituent planning contexts cover only
Evidence and Rule and carry only their measured costs. Their resource manifest
is an explicit projection of the full factory observation: every included entry
must exactly match that full manifest. Runtime still checks the full bound
observation before/after dispatch, including optional active-instance attestation.
Unused verifier costs are not guessed or assigned zero. The original caller's
selector is left intact; a scoped clone plans the assigned identities. A projected
manifest ID is a scope identity, not a claim of a separate measured live setup.

Existing V1 two-question parsing, contracts and historical identities remain
separate. New optional fields are omitted when absent. No default router, outer
prototype allowlist, API, DB, frontend, verifier algorithm, dependency assumptions,
threshold or frozen atomic policy was changed or activated.

## CLI and API-owner handoff

From `build/flexible-verifier-teams`, use the existing environment's Python:

```text
python -m scripts.compound_study audit --source <original>/build/multitask-policy42 --output <new-audit-dir>
python -m scripts.compound_study prepare --audit <new-audit-dir> --output <new-study-dir>
```

The second command currently refuses the 36-group pool. The following stages are
implemented for a separately authorized valid study, and were not run empirically:

```text
python -m scripts.compound_study collect --study <study-dir> --source <resource-dir> --role history --output <history-dir>
python -m scripts.compound_study collect --study <study-dir> --source <resource-dir> --role development --output <development-dir>
python -m scripts.compound_study fit --study <study-dir> --history <history-dir> --development <development-dir> --output <candidate-dir>
python -m scripts.compound_study collect --study <study-dir> --source <resource-dir> --role final_test --frozen <candidate-dir> --output <test-dir>
python -m scripts.compound_study evaluate --frozen <candidate-dir> --test <test-dir> --output <evaluation-dir>
```

Collection accepts `--resume-from <prior-dir>` and always writes a new directory.
The isolated collection bridge uses the resource-compatible original checkout and
the same owned collector/journal helper. Its network guard forbids all generation
and downloads; only bounded local service-metadata GETs are permitted. It does not
initialize an API route. Final collection checks the actual frozen candidate,
inventory and code hashes before loading models; an arbitrary freeze-ID string
does not authorize it.

To integrate a future validated policy, reload it with `load_candidate`, then pass
`(policy.contract.question_signature, policy.contract.budget, True, policy)` as an
explicit `QuestionPolicyConfiguration.component_entries` entry. Continue to use
`configuration_from_atomic_artifacts` for the frozen arithmetic/factual policies
and retain the prototype's existing outer allowlist. No empirical compound entry
is supplied in this handoff. Future dataset/design changes need separate approval;
this task did not expand the corpus to make the experiment possible.

`routing.json` records real frozen-policy sampling through the owned registration:
arithmetic selects Rule, factual selects Evidence. A supported V2 compound request
returns `missing_policy`; an unsupported operation returns `unsupported_category`.
A deliberately invalid offline resource observation returns
`provenance_incompatible`, without inference. This resource-negative fixture is
not a claim that the actual local files are incompatible. No real compound team
was routed because no new empirical policy exists.

## Verification and remaining work

`tests/test_compound_empirical.py` exercises a complete **synthetic software**
48-group preparation/collection/history/cost/payoff/fit/export/reload/reserved
evaluation/routing flow, including source tampering, split leakage, malformed
answers, decimal binding, wrong-base propagation, resource/report identities,
checkpoint recovery, coverage infeasibility and refusal to collect tests before
freezing. Its mock reports/timings/policies are not empirical evidence. Existing
component, task-routing, runtime, collector, flexible-minimum, coverage,
reliability and held-out-collection regressions were also run; exact commands and
results are in `checks.json`.

All prior artifacts, completed held-out results and original freezes are preserved.
No empirical development matrix, selected compound candidate or reserved evaluation
exists for this study. There is no demonstrated benefit beyond fixed Evidence+Rule.
The precise remaining blocker is a valid independently grouped source pool for
the required design under the no-expansion/no-rebuild restriction. The two old
atomic singleton policies remain the only empirical policies registered here.
