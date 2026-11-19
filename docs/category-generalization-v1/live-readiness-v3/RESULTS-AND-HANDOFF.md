# Authorized arithmetic native smoke: results and release handoff

Branch: codex/category-generalization-v3. Execution started from 34aadd6, after 9997215 preserved the completed readiness work. User clarified and authorized the unchanged sealed v2 question `What is 4 + 4?` with candidates 8/9 and independent reference 8. No code, seal, fitted policy, resource manifest, probability, threshold, budget or route was modified for execution.

## Actual results

One invocation of the exact v2 execute command, with `PYTHONDONTWRITEBYTECODE=1`, using `/private/tmp/category-engineering-v4/bin/python`; output `/private/tmp/reusable-arithmetic-native-v2`; plan `34b309882e79e547e564fc2382495565c42e4ee79bd2e8e6dfd461c4f79e20ad`. Process exit code 0. No retry.

| Candidate | Real Rule report | Public decision | Measured verifier latency |
|---|---|---|---:|
| 8 | SUPPORT, score 1, `Expected 8; received 8.` | passed | 2.05 ms |
| 9 | REJECT, score 0, `Expected 8; received 9.` | failed | 0.08 ms |

Both used question `What is 4 + 4?`, context `8`, factual `arithmetic_addition`, exact Decimal equality. Both have one informative contributor (minimum one), achieved arithmetic coverage, no unresolved requirement and no override reason. These are two bounded observations, not measured category-wide error rates or a statistical certification.

Both selected:

- Artifact `cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477`.
- Policy `c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14`, version `game_policy_reliability_first_v1`.
- Compatibility `5f217f601b87ab4d2889b59ca9bda07d8a07a6774d074625f8b01c2050cb736d`.
- Strategy `afbd22f1ed2281814985af413a3945c5706d1aa838eba2d1b79cc391371521ac`, team Rule, aggregation reputation_weighted; original full vector retained (selected mass 1).
- Original threshold .55, budget 21258.33526502247 ms, estimated cost 9.678209995036013 ms each. Measured latencies above do not replace frozen cost estimates.

Execution receipts report `native_smoke_complete`, `policy_identity_preserved`, `coverage_and_contributors_ready` and `expected_decisions_observed` all true; two starts and two completions, zero generations and zero metadata requests. Network/HTTP, other native verifier construction/execution, fitting, greedy substitution, child-process and output-directory guards recorded no violation. The runner wrote only the approved receipt directory. Subsequent byte-identical archiving into this documentation directory is a separately authorized preservation action, not a native run.

Native identity evidence: original `create_singleton` constructed the actual RuleVerifier; pre/post `SingletonObserver` checked actual class identity, unchanged method/source/configuration and instance settings. The existing GameRuntime journal records each start before `verifier.verify` and each fresh result afterwards. There were no mocks or development-output replay. `fallback_enabled` is false and termination is complete_selected_team. Original frozen full resource identity `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb` is retained; approved singleton transfer `ddbb12d1a91ee520887ee0462e81a57ea34109b821487b8cc045a90b268eec87` maps to the actual Rule scope `c53d93e72864ad960841cf5762e84b9a3f7653d93d0b96e724622ddb7b64092c`. Pre/post observed manifests match and `active_instances_checked` is true for both requests. No unused model/index/service was claimed to be constructed.

Limitation: after result.json was saved, interpreter shutdown emitted an ignored exception in logging cleanup: the native profiling callback received a frame whose `__name__` was None, and `.startswith` raised AttributeError. This is a teardown instrumentation defect, not a recorded policy/provenance/dispatch failure; process exit remained zero and both attempts were already complete. It is preserved in receipt-inventory.json. No rerun or modification of sealed code was made. A future separately reviewed tool revision should make that callback teardown-safe before another native plan is approved; the current run must not be described as warning-free.

## Preserved evidence

`native-arithmetic-receipts/plan.json`, `result.json` and `native-calls.jsonl` are byte-identical copies of the original output files. `receipt-inventory.json` records hashes, sizes, invocation count, authorization and teardown diagnostic. Post-run stdlib receipt checks verified the two decisions, two completed journal entries, policy identity, coverage/contributors and pre/post resource attestations. `preservation.json` verifies historical bytes and registration inventories unchanged and compares the already archived 69-question/207-projection receipts; those dynamic tests and the prior 120 category tests were not rerun. No new test-suite pass count is inferred from the native smoke. Previous nine targeted engineering tests remain the latest targeted test run.

## Exact remaining backend activation requirements

No API, DB, frontend, generator or verifier implementation was edited. Runtime activation remains absent; this native smoke called ReusablePolicyGameRuntime directly, not either HTTP route.

1. **Runtime/config owner:** implement trusted server-only versioned scope loading and a disabled-by-default explicit reuse option in `app/game/deployment.py:create_game_runtime` and its settings contract. Validate pinned artifact/compatibility IDs, bounded pattern/rules version and scope review basis; never accept policy/resource/budget overrides from request bodies. Existing flexible/bundle/artifact selection must retain current default behavior and mutual-exclusion checks.
2. **Runtime owner:** on the approved flexible branch, construct the existing legacy runtime and call `compose_factory_bound_reuse(legacy, approved_artifacts, reviewed_scopes, rng=legacy._rng)`. This returns the existing Flexible-compatible adapter shape. Keep ExactFirstCategoryDispatcher ahead of reuse, including exact-route failures. No silent retry through reuse. The broad smoke pattern is not a reviewed deployment scope package.
3. **Resource owner:** configure reviewed route-specific adapters/relocation receipts and actual-instance resource factories. The lazy adapter is needed because ValidationService constructs an empty selector for flexible runtimes; passing the unbound reusable runtime directly will not supply real verifier resources. Keep request-local observers, journal forwarding, all pre/post identity/provenance checks and unchanged budget/contributor/coverage/finalization behavior. Review shared RNG concurrency and resource construction overhead separately from frozen attempt costs.
4. **Backend owner, `/validate`:** verify the shared `app/api/routes.py` service instance resolves the opt-in factory, executes new submitted inputs, persists journal/validation/report records, and returns passed/failed/uncertain/unavailable results correctly with no cached development output. Use the approved reference-present arithmetic payloads first. Do not silently synthesize context.
5. **Backend owner, `/generate-and-validate`:** verify generated answer is passed to the SAME service/runtime with original question and independently supplied context. This route adds generator execution, DB writes and a recovery lifecycle; those need separately bounded authorization/environment. Arithmetic smoke authorization covers neither generator nor DB execution.
6. **Backend/database owners:** validate startup recovery/lifespan, migration/environment requirements, interrupted executions, durable attempt starts/completions and no duplicate/retried native calls. The existing memory-only constructor test is not evidence of persistent HTTP acceptance.
7. **Release owner:** repeat all 69 historical question projections after the integration patch, comparing policy/compatibility IDs, complete probabilities, resource requirements and expected execution. Run owned routing/API regression and guard tests; resolve or explicitly adjudicate the pre-existing failures recorded in ENGINEERING-ACCEPTANCE-v3.md. Keep deployment disabled through review. No merge/deploy is authorized here.

For a future independently fitted reference-free policy, `reviewed_resource_factories` currently only authorizes pinned historical singleton/reference artifacts. A new policy needs its own reviewed native-resource binding and execution attestation; it must not be slipped into the old singleton transfer allowlist.

## Verdict

Engineering reuse and this two-case real Rule smoke have succeeded, subject to the disclosed teardown diagnostic. Production factory/both-route acceptance remains incomplete. Evidence/reference native readiness still lacks the original approved resources and execution authorization. Independent research certification is unchanged. **Not merge-ready as a live-enabled release.** The reference-free work remains planning only; see REFERENCE-FREE-PLAN.md. No native collection or new fitting for that contract was started.
