# Exploratory coverage-constrained development results

Not primary paper settings or held-out evidence. Clean coverage is the exact policy-weighted expectation over retained development examples, not a Monte Carlo estimate.

The original policy remains unchanged. All fourteen strategies are retained in every variant.

History weights: Evidence and Confidence each posterior 41/42, log-odds log(41), group reliability 20/21; Semantic and Rule each 1/2 and zero weights.
Group aggregation counts active reports, including zero-reliability Semantic; log-odds aggregation excludes its zero-weight vote. This existing contract is unchanged.

## Original

Clean/all-attack loss 0.2; coverage 0; expected cost 181.689941 ms; worst objective 0.201402409692. Evidence + Rule / reputation-weighted probability 1; all thirteen other probabilities zero.

## Target 25%

Artifact `d4e0b039891c011cddbc535d0a522328f862baa9f5cba3bc82fee2e454526829`; worst objective 0.27650177172.

Every strategy:
- ['confidence', 'evidence'] / reputation_weighted: probability 0, estimated cost 12903.808043734 ms.
- ['confidence', 'evidence'] / dependency_group: probability 0, estimated cost 12903.808043734 ms.
- ['evidence', 'rule'] / reputation_weighted: probability 0.75, estimated cost 181.689941246 ms.
- ['evidence', 'rule'] / dependency_group: probability 0, estimated cost 181.689941246 ms.
- ['evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.181544984 ms.
- ['evidence', 'semantic'] / dependency_group: probability 0.25, estimated cost 233.181544984 ms.
- ['confidence', 'evidence', 'rule'] / reputation_weighted: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'rule'] / dependency_group: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.426692471 ms.
- ['confidence', 'evidence', 'semantic'] / dependency_group: probability 0, estimated cost 12955.426692471 ms.
- ['evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.308589982 ms.
- ['evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 233.308589982 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.553737469 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 12955.553737469 ms.

Scenarios (false counts are expected counts out of forty):
- clean: coverage 25.000%, false accept/reject 0/0, uncertainty 75.000%, validation loss 0.150000000, estimated cost 194.562842180 ms, cost-inclusive objective 0.151501772.
- forced_support: coverage 25.000%, false accept/reject 5/0, uncertainty 75.000%, validation loss 0.275000000, estimated cost 194.562842180 ms, cost-inclusive objective 0.276501772.
- forced_rejection: coverage 25.000%, false accept/reject 0/5, uncertainty 75.000%, validation loss 0.275000000, estimated cost 194.562842180 ms, cost-inclusive objective 0.276501772.
- confidence_inflation: coverage 25.000%, false accept/reject 0/0, uncertainty 75.000%, validation loss 0.150000000, estimated cost 194.562842180 ms, cost-inclusive objective 0.151501772.
- suppression: coverage 0.000%, false accept/reject 0/0, uncertainty 100.000%, validation loss 0.200000000, estimated cost 194.562842180 ms, cost-inclusive objective 0.201501772.

Certificate:
```json
{
  "version": "clean_coverage_dual_v1",
  "multiplier": 0.3003974481120747,
  "achieved": 0.25,
  "residual": 0.0
}
```

## Target 50%

Artifact `44f89c998f2652b7885a3cfd40f2b9fae7cbfb1ae7709556a1f141f4b91ae022`; worst objective 0.351601133748.

Every strategy:
- ['confidence', 'evidence'] / reputation_weighted: probability 0, estimated cost 12903.808043734 ms.
- ['confidence', 'evidence'] / dependency_group: probability 0, estimated cost 12903.808043734 ms.
- ['evidence', 'rule'] / reputation_weighted: probability 0.5, estimated cost 181.689941246 ms.
- ['evidence', 'rule'] / dependency_group: probability 0, estimated cost 181.689941246 ms.
- ['evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.181544984 ms.
- ['evidence', 'semantic'] / dependency_group: probability 0.5, estimated cost 233.181544984 ms.
- ['confidence', 'evidence', 'rule'] / reputation_weighted: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'rule'] / dependency_group: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.426692471 ms.
- ['confidence', 'evidence', 'semantic'] / dependency_group: probability 0, estimated cost 12955.426692471 ms.
- ['evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.308589982 ms.
- ['evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 233.308589982 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.553737469 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 12955.553737469 ms.

Scenarios (false counts are expected counts out of forty):
- clean: coverage 50.000%, false accept/reject 0/0, uncertainty 50.000%, validation loss 0.100000000, estimated cost 207.435743115 ms, cost-inclusive objective 0.101601134.
- forced_support: coverage 50.000%, false accept/reject 10/0, uncertainty 50.000%, validation loss 0.350000000, estimated cost 207.435743115 ms, cost-inclusive objective 0.351601134.
- forced_rejection: coverage 50.000%, false accept/reject 0/10, uncertainty 50.000%, validation loss 0.350000000, estimated cost 207.435743115 ms, cost-inclusive objective 0.351601134.
- confidence_inflation: coverage 50.000%, false accept/reject 0/0, uncertainty 50.000%, validation loss 0.100000000, estimated cost 207.435743115 ms, cost-inclusive objective 0.101601134.
- suppression: coverage 0.000%, false accept/reject 0/0, uncertainty 100.000%, validation loss 0.200000000, estimated cost 207.435743115 ms, cost-inclusive objective 0.201601134.

Certificate:
```json
{
  "version": "clean_coverage_dual_v1",
  "multiplier": 0.3003974481120747,
  "achieved": 0.5,
  "residual": 0.0
}
```

## Target 75%

Artifact `b3592bc1bab2c49abcd8c18ac52f95d005ccb2efa75363a2418809fa23de98d0`; worst objective 0.426700495776.

Every strategy:
- ['confidence', 'evidence'] / reputation_weighted: probability 0, estimated cost 12903.808043734 ms.
- ['confidence', 'evidence'] / dependency_group: probability 0, estimated cost 12903.808043734 ms.
- ['evidence', 'rule'] / reputation_weighted: probability 0.25, estimated cost 181.689941246 ms.
- ['evidence', 'rule'] / dependency_group: probability 0, estimated cost 181.689941246 ms.
- ['evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.181544984 ms.
- ['evidence', 'semantic'] / dependency_group: probability 0.75, estimated cost 233.181544984 ms.
- ['confidence', 'evidence', 'rule'] / reputation_weighted: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'rule'] / dependency_group: probability 0, estimated cost 12903.935088732 ms.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.426692471 ms.
- ['confidence', 'evidence', 'semantic'] / dependency_group: probability 0, estimated cost 12955.426692471 ms.
- ['evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 233.308589982 ms.
- ['evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 233.308589982 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted: probability 0, estimated cost 12955.553737469 ms.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group: probability 0, estimated cost 12955.553737469 ms.

Scenarios (false counts are expected counts out of forty):
- clean: coverage 75.000%, false accept/reject 0/0, uncertainty 25.000%, validation loss 0.050000000, estimated cost 220.308644050 ms, cost-inclusive objective 0.051700496.
- forced_support: coverage 75.000%, false accept/reject 15/0, uncertainty 25.000%, validation loss 0.425000000, estimated cost 220.308644050 ms, cost-inclusive objective 0.426700496.
- forced_rejection: coverage 75.000%, false accept/reject 0/15, uncertainty 25.000%, validation loss 0.425000000, estimated cost 220.308644050 ms, cost-inclusive objective 0.426700496.
- confidence_inflation: coverage 75.000%, false accept/reject 0/0, uncertainty 25.000%, validation loss 0.050000000, estimated cost 220.308644050 ms, cost-inclusive objective 0.051700496.
- suppression: coverage 0.000%, false accept/reject 0/0, uncertainty 100.000%, validation loss 0.200000000, estimated cost 220.308644050 ms, cost-inclusive objective 0.201700496.

Certificate:
```json
{
  "version": "clean_coverage_dual_v1",
  "multiplier": 0.3003974481120747,
  "achieved": 0.75,
  "residual": 0.0
}
```

## Recommendation and limitations

Use the 50% target as a concrete next exploratory engineering candidate if making a decisive clean decision on half the supported population is worth increasing worst-case objective from 0.20140241 to 0.35160113. Do not activate or call it universally best. Targets 25% and 75% are explicit alternatives, not publication selection.
Scope remains the reference-assisted known-corpus capital-fact pilot. One shared compromise component includes all informative verifiers. The constraint cannot create independent evidence, improve the source labels, or guarantee attacked coverage. Suppression yields zero coverage in all variants.
Only additive clean coverage settings changed. All original losses, budgets, dependencies, guards, recordings and calibration remain unchanged. Final-test payload access is forbidden throughout these commands.
