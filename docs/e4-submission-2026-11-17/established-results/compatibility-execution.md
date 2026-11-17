# Established compatibility and execution evidence

Statuses below apply only to the observed conditions. Historical guard outcomes and current Rule-only execution remain separate evidence populations.

| Observed check | Result | Scope and supporting records |
|---|---|---|
| Current Rule route resource/instance compatibility | PASS | [Current checks](evidence/current-api/compatibility-checks.json), actual startup and current response pre/post resource proofs; reviewed Rule singleton and preserved policy identities. |
| Observed service metadata identity | MATCH | Recorded Ollama 0.40.14, llama3.2:3b and model digest agree with the reviewed Flexible service observation. This is metadata identity. |
| Historical missing-index rejection | PASS | [Historical response](evidence/historical-api/resource-missing-index.json): resource_incompatible, before_dispatch, zero verifier reports/attempts. |
| Historical input/scope guards | PASS | [Unsupported question](evidence/historical-api/unsupported-scope.json), [missing context](evidence/historical-api/ref-missing-context.json), [malformed Compound](evidence/historical-api/compound-malformed.json), [HTTP schema rejection](evidence/historical-api/schema-malformed.json). Recorded negative inputs were rejected without verifier dispatch. |
| Bounded execution within frozen budget | PASS | The three retained current executions selected estimated Rule cost 9.678209995036013 ms within frozen estimated-attempt budget 21258.33526502247 ms. This row describes successful within-budget execution and approved call accounting. |
| Selected Rule completion, aggregation and finalization | PASS | [Correct response](evidence/current-api/correct/response.json), [incorrect response](evidence/current-api/incorrect/response.json), [timed response](evidence/current-api/timed/response.json): Rule-only team, reputation-weighted aggregation, complete selected-team termination. |
| Linked persistence/readback | PASS | Correct, incorrect and timed persistence records include completed execution journal, one linked completed attempt, one verifier output and completed audit. Actual database identity is multi_agent_review_test. |

The correct arithmetic candidate yields SUPPORT/final passed; the incorrect candidate yields REJECT/final failed. Rejection is an answer outcome, not a verifier execution failure. All retained current calls completed. The original two-case execution and the successful corrected timing execution used separate bounded approvals, each with zero generations.
