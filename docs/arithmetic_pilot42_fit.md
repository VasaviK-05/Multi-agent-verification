# Approved arithmetic engineering-pilot policy

**Empirical engineering-pilot policy fitted, exported and validated. The selected
policy returns uncertainty on every development example under every evaluated attack.**
This is a successful offline build, not evidence of useful decisive verification,
research improvement, or broader applicability.

## Approval and unchanged configuration

The human user explicitly approved the complete existing proposal for this arithmetic
engineering pilot only. Approval is recorded in `build/arithmetic-pilot42/approval.json`.
The exact approved configuration digest is:

`af723595edffe54fbd8cd6f1d3c082bd718c53edfddd2d063bdda8aa6094ad41`

This is SHA-256 of the existing canonical_json UTF-8 representation of the nested
PolicyBuildSpecification. It equals the builder input digest and validated specification
ID. The original proposal file SHA-256 is:

`788fe19c11f9a06a3014eb337b246d359802c85a9ad2ef9ba779a5ef3529901e`

The original proposal, recordings and calibration artifact remain byte-for-byte
unchanged. `approved-policy-input.json` contains the exact nested specification,
including its original `UNAPPROVED-proposal-v1` version text. That historical text was
preserved to avoid changing the configuration digest; the separate human approval
record supplies authorization. No loss, threshold, prior, budget, attack, roster,
dependency, seed, numerical tolerance, context or dataset setting was changed.

Existing calibration `c32267151f0fdf265ca502652f11f6828d967b985ab1efbd7a33fdd69d117398`
was reused without calling calibrate or apply_calibration, and without new measurements.
Artifact reload validation checked its existing integrity. The already calibrated,
bound context was supplied directly to the normal builder without calibration flags.
The approval/audit files link calibration lineage because this direct build path does
not reapply a calibration artifact to an already bound context.

## Data and applicability

The input is constructed, reference-assisted one-operation arithmetic, not an external
benchmark. Exact Fraction arithmetic independently established labels. History and
development each contain 20 groups/40 candidates; one correct and one substantively
incorrect answer belong to each group. Seed 42 fixes group assignments. Final test
remains 20 groups/40 candidates under procedural holdout, not third-party custody.

Only the existing rule and semantic adapters were collected. Semantic was supplied
an explicit correct-result reference and supported **every one of the 80 collected
candidates, including all 40 incorrect answers**. Its similarity outputs are not
arithmetic correctness certificates. No evidence-verifier robustness is evaluated.

**The minimum-two constraint and two-candidate roster permit only one team, with two
aggregation choices. This pilot cannot demonstrate adaptive team selection or cost
optimization. Results apply only to this constructed, reference-assisted arithmetic
engineering pilot.** Both strategies have identical estimated cost and resource loss;
there is no cost tradeoff for the optimizer to choose.

## Complete strategy probabilities

Both feasible strategies are retained in the artifact, including zero probability:

- Team `[rule, semantic]`, reputation_weighted: **probability 1.0**;
  strategy ID `4740575c2e29074c1bfdc0e85077446d31884b4a0e65ad126156df4a5ed3bf95`.
- Team `[rule, semantic]`, dependency_group: **probability 0.0**;
  strategy ID `a2ea28d77c27dec2a4854796d14860e9876d1a4c7f2672a90d80a637f49c0b1f`.

Total probability is 1; all mass is on team size two. Each strategy costs an estimated
12.94808874517912 ms, the unchanged sum of measured attempt means. It is neither
parallel request latency nor monetary cost. The cost penalty is constant 0.1 loss
for either strategy, using the approved 0.007723147560077727 loss/ms resource weight.

## Development results, separate from resource cost

For the fitted distribution, each evaluated scenario—clean, forced_support,
forced_rejection, confidence_inflation and suppression—has:

- Decision-only development validation loss: **0.2**.
- Development decision coverage: **0%**; uncertainty rate **100%**.
- Expected estimated attempt cost: **12.94808874517912 ms**.
- Resource contribution: **0.1** loss.
- Cost-inclusive game objective: **0.3**, serialized as 0.30000000000000004.

Thus clean and worst-case development validation loss are both 0.2, and clean and
worst-case game objectives are both 0.3. All five scenarios, including clean, are tied
worst cases under the selected policy. The apparent absence of decisive errors does
not mean high accuracy: there are no public decisions, so selective risk is undefined.

## Payoff comparison and interpretation

The complete strategy payoff rows **are not equivalent**, under either exact equality
or absolute tolerance 1e-12 with relative tolerance zero. Maximum cell difference is
approximately 0.3. Ordered columns are clean, forced_support, forced_rejection,
confidence_inflation and suppression.

- reputation_weighted decision-only losses: `[0.2, 0.2, 0.2, 0.2, 0.2]`;
  cost-inclusive objectives: `[0.3, 0.3, 0.3, 0.3, 0.3]`;
  decision coverages: `[0, 0, 0, 0, 0]`.
- dependency_group decision-only losses: `[0, 0.5, 0.5, 0, 0.2]`;
  cost-inclusive objectives: `[0.1, 0.6, 0.6, 0.1, 0.3]`;
  decision coverages: `[1, 1, 1, 1, 0]`.

Only the suppression column is equal across these two rows. The solver's mass-one
allocation reflects this specific fixed game and approved penalties. It is **not
evidence that reputation-weighted aggregation is generally superior**; in particular,
dependency grouping has better clean loss/coverage in these development recordings.
Had full rows been equivalent, their probability allocation would not distinguish
aggregation performance; the actual rows here were explicitly checked and differ.

The recorded clean replay reason is minimum_contributors on all 40 development
examples for reputation weighting. Under approved Beta(1,1) priors, history establishes
rule: 40 successes/0 failures, mean 0.9761904761904762; semantic: 20 successes/20 failures,
mean 0.5. The existing log-odds implementation assigns semantic zero reputation weight,
leaving one active contributor below the minimum of two. This explains the public
uncertainty using actual replay diagnostics rather than a causal story about model
quality. The configured 0.2 uncertainty penalty is smaller than the dependency row's
0.5 worst attacked directional-error loss. No thresholds or failure gates were relaxed
to make the policy decisive.

## Validation and identities

The existing builder fitted twice and checked matrix, snapshot and probability
equivalence (absolute tolerance 1e-12, relative tolerance zero; snapshot records exact).
Exported JSON was reloaded and its policy and numerical certificate revalidated.
The certificate reports optimal status, primal-dual gap 0, normalization residual 0,
upper/lower value 0.30000000000000004 and certificate tolerance 1e-8.

Provider/runtime checks include InMemoryPolicyProvider snapshot, DeploymentEpisode and
GameRuntime construction, frozen-planning compatibility and a seeded policy draw.
An additional offline runtime replay consumed retained development reports and actual
retained pre/post resource observations and matched existing offline replay exactly.
It did not execute new verifier inference or claim fresh live-resource observations.

The run blocked all opens under the final-custody directory, final-evaluation calls,
calibration application/recalibration, network connections and DB/API/orchestration
imports. Guarded follow-up verification also blocked optimizer calls. No final payload
was opened, no final evaluation ran, and source recordings/calibration/proposal hashes
were checked unchanged. Raw bundle-to-training-manifest equality was also verified.

Focused builder/runtime regression suite: **85 passed**, no failures. No application
source was changed in this fit turn. There are no new or classified baseline failures.

Identifiers:

- Artifact: `6b52c2cc954d461a9a1d34d4ffcf23b048a77f494104fbca7a7f038271167a94`.
- Policy: `0927804d0fe9ac9f9b2ca83a0cda98dd569a3b60fab09c3747b022a662db0517`.
- Matrix: `1a2570eba400e794df06906060049bd50762eea878fcc23a026a33d28310fa6a`.
- Proposed/approved history snapshot: `d4353a946a8a8043f25dfcaa31930bafc31ac28b6ab4b5a653f1f2935071db3d`.

Git revision is 224a2e59792b7ee0183bfa64aed0481dcad57d78, with working-tree/source
digests retained. Solver environment: Python 3.11.5, NumPy 2.4.6, SciPy 1.17.1,
HiGHS 1.12.0 and Pydantic 2.13.5. Numerical accuracy is not sampling uncertainty.

## Commands and outputs

Executed commands:

```powershell
.venv/Scripts/python.exe build/arithmetic-pilot42/fit_approved.py
.venv/Scripts/python.exe build/arithmetic-pilot42/verify_approved.py
.venv/Scripts/python.exe -m pytest tests/test_game_build.py tests/test_game_runtime.py -q -p no:cacheprovider
```

The first guarded script records approval and invokes the existing builder with the
exact unchanged input, equivalent to the following command without calibration flags:

```powershell
.venv/Scripts/python.exe -m app.game.offline.build build/arithmetic-pilot42/approved-policy-input.json --output-dir build/arithmetic-pilot42/fitted-policy
```

That directory already contains the successful artifact; rerunning the builder there
intentionally refuses to overwrite it. Preserve the original approved output.

Outputs:

- `build/arithmetic-pilot42/approval.json`: exact approval/configuration/source digests.
- `build/arithmetic-pilot42/approved-policy-input.json`: exact approved nested input.
- `build/arithmetic-pilot42/fitted-policy/policy.json`: existing PolicyArtifact format.
- `build/arithmetic-pilot42/fitted-policy/build-report.json`: scientific outputs,
  reproducibility and incidental build metadata separated.
- `build/arithmetic-pilot42/fitted-policy/approval-and-validation.json`: all strategy
  probabilities, per-strategy/per-attack losses/coverage, payoff-equivalence check,
  approval/calibration linkage, certificate and scope limits.
- `build/arithmetic-pilot42/fitted-policy/runtime-replay-verification.json`: guarded
  source-manifest and historical-runtime parity validation, including replay reasons.

Only this result document, the preparation document's status note and generated offline
approval/build/validation artifacts were added/updated this turn. Existing concurrent
work was preserved. No DB/API changes, production writes, commits or pushes occurred.

## Shared-code availability

Referenced `build/` recordings, fitted artifacts, approval receipts and diagnostic
traces are local-only and are not distributed by this Git branch. This Markdown
report preserves their historical results and limitations. No new inference or
final evaluation is authorized by publishing the source.
