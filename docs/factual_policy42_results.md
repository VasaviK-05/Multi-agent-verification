# Factual engineering campaign

This campaign reuses the existing collector, calibration, planning, replay,
report-corruption adapters, minimax solver, artifact format and public runtime.
No verifier, retriever, generator, database, API or startup behavior is changed.
The arithmetic pilot and its always-abstaining result remain preserved.

## Scope and data

The local campaign directory is `build/factual-policy42-20261029/` (ignored).
Preparation selected 60 country-capital groups from 132 eligible records, before
inspecting verifier outcomes. Country names must be single ASCII tokens, have one
capital, agree exactly after NFKC/casefold across both source files, and fall
outside the recorded ambiguous/disputed/transition exclusions. Every exclusion,
including eligible records outside the seed-42 sample, is retained in
`dataset-audit.json`. Exclusion reason counts overlap.

The versioned sources are GeoNames `countryInfo.txt` (CC-BY attribution, retained
header) and mledoze countries commit
`6031f5df137c41c76d180c55a0782185ae3ed05b` (ODbL-1.0; retained license).
See [GeoNames terms](https://www.geonames.org/export/) and
[the pinned countries license](https://github.com/mledoze/countries/blob/6031f5df137c41c76d180c55a0782185ae3ed05b/LICENSE).
File hashes and the original files remain local. The sources are independent of
framework decisions, but their lineages may overlap; these are not two independent
human adjudications. Labels use structured capital identity, never substring
matching or verifier agreement. Incorrect answers are constructed by rotating
different capital names within each split, not naturally occurring model errors.

ISO groups are sorted, shuffled with seed 42 and assigned twenty each to history,
development and final reservation. Both answer variants stay together: forty
candidates per split. Only history/development enter collection and fitting.
Custody is procedural, not independently blinded. Preparation writes the final
candidate/label payload once under `custody/`; subsequent driver phases install
an open audit guard forbidding that directory. No final reports are collected.
The background corpus contains public reference facts for all sixty countries;
this is a known-corpus, reference-assisted engineering scope, not unseen knowledge.

All actual analyzer outputs share the same general-domain, easy/0.13, known
`direct_fact` requirements context with unknown domain status. The selector retains
its actual default profiles, capability descriptors and participant constraints.
Semantic's reference prerequisite is satisfied; readiness remains unknown until
observed execution. Only Evidence promises expected factual coverage. There are
seven feasible teams containing Evidence and at least one other candidate, each
with both aggregations. Neither structural feasibility nor a passing software
probe establishes useful contributors or robustness.

## Evidence readiness and recording

`evidence_public_contract_validation_v2` replaces the obsolete unconditional
block only when a complete retained probe suite passes public report normalization
and factual coverage checks and matches the exact Evidence resource manifest.
It includes controlled support/rejection/neutral/conflict and installed-model NLI
support/rejection/neutral reports. Conflict/neutral must abstain without achieved
factual coverage. Missing proof retains the old blocker; incomplete, malformed,
failed or stale proof cannot clear it. This is a trusted-producer consistency
receipt, like resource provenance, not cryptographic proof of execution.
Other resource, binding, coverage, prerequisite, contributor and failure guards
remain enforced. Legacy recording serialization omits the new optional field
when absent, preserving historical identities. Evaluated decision semantics and
the PolicyArtifact format are unchanged.

The isolated index-v2 receipt witnesses the actual installed embedding weights
and new public-fact corpus. No old index-v1 receipt or historical calibration is
relabelled current. Installed NLI produced support 0.997381866, rejection
0.999589622 and neutral uncertainty in the independent software probes. The
controlled public Evidence probes also passed. These probes are not study samples.

The completed checkpoint has 320 executed/retained attempts: eighty per candidate.
Semantic and Evidence each returned eighty directional reports; Rule abstained
eighty times; Confidence returned seventy-nine directional reports and one
abstention. There are no failed executions, completeness gaps or collection issues.
The local network audit contains exactly 400 successful bounded loopback generation
requests and 1,290 successful metadata GETs. A preceding sandbox-denied metadata
request is preserved separately; it occurred before any verifier attempt.
Resuming this task did not repeat preparation or any verifier attempt.

Attempt timers surround `verify`, excluding model initialization, readiness
probes and pre/post resource hashing. First and subsequent measured calls are all
retained, with zero warmup exclusions. Means (eighty samples each): Confidence
12,722.245147 ms; Evidence 181.562896 ms; Semantic 51.618649 ms; Rule 0.127045 ms.
These are summed attempt wall times, not money, CPU time or guaranteed request
latency. Initialization/probes and shared-machine contention limit portability.

Approved settings are losses 1/1/0.2, Beta(1,1), strict signed threshold 0.55,
existing participant/contributor guards, both aggregations, existing one-group
report corruption including unavailable suppression, tolerance 1e-8 and seed 42.
The measured budget is 12,955.553737469018 ms and resource weight is 0.1/B.
Known embedding and NLI sharing is recorded from actual resource fingerprints;
conservative unresolved/shared-unknown treatment connects all four verifiers.
No development-driven setting change is authorized or applied.

## Commands and local producer outputs

The preparation command below uses the current explicit configuration interface;
the historical run used a reviewed local draft through the earlier interface.
That hidden dependency was removed without regenerating this campaign. See
[preparation configuration](preparation_configuration.md). Do not replay these
commands over preserved outputs.

```powershell
.venv/Scripts/python.exe -m scripts.factual_policy42 prepare --root build/factual-policy42-20261029 --adapter-config PATH_TO_REVIEWED_ADAPTER.json
.venv/Scripts/python.exe -m app.benchmark.project_adapter prepare-index build/factual-policy42-20261029/adapter.json --output build/factual-policy42-20261029/index-receipt.json
.venv/Scripts/python.exe -m scripts.factual_policy42 collect --root build/factual-policy42-20261029
.venv/Scripts/python.exe -m app.game.offline.collect check build/factual-policy42-20261029/collection
.venv/Scripts/python.exe -m scripts.factual_policy42 fit --root build/factual-policy42-20261029
```

Preparation/index/collection commands above document completed work; do not rerun
them in this directory. Producers use exclusive creation and preserve journals.
No resume implementation was necessary: the original process had finished all
320 attempts before the resumed task inspected it. `collection-report.json`,
`recordings.json`, `measurements.json`, request and observed setup are authoritative.
Fit-only failures must be repaired without rerunning collection or overwriting
existing calibration/configuration files. The report-only phase is
`python -m scripts.factual_policy42 report --root ...`; it reads retained reports
and performs live resource checks, not new inference.

Frozen history: Evidence and Confidence each 40 successes/0 failures,
posterior 41/42 and log-odds log(41); Semantic 20/20, posterior 1/2 and zero
log-odds; Rule has no directional observations, prior 1/2 and zero log-odds.
No development labels enter reputation and no production manager is written.

## Fitted result

The existing builder exported and reloaded
`build/factual-policy42-20261029/fitted-policy/policy.json`. It retains all fourteen
strategies. Team costs below are estimated summed attempt milliseconds. Probability
is shown as reputation-weighted / dependency-group respectively:

- Evidence + Rule: 181.689941; **1 / 0**.
- Evidence + Semantic: 233.181545; 0 / 0.
- Confidence + Evidence: 12,903.808044; 0 / 0.
- Evidence + Rule + Semantic: 233.308590; 0 / 0.
- Confidence + Evidence + Rule: 12,903.935089; 0 / 0.
- Confidence + Evidence + Semantic: 12,955.426692; 0 / 0.
- Confidence + Evidence + Rule + Semantic: 12,955.553737; 0 / 0.

Team-size probability totals are two: 1, three: 0, four: 0. Clean, forced support,
forced rejection, confidence inflation and unavailable suppression each have
validation loss **0.2**, uncertainty **100%**, decision coverage **0%**, and false
acceptance/rejection **0/0**. Each has expected estimated cost 181.689941 ms and
cost-inclusive objective **0.2014024096918393**. All scenarios tie for worst case.
The resource penalty is approximately 0.00140241, separate from validation loss.

This is a mathematically valid, always-abstaining artifact, not a useful operational
policy or evidence of robustness/efficiency improvement. The selected team has only
one directional contributor: Evidence has weight log(41), whereas unsupported
Rule abstains. The minimum-two contributor guard therefore overrides even strong
correct clean Evidence decisions. Report corruption preserves existing abstentions;
it does not turn unsupported Rule into a contributor. Suppression also activates
coverage and execution protections. This is intended conservative behavior, not a
reason to weaken contributor guards. Both aggregations on Evidence + Rule have
equivalent payoffs; the solver's allocation does not establish aggregation superiority.

The broad single shared-unknown compromise component and uncertainty loss 0.2
make abstention competitive against directional strategies exposed to coherent
forced errors. The roster does contain two informative history contributors
(Evidence and Confidence), so this study differs from the single-team arithmetic
pilot, but the fitted result still does not demonstrate adaptive team selection.
No threshold, loss, dependency or participant setting was changed after outcomes.

Identifiers:

- Artifact: `238adc94fa3d6d81f60740d4cb585c52befa1748ea2ca1ee7aa2e169cf464236`.
- Policy: `99d6d6369341c48f919c8a8f2a1643f0320821afa15bf9d323e816e5e46dad30`.
- Matrix: `25303e5c2f8d8db609c812b780e9373923204743ee459d56e0000b0cd94504bc`.
- History snapshot: `0aff50756b09cd72d5e653e8739cde685d7ba90ff34188d86c7682315d8e4ad3`.
- Calibration: `d5fd225b45d0b09fb54de3a07344415604638ce004fa8b51dac6218bd25a2793`.
- Recording bundle: `71ccd4a8c331e574e849e1d84b4b9993df60be3c38da2275b19b8b8872eaab3c`.

The LP certificate is optimal at tolerance 1e-8, with zero primal/dual gap,
normalization residual and constraint residuals. Repeated builds agree in matrix,
snapshot and policy probabilities at absolute tolerance 1e-12, relative tolerance
zero. Incidental paths, working-tree metadata and solver prose are excluded from
scientific comparison. The original source revision is
`17b695373f935dc1f5fd09c37cf8917969367f7a` with owned uncommitted additions; the
actual application digest is retained and verified unchanged since collection.
Runtime versions: CPython 3.11.5, NumPy 2.4.6, SciPy 1.17.1, Pydantic 2.13.5,
bundled HiGHS 1.12.0, `linprog(method='highs')` defaults. Model/provider/package
versions and actual snapshots are additionally retained in observed setup.

`approval-binding.json` binds the approved configuration digest, actual bundle,
calibration and driver source digest. `policy-input.json` contains only history,
development and metadata reservation. `fitted-policy/build-report.json` and
`summary.txt` separate validation loss from the cost-inclusive objective.
The exact fit-driver bytes are retained as local `fit-driver.original.py`, matching
the approval binding. A later report-only dataclass serialization fix does not
change the fitted settings, calibration or artifact; the completed report records
its own driver digest separately. The first post-fit report also encountered a
sandbox-denied loopback metadata check; only the report phase was rerun with
metadata access, without new inference or refitting.

## Integration and ownership

Load saved bytes with `PolicyArtifact.model_validate_json`, register the object
in `InMemoryPolicyProvider`, and construct `DeploymentEpisode` using that
artifact's exact context, contract and execution-configuration identity. Use
`GameRuntime` with real selector/adapters and
`app.game.offline.recording_adapters.ProjectObserver`, with
`VERIFIER_COLLECTION_ADAPTER_CONFIG` pointing at the retained adapter configuration.
No API startup registration was added. The artifact contains no training labels
or reports. Compatibility IDs enforce captured planning/resource contracts;
they are not a semantic country allowlist. The integrating caller must also
respect the narrower documented study scope. This always-abstaining artifact is
for engineering inspection, not recommended operational activation.

The study owner owns future scientific changes to threat assumptions, losses or
roster. Such changes require explicit approval and a new bound build. Dependency
independence requires evidence, not removal of `shared_unknown` to obtain a
preferred result. The Semantic owner may investigate all-support behavior under
this reference-assisted scope; no algorithm defect is claimed. Rule's lack of
factual checking is an explicit capability limitation. The obsolete evidence
blanket gate is resolved for the validated resource setup, subject to all other
readiness conditions. A separate full-corpus upstream test still needs the absent
`data/articles_13083.json`; the isolated study does not validate that absent corpus.

Changed reusable files, all within owned workflow/test/documentation scope:

- `app/game/research/evidence_validation.py` — retained versioned probe evidence.
- `app/game/research/readiness.py` — resource-bound evidence condition.
- `app/game/research/specification.py` — optional proof, legacy identity preservation.
- `scripts/factual_policy42.py` — study producer over existing public workflows.
- `scripts/run_factual_diagnostic.py` — bounded request ceilings; original defaults retained.
- `tests/test_game_evidence_validation.py` — proof/tamper/resource checks, preserved guards, bounded network and grouped reproducible preparation regressions.
- `docs/game_policy_build.md` and this handoff.

The pre-existing untracked `docs/game_empirical_build_audit.md` is preserved.
No source/test change was made to verifier/retrieval/generation, DB/API/frontend
or unrelated orchestration. No production writes, inference payments, model
downloads, final evaluation, commits, pushes, merges or API activation occurred.

## Validation commands

The resumed affected suite passed **193 tests**:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_evidence_validation.py tests/test_game_build.py tests/test_game_research.py tests/test_game_collection.py tests/test_cost_calibration.py tests/test_diagnostic_collection.py tests/test_game_runtime.py -q
```

The original public Evidence reproductions passed **4 tests, 89 deselected**:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_adaptive_pipeline.py -q -k 'test_actual_evidence_output_contract_is_consumed_without_models or test_actual_conflicting_evidence_cannot_cover_factual_request'
```

Before interruption, 51 focused readiness/research tests and 267 broader affected
tests passed. Those counts overlap the resumed suite and must not be added as
unique tests. The broader command was:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_game_build.py tests/test_game_collection.py tests/test_cost_calibration.py tests/test_diagnostic_collection.py tests/test_factual_team_pilot.py tests/test_project_collection_adapter.py tests/test_game_completion.py tests/test_game_offline.py tests/test_game_runtime.py -q
git diff --check
rg -n '^(<<<<<<<|=======|>>>>>>>)' app scripts tests --glob '*.py'
```

Whitespace and source conflict-marker checks pass; the marker search returns no
matches. Changed reusable files were checked for accidental credentials and local
machine paths. No new affected-test failure remains. Initial new-test fixture
construction errors (v2 execution/configuration IDs) were corrected without
relaxing contract assertions. The report-only serializer error described above
was corrected separately. Historical evidence failures are not counted as current
baseline failures: the four reproductions now pass. The absent upstream full
corpus remains a separate data limitation, not a failure of the isolated campaign.

## Completed diagnostics and runtime validation

The report-only phase completed successfully after the serializer correction.
`development-report.json` contains every strategy probability/cost, all fourteen
by five scenario metrics, false acceptance/rejection counts, uncertainty/coverage,
history statistics/weights, representative correct/incorrect raw reports and
decision traces, baseline comparisons and two successful runtime parity checks.
`development-summary.md` provides a readable local report, including worked
correct/incorrect examples; its labels remain ignored/private. All forty clean
selected-policy outcomes have reason `minimum_contributors`. For the two retained
examples the numerical scores are +0.996125876904 and -0.999889969826. Each has
one contributor, achieved factual coverage and no execution failure, so both
public decisions remain uncertain. Numerator is log(41) times the signed Evidence
confidence, denominator log(41); Rule contributes no mass. The strict threshold
0.55 is crossed numerically but does not waive contributor protection.

The captured full-team greedy baseline is Evidence + Confidence with
reputation-weighted aggregation. Clean validation loss is 0.01 at 95% coverage;
forced-support loss is 0.505 at 97.5% coverage, forced-rejection 0.48 at 97.5%,
inflation 0.01 at 95%, suppression 0.2 at zero coverage. Uniform feasible-strategy
mixing has clean loss 0.0621428571 at 68.9285714% coverage; forced-support loss
0.4164285714, rejection 0.4057142857, inflation 0.0621428571 and suppression 0.2.
These are recorded complete-team comparisons with identical public guards, not
equivalence to production baseline early stopping/feedback. Detailed counts and
separate cost-inclusive objectives are in the report. No held-out superiority
or measured efficiency improvement follows.

Runtime checks use retained real development reports through public `GameRuntime`
and the live real-resource `ProjectObserver`, not a fabricated observation or new
inference. Correct and incorrect examples both select the saved artifact and
exactly match replay scores/status. Observed resource manifest is
`9c81e66b3356176f658d99dba6d862174d5a99f40d825ba1811dcc0f8b5717ad`.
`final-verification.json` additionally revalidates the saved artifact, solver
certificate and provider, confirms the application source digest has not changed,
checks the archived fit driver against approval, and verifies all ten inventoried
arithmetic files unchanged. It records zero additional inference attempts and an
active custody-open guard. The final local audit commands were:

```powershell
.venv/Scripts/python.exe -m scripts.factual_policy42 report --root build/factual-policy42-20261029
.venv/Scripts/python.exe -c "import runpy; runpy.run_path('build/factual-policy42-20261029/finish_report.py')"
git diff --check
git status --short
```

These are completed producer commands, not instructions to overwrite their
exclusive outputs. All new private/generated artifacts remain under ignored
`build/`; reusable source/tests/docs remain uncommitted. No safe-resume blocker
remains, because the original campaign had already completed every attempt.
The outstanding operational limitation is the approved game's always-abstaining
optimum; a different scientific tradeoff requires the study owner's decision.
