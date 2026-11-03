# Game-mode HTTP validation audit

Date: 2026-11-04. This report summarizes the persisted HTTP validation for
`376b7014-b157-44ef-9e04-fe337f522fb9`. It was prepared from read-only queries
against the local `multi_agent_review_test` database. No validation was rerun.

## Request and decision

| Field | Persisted value |
|---|---|
| Validation ID | `376b7014-b157-44ef-9e04-fe337f522fb9` |
| Question | `What is 510 + 822?` |
| Submitted answer | `1332` |
| Context/reference | `1332` |
| Execution mode | `game` |
| Policy ID | `99d261fcf126e930fa4f0becd7c763ec4224c2e436db7bbe05b64922a6e87f6b` |
| Artifact ID | `1a336129b0c32b8634e434be7c1ff3a8ef73f79353270be03ce61ecf2e91f697` |
| Selected strategy ID | `7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac` |
| Selected verifier team | `evidence`, `rule` |
| Aggregation method | `reputation_weighted` (`log_odds_v1` calculation) |
| Final public status | `uncertain` |
| Final score | `1.0` |
| Final status reason | `minimum_contributors`: 1 informative contributor; 2 required |

The numerical decision was `passed`, but Evidence abstained because it found no
sufficiently relevant evidence. Rule verified `1332`. The minimum-contributor
guard therefore kept the public result `uncertain`. The validation row and audit
both record this public status and guard reason.

## Resource manifest verification

The execution contract expected resource manifest
`898af00e993768ab1d2d320a4cd2d743187ccb475979a39072c1bc8deabf96d7`; the
runtime observer reported the same ID. The resource check passed.

The persisted `resource_observation_audit` also records the explicit relocation
binding `fd3d82f03422b81ead18e5b93f24c9c5606e00702cc10cd47a445b760faf9d26`.
It binds historical manifest
`7abefbec9f37c38a863a3338266b90813442f72d9753bfb127b7484c4d957bb9` to the
verified current manifest above. Its recorded content checks include corpus,
FAISS index, chunks, embedding and NLI models, receipt, and semantic settings.
The observer audit was present both before and after verifier execution.

## Persisted verifier execution

The audit run status is `completed`; the database contains two verifier output
rows for this validation:

| Verifier | Result | Detail |
|---|---|---|
| Evidence | Abstention (`score=0.0`, `passed=false`) | `no_relevant_evidence` |
| Rule | Directional support (`score=1.0`, `passed=true`) | Expected and actual values were both `1332` |

The saved execution record repeats the policy ID, artifact ID, selected strategy,
team, aggregation, public status, and `minimum_contributors` override reason.

## Evidence sources

- `validation_records`, selected by the exact validation ID.
- `validation_audits`, selected by the exact validation ID; `run_status` is
  `completed` and `run_summary` contains the game execution and resource audits.
- `verifier_outputs`, selected by the exact validation ID and ordered by
  `execution_order`; the Rule output embeds the game execution record.

All requested audit fields were available and consistently linked to this
validation ID. No policy or artifact identity was inferred from a separate
direct-service run.
