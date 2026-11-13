# Prospective Experiment 1 — game-side implementation

This is a separate versioned prospective study interface. It reuses the existing game, frozen comparison and metric/statistical implementations. It does not complete or authorize the historical experiment, alter its four policies, reinterpret its freezes, or change audit PR #37. The unrelated `app/game/research/prospective.py` frozen-rule Development-transfer workflow is not modified or relabelled as Final Test support.

## Research protocol

Question: **Does joint verifier-team and aggregation selection provide a useful tradeoff between validation loss, decision coverage and computational cost under declared resource limits and report-corruption attacks?** No superiority, non-degenerate mixture or minimum performance is assumed. Pure solutions, baseline ties and infeasibility are valid findings.

Primary outcome is worst-case expected **decision-only validation loss**, maximizing across the declared complete attack set after averaging examples and integrating exact policy probabilities. Supporting outcomes are clean validation loss; correct acceptance/rejection; false acceptance/rejection; uncertainty; decision coverage; selective risk; unresolved obligations; estimated attempt cost; and cost-inclusive total loss.

Prescribed constants: false-accept loss 1, false-reject loss 1, uncertain loss 0.2, decision threshold 0.55. These are protocol literals, not producer-supplied alternatives.

The template deliberately leaves unapproved selected/informative minima, Development floor, budget, per-candidate costs, resource coefficient/units, History priors, failure semantics, optimizer tolerances, objective, dependency registry, suppression mode, statistics seed/repetitions, population sizes and exact source/resource identities unresolved. **Do not copy historical numerical settings or merely change approval flags.** Statistical confidence is 95%; seed/repetitions are explicitly required when the design is approved. Sample sizes are derived from an externally approved exact group roster, not selected by this implementation.

Development coverage constrains policy/baseline preparation. Held-out coverage is an observed result, never guaranteed, used to tune the floor, or used to repair a noncompliant method.

Attack family is the existing `report_corruption_v1`: clean, forced support, forced rejection, confidence inflation and suppression. Suppression must explicitly choose unavailable or abstention. Attack actions use full connected shared-failure groups and conservative shared unknowns. They are not an upstream evidence-poisoning or actual model-compromise claim. All raw reports, failures, prerequisites and achieved-coverage guards retain their existing interpretation.

## Files and interfaces

New package: `app/game/research/experiment1/prospective/`:

- `models.py`: strict protocol, outcome-free populations, exclusions, provenance/evidence, external approval/release records and caller-digest-authenticated document loader.
- `readiness.py`: independent per-cohort five-stage readiness, with expected artifacts, responsible owners and exact compatibility checks. No fitting, replay, verifier, model/service/database use or Final Test loader.
- `reporting.py`: explicit Development and separately authorized Final reporting adapters. Reuses `AtomicEntry`, `validate_frozen`, `atomic_cube`, `point_report`, `paired_point_differences` and `bootstrap_report`. No policy selection, fitting or sampling.
- `__main__.py`: **schema/readiness only**. There is no CLI scoring, fitting, collection or release command.

The historical `ExperimentManifest`, runner, comparison functions, metrics, uncertainty implementation and original CLI are byte-for-byte unchanged. The historical ambiguity remains explicitly mapped in prospective outputs: legacy `mean_loss` / legacy `worst_case_expected_loss` include resource cost and correspond to new `total_loss` / `worst_case_total_loss`. New `worst_case_expected_loss` is decision-only. Never join these fields by their equal names.

## Evidence and authority boundary

`load_authenticated(path, expected_sha256)` reads only the explicitly designated Manifest/Authorizations document. The expected digest must come from a trusted review channel, not be trusted because an unreviewed file supplies its own hash. Duplicate JSON keys, nonfinite numbers, foreign/historical envelope versions and known reserved-payload paths/schemas are rejected. Artifact/evidence strings are locators only and are never followed. No arbitrary archive discovery or generator runs occur.

`Evidence` carries a kind, subject ID, artifact digest, authority and review record. This verifies **consistency and identity relative to supplied trusted evidence**, not the external truth of a producer's assertion. Genuine label adjudication, task capability review, resource observations and independent custody cannot be manufactured by this code or by a self-issued JSON assertion. External review is required; these records are not cryptographic signatures or a replacement for filesystem/service access control.

Three identities deliberately have different lifecycles:

1. `collection_id(cohort)` binds study/cohort, exact executable source, outcome-free population (all split and excluded identities), resources, captured candidate capabilities/prerequisites and input/reference contract. Fitting-only numerical decisions can remain unresolved while raw recording prerequisites are reviewed.
2. `protocol_id` additionally freezes all scientific choices, dependency/attack definitions and statistical design. It excludes later reports/policies, exposure attestations and review records so they can be attached without circular approvals.
3. `fitting_id(cohort)` binds the protocol plus the exact TrainingManifest, actual captured PolicyBuildSpecification and calibration evidence. Changing reports, labels, captured inputs or calibration invalidates a stale fitting approval. The original unconstrained input specification remains authoritative after freezing: only explicitly derived clean-coverage/reliability matrix overlays are removed when linking a prepared comparison back to that approved input. Legitimate preparation does not require a new fitting approval or authorize a refit; any other specification change fails the link. `manifest_id` binds the entire assembled scientific package including frozen distributions and evidence.

External collection approval targets collection ID; protocol approval targets protocol ID; fitting approval targets fitting ID. A `FinalRelease` must name exact manifest ID, cohort, reservation ID, payload SHA-256, authority and decision record. Readiness inspects release metadata only. `report_final` verifies all upstream gates **before invoking** the caller's payload loader, then verifies exact bytes, typed reservation, labels/reference provenance, complete recording roster and observed resources before replay.

The reporter cannot open Final Test without a supplied loader, and the metadata checker has no loader parameter. Keep outcomes out of any Manifest/Authorizations document. The fixture suite only creates explicit synthetic final partitions in memory; no real restricted data is loaded.

## Population and label integrity

Arithmetic and Factual have separate dispositions and results; pooling is forbidden. Every outcome-free member binds role, example/group/question/content/run identity, reference digest and independent label provenance. History/Development/Final identities cannot cross roles; question/content variants must remain in one related group. Cross-cohort overlap and reintroduction of excluded or group-quarantined examples fail validation. Excluded records and reasons remain part of the immutable manifest identity.

An empirical study cannot consume synthetic training evidence. Provisional/synthetic label provenance cannot be cast to independent ground truth or human verification. Producer label protocol is required; a provisional producer protocol additionally requires an independently reviewed label record before collection, even if its producer class is called VERIFIED_CORRECT. Final metadata contains no correctness bit or answer. The exact record/input digest and independent external label review are required; matching a label-source name alone does not adjudicate truth.

V1 admits explicitly reviewed bounded arithmetic or grounded direct-fact populations. Literal GSM8K/HotpotQA benchmark populations are blocked, even if someone changes a task label: GSM8K is not automatically supported direct arithmetic and HotpotQA is not automatically supported direct-fact verification. Broader support requires actual verifier-owner evidence and a separately reviewed scope/version, not a weakened guard. Missing reference serializers, mismatched reference hashes or inconsistent reference availability cannot be silently flattened into one fitting context.

No new data or fitted policy is shipped. Four historical fitted policy identities are explicitly excluded from this new-policy study. New frozen specifications must use `study_id + ':' + cohort`, the exact prospective training/reservation and exact reviewed source. All original report/adapter/resource and History-derived reputation checks remain enforced through the existing typed framework. A failed/unavailable terminal attempt may complete a recording slot; a missing attempt does not. Failure cannot become abstention and terminal completeness does not prove useful achieved coverage or coverage-floor feasibility.

## Baseline fairness and statistical safeguards

The five comparison families use the same frozen context, feasible rows, candidate capabilities and exclusions, minimum selected/informative contributors, budget/costs, dependencies, obligations, threshold, reference/input population, attack actions and failure/uncertainty contract:

- Full minimax: exact fitted certificate and probabilities, including zero/tiny weights; no refit.
- Greedy: captured selector team and declared aggregation, complete-team evaluation under the same contracts. Infeasible captured teams remain explicitly unavailable.
- Development-fixed: original coverage eligibility and declared objective/tolerance/cost/ID selection. No Final Test selection.
- Uniform: exactly 1/N on frozen feasible rows, without coverage reweighting.
- Aggregation-restricted games: exact parent-matrix projections and numerical certificates preserving coverage and objective.

The existing complete roster also includes separately labelled clean-Development fixed selection; it does not replace the worst-case fixed baseline. The adapter accepts already frozen comparisons only. It cannot create distributions, force a mixture, repair coverage or invent unavailable baselines. Readiness validates source/attack/resource bindings, candidate descriptors, independent inputs, scientific costs/objectives and frozen certificates. No demonstrable defect in the shared mathematics required a historical code change.

Every method exposes expected Development coverage and floor compliance, including violations. All methods share one replay cube. Uncertainty resamples **whole related groups** with the same draw across methods and attacks, integrates exact probabilities, recomputes each attack maximum within each draw, and uses paired full-minus-baseline contrasts. Unequal group sizes retain correct example denominators. Selective risk is undefined at zero decisions; if any resample is undefined, its unconditional interval is omitted and the undefined fraction disclosed. Fewer than two groups produces no population interval. Group-level code does not establish statistical independence absent actual grouping/custody evidence.

`publication_rows` supplies cohort/method/attack/dependency-group keyed metric rows; `uncertainty` supplies matching 95% intervals and paired contrasts. Outputs preserve policy/comparison/cube/protocol IDs, cost units and unavailable-method reasons. They are machine inputs for later tables, not fabricated empirical tables or wider-population claims.

## Metadata readiness and later reporting

```sh
python3 -B -m app.game.research.experiment1.prospective schema
python3 -B -m app.game.research.experiment1.prospective readiness \
  docs/experiment1/prospective/protocol.template.json --sha256 <trusted-file-sha256>
```

Supply separately trusted `--authorizations` / `--authorization-sha256` only after external approvals exist. A draft's expected exit is **2**; individual stages are reported, and exit 0 requires Final Test scoring readiness. This is not an execution command.

Stages, independently reported per cohort:

1. **Protocol review:** structurally valid draft and explicit unresolved decisions; not scientific approval.
2. **History/Development collection:** exact source, reviewed populations/labels/task support/input/reference/resources/collector and scoped collection authorization. Does not require a policy, budget, floor or loss optimization first.
3. **Policy fitting:** additionally actual complete training inputs, an actual captured and bound `PolicyBuildSpecification`, calibration, all scientific decisions, protocol and exact fitting-input approval. A readiness checker does not synthesize a PlanningContext from a roster; the context must pass existing History/resource/requirement checks. Before a new fit it must be the unconstrained bound context, not an existing prepared policy context. No solver is called by readiness; a later legitimate solve may still be infeasible.
4. **Final Test authorization review:** additionally exact new frozen policy/baselines/statistics and independent outcome-free custody with explicit `untouched_reserved` exposure status. Unknown or previously exposed populations fail closed. No outcomes or scoring permission implied.
5. **Final Test scoring:** additionally external exact-manifest/reservation/payload release. Readiness remains outcome-free.

The explicit APIs are `report_development(...)` and `report_final(..., payload_loader=...)`. They require exact observed source revision/fingerprint and typed external authorizations. The loader returns bytes only after approval passes. Explicit gated new-policy fitting and replay commands, plus aggregate publication export, are now documented in [EXECUTION.md](EXECUTION.md). Actual verifier collection remains a separate authorized workflow; this package never dispatches it.

Current real status: protocol/interface review can proceed. Collection, fitting, authorization review and Final Test scoring remain blocked by the template's unresolved inputs and the documented research_v1 scope/label/resource/History/custody prerequisites. Approved research_v1 Development eligibility is not revoked or requested again; it does not satisfy these other gates.


## Validation and completion boundary

The final focused prospective suite passed **47 tests**. The combined regression run passed **187 tests**, including **146 existing** game/research/reporting/input/coverage/reliability/flexible-team/Evidence tests and 41 overlapping prospective cases. After the final custody/exposure, producer-label and actual fitting-input guards, the 47-case prospective suite passed again. This covers **193 distinct final cases**; overlapping runs are not added together. Exact timings, preservation checks and limitations are in `validation.json`.

The initial sparse test checkout omitted the unchanged root `database.py` import shim; adding it to the sparse checkout resolved that import without a database change. An existing synthetic adapter fixture omitted the explicitly required nullable `resource_relocation_binding`; only that one game-owned test-fixture field was added. No production schema, collector, verifier, API, runtime or database file changed.

Reproduction in the established guarded dependency environment:

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest tests/test_experiment1_prospective.py -q -p no:cacheprovider -p no_external_connections
```

The existing regression run additionally covers `test_experiment1_reporting.py`, `test_experiment1_comparison.py`, `test_experiment1_phase_b_inputs.py`, `test_game_research.py`, `test_game_clean_coverage.py`, `test_game_reliability_first.py`, `test_flexible_teams.py` and `test_game_evidence_validation.py`. The optional-model import guard raises on model construction; network/database connections are forbidden. These tests are not a native verifier-runtime or intended-platform collection certificate. Tiny generated LPs, fake report fixtures and in-memory synthetic final partitions do not create empirical results or grant real Final Test access.

The bounded Arithmetic/direct-fact game-side protocol, interfaces, staged gates, fairness checks and report/statistical adapter are implemented and tested. Real collection, fitting and final scoring remain blocked pending the owner prerequisites in `HANDOFF.md`. Arbitrary GSM8K/HotpotQA capability or a broader task contract is not implemented or implied.


The execution/export continuation adds source/configuration provenance, an authorization-gated new-fit/freeze entry, and no-overwrite CSV/LaTeX/PNG/PDF generation. See [EXECUTION.md](EXECUTION.md) for exact commands, current owner prerequisites and publication interpretation. The prior validation totals above describe the pre-export commits; the continuation validation is recorded separately.
