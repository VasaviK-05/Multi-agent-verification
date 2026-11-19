# Reusable fitted-policy live readiness

Prepared on codex/category-generalization-v3 after accepted commit 0361f979d82805b16cc75ecc6fa12f9ca5697a44. No merge, deployment, native verifier construction/execution, Ollama request, fitting, model download or historical-resource change was performed for this readiness task.

## Verdict

**Not ready to merge as a live-enabled release.** Engineering reuse is demonstrated with mocks; native smoke success and production factory activation remain outstanding. Independent research certification of category-wide performance is not established by a smoke test or by the unchanged historical evaluation. The additive adapter and preparation tooling can be reviewed independently, but must not be represented as activated functionality.

The accepted 120 category tests are not rerun here. Seven additional mock/preparation checks cover the actual ValidationService empty-selector construction path, lazy binding, fail-closed resources, preparation without native factories, approval interlock and attempt journaling. Historical core/API failures documented in ENGINEERING-ACCEPTANCE-v3.md remain outside this change; no new claim that those suites pass is made.

## Integration handoff — exact outstanding changes

Runtime/config owner:

1. Extend `app/game/deployment.py:create_game_runtime` with a separately versioned, explicitly disabled-by-default server opt-in. Retain the existing legacy factory result when disabled. Do not take scope, artifact, resource, budget or policy overrides from HTTP requests.
2. Load a reviewed trusted-server scope package using `ReusablePolicyScope` validation. Pin scope version, original artifact and compatibility IDs, question-rules version, bounded question patterns and review basis. Review the package before enabling it; preparation scopes are test proposals, not deployment certification. Reject missing/duplicate/invalid bindings at startup.
3. Construct the original `FlexiblePolicyGameRuntime`, obtain the approved original artifacts from its provider, and call `compose_factory_bound_reuse(legacy, artifacts, scopes, rng=legacy._rng)` from `app/game/reusable_deployment.py`. The returned Flexible subclass preserves the existing service contract. Its exact-first dispatcher must retain all 69 registered routes, including their failures, before considering reuse. Never retry a failed exact route through reuse.
4. Use the existing route-specific `_adapter_for` resource configurations and reviewed relocation bindings. The new lazy helper binds actual native selectors and observers per compatible request, replacing the service's deliberately empty selector only inside reusable dispatch. It never eagerly constructs every model. No fake full-resource observer is acceptable. Shared RNG concurrency and per-request construction overhead should be reviewed for deployment; frozen attempt costs do not measure that startup overhead.
5. Preserve execution_journal forwarding, original finalization, coverage, contributor, provenance and budget checks. Fail closed on incompatible/missing resources; no greedy/fitter fallback. Maintain the original full probability vector, zero-probability strategies and aggregation definitions.

Backend owner:

6. Exercise both existing `/validate` and `/generate-and-validate` through their shared ValidationService after the factory/config hook exists. No API implementation change is intrinsically required to select this runtime. Verify real startup/lifespan recovery, persistent execution journal, unavailable/error responses and budget accounting in the intended DB environment. Our new service-constructor test uses mocks and memory-only history; it is not a deployed HTTP test.
7. For `/generate-and-validate`, separately authorize and bound generator execution and DB writes. Supply independently sourced reference context; never copy the generated candidate into the reference. Native arithmetic smoke below intentionally bypasses generator, DB and startup lifecycle. Recheck every original registered route's policy ID, compatibility ID, probability vector, resource identity and execution expectations before merging the eventual activation patch.

No API, DB, frontend, generator or verifier implementation files were edited for this handoff. `create_game_runtime` and settings remain unchanged: activation is still absent.

## Arithmetic reference is a genuine fitted-context requirement

`scripts/multitask_policy42.py` constructed each arithmetic reference independently as the exact sum. The fitted planning context included reference availability, all four candidates and their prerequisites. `PlanningContext.compatibility_id` preserves these features even though the original fitted distribution selects Rule alone with probability one. Semantic is reference-dependent; its zero-mass strategies remain part of the original plan. Rule itself does not need reference text, but that does not authorize dropping a feature from the full fitted compatibility contract.

Original arithmetic artifact: `cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477`.
Policy: `c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14`.
Compatibility: `5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`.
Selected strategy is Rule / reputation_weighted, probability 1. No question-instance refit is needed.

Valid `/validate` JSON (reference independently established before candidate inspection):

```json
{"question":"What is 4 + 4?","answer":"8","context":"8"}
```

Negative control:

```json
{"question":"What is 4 + 4?","answer":"9","context":"8"}
```

Preparation derives reference 8 independently with both Fraction and Decimal and records that receipt. Missing/blank/judgment-list context remains incompatible. These payloads require the opt-in factory integration above; the current unmodified factory still uses its existing routing. Fabricated padding, candidate echoing, manifest relaxation and silent refitting are prohibited.

## Prepared native runs — approval still required

The sealed JSON plans are in `plans/`. Preparation performs classification, original compatibility matching and static/source checks only. It does not instantiate Rule, Evidence, Semantic or Confidence. The arithmetic plan has no preparation blockers; this is not native success.

Run from `/private/tmp/category-generalization-v3` only after separate owner authorization:

```sh
/private/tmp/category-engineering-v4/bin/python -m scripts.reusable_native_smoke execute --plan docs/category-generalization-v1/live-readiness-v1/plans/arithmetic.json --plan-id cd4aaf31c0e564ef5c7efa4008327251c975c47ba9f73dabeddecbab14a3cb56 --output /private/tmp/reusable-arithmetic-native-v1 --execute-approved
```

This performs exactly two current-question Rule attempts: accept 8 and reject 9 for unseen `What is 4 + 4?`, both with independently established context 8. Zero Ollama generations, zero HTTP, 120-second outer limit, no retry/resume, exclusive new output directory. No new dependency is proposed. Uses the approved isolated Python 3.12 environment; Rule requires no model/corpus/index construction. Original unused configuration fields are retained, not claimed as present resources.

The runner seals source inventory, bundle hash, original policy/version/compatibility, all probabilities and strategy definitions. Its journal checks original selected strategy and aggregation and persists attempt starts before dispatch. It prohibits fit/build/minimax entry points and greedy selector methods, denies unauthorized network/resource writes, and uses original native factories/observers and GameRuntime dispatch. It records new reports rather than replaying development reports. Exit success requires completed real attempts, exact original identity/distribution and expected decisions. Coverage/contributor readiness is separately recorded. Execution is not evidence until result and attempt ledgers exist and are reviewed.

| Check | Native attempts maximum | Ollama generations maximum | Metadata GET maximum | Outer seconds |
|---|---:|---:|---:|---:|
| Arithmetic correct + incorrect | 2 Rule | 0 | 0 | 120 |
| Factual snapshot wording | 1 Evidence | 0 | 0 | 120 |
| Reference paraphrase | 2 (Semantic, optionally Confidence) | 5 | 20 | 600 |

Original arithmetic budget is 21258.33526502247 ms, Rule estimate 9.678209995036013 ms per attempt. Factual budget is 15965.046464995248 ms, Evidence estimate 188.79894875281025 ms. Reference budget is 16594.78458249673 ms; Semantic estimate 102.07135749794816 ms, Confidence estimate 16428.737124999952 ms. These frozen estimates are preserved, not execution measurements. Local CPU/time use and reference service requests have no asserted monetary price; no paid external endpoint is proposed.

## Evidence and Semantic blockers and conditions

Evidence plan uses previously unregistered wording `what is the population of Belgium?`, answer/reference `The population of Belgium is 11941781.` from the recorded GeoNames source snapshot. This is a wording-reuse check, not an unseen-entity or current-population claim. Confirm the actual pinned corpus row before execution; source metadata is not a cached verifier verdict. Retain original Evidence probability-one policy.

Reference plan uses `Paraphrase this reference: Mira delivered twelve parcels to Noor.`, candidate `Twelve parcels were delivered to Noor by Mira.`, context `Mira delivered twelve parcels to Noor.` Retain original Semantic singleton probability 1/6 and Confidence+Semantic probability 5/6, reputation-weighted aggregation. No forced singleton or renormalization. A legitimate neutral Semantic result may remain uncertain; native completion alone does not establish contributor/coverage readiness or accuracy.

Both plans currently have null configurations and deliberately cannot execute. Supply reviewed existing route-specific AdapterConfiguration files, then prepare a NEW directory and review new plan IDs before requesting execution:

```sh
/private/tmp/category-engineering-v4/bin/python -m scripts.reusable_native_smoke prepare --output /private/tmp/reusable-readiness-resourced-v2 --evidence-configuration /ABSOLUTE/EXISTING/REVIEWED/evidence.json --reference-configuration /ABSOLUTE/EXISTING/REVIEWED/reference.json
```

The uppercase paths are required inputs, not available files. Execution then uses the same execute command with that new plan's exact path/ID and a fresh output directory, only after separate approval. No resource rebuild, substitute corpus, download or service update is authorized.

Required corpus SHA256 is `28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a`. This worktree lacks both historical corpus locations and index-v2. Its root corpus has different hash `523e51acef45dc91d1d85b5c3c7e4747de47ae322128dc8d1fcad925ea5be57a` and is not compatible. Existing adapter snapshot paths are not usable local resources. Evidence needs the exact reviewed corpus/index/embedding/NLI resources and actual-instance attestation/relocation receipt. Reference requires the full original roster and resource/service identity, even if sampling chooses Semantic alone. Do not narrow the roster to avoid dependencies.

Frozen reference service is Ollama 0.40.14, llama3.2:3b digest `sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`, localhost:11434; original five samples, temperature .8, timeout 60. Reference execution may make bounded version/tags GETs and up to five generations. No service was contacted during preparation. Existing source capsules and relocation/service/model receipts must validate unchanged. Package import success does not substitute for native model/manifest compatibility.

## Remaining acceptance gates

1. Review opt-in scope package and factory/config patch; retain disabled defaults and exact-first behavior.
2. Authorize and execute sealed arithmetic smoke; inspect fresh reports, attempt ledger, selected strategy, aggregation, identity, decisions, coverage and measured costs.
3. Locate and attest original Evidence/reference resources; review new plans and authorize their bounded execution. Stop on incompatibility; no repair by changing historical resources.
4. Backend owner runs both real API paths with approved generator/DB environment and persistent journal/recovery; verify historical route regression and all runtime guards.
5. Resolve known baseline failures or explicitly adjudicate them before release. Smoke tests do not supersede independent held-out category certification, calibration/coverage or loss measurements. No broad category accuracy claim follows from these three bounded checks.
