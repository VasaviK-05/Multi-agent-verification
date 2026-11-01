# Informative-contributor reliability-first exploration

Development only. No final-test access, inference, recalibration or deployment. All fourteen strategies are retained in every policy.

Legacy all-strategy replay was reproduced exactly before changing code. New-contributor outcomes were rebuilt from the unchanged retained reports; history reputation is unchanged.

## Original

Artifact `238adc94fa3d6d81f60740d4cb585c52befa1748ea2ca1ee7aa2e169cf464236` at `build/factual-policy42-20261029/fitted-policy/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 1; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.975000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.975000.

Probability on zero-clean-coverage strategies: 1.

Scenarios (expected false counts out of forty):
- clean: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- forced_support: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- forced_rejection: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- confidence_inflation: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.

## Legacy coverage 25%

Artifact `d4e0b039891c011cddbc535d0a522328f862baa9f5cba3bc82fee2e454526829` at `build/factual-coverage-exploration42/coverage-25/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 0.75; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0.25; estimated cost 233.181544984 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.975000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.975000.

Probability on zero-clean-coverage strategies: 0.75.

Scenarios (expected false counts out of forty):
- clean: coverage 25.000000%, false accept/reject 0/0, uncertainty 75.000000%, validation loss 0.15, expected cost 194.562842180 ms, old cost-inclusive diagnostic 0.15150177172.
- forced_support: coverage 25.000000%, false accept/reject 5/0, uncertainty 75.000000%, validation loss 0.275, expected cost 194.562842180 ms, old cost-inclusive diagnostic 0.27650177172.
- forced_rejection: coverage 25.000000%, false accept/reject 0/5, uncertainty 75.000000%, validation loss 0.275, expected cost 194.562842180 ms, old cost-inclusive diagnostic 0.27650177172.
- confidence_inflation: coverage 25.000000%, false accept/reject 0/0, uncertainty 75.000000%, validation loss 0.15, expected cost 194.562842180 ms, old cost-inclusive diagnostic 0.15150177172.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 194.562842180 ms, old cost-inclusive diagnostic 0.20150177172.

## Legacy coverage 50%

Artifact `44f89c998f2652b7885a3cfd40f2b9fae7cbfb1ae7709556a1f141f4b91ae022` at `build/factual-coverage-exploration42/coverage-50/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 0.5; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0.5; estimated cost 233.181544984 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.975000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.975000.

Probability on zero-clean-coverage strategies: 0.5.

Scenarios (expected false counts out of forty):
- clean: coverage 50.000000%, false accept/reject 0/0, uncertainty 50.000000%, validation loss 0.1, expected cost 207.435743115 ms, old cost-inclusive diagnostic 0.101601133748.
- forced_support: coverage 50.000000%, false accept/reject 10/0, uncertainty 50.000000%, validation loss 0.35, expected cost 207.435743115 ms, old cost-inclusive diagnostic 0.351601133748.
- forced_rejection: coverage 50.000000%, false accept/reject 0/10, uncertainty 50.000000%, validation loss 0.35, expected cost 207.435743115 ms, old cost-inclusive diagnostic 0.351601133748.
- confidence_inflation: coverage 50.000000%, false accept/reject 0/0, uncertainty 50.000000%, validation loss 0.1, expected cost 207.435743115 ms, old cost-inclusive diagnostic 0.101601133748.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 207.435743115 ms, old cost-inclusive diagnostic 0.201601133748.

## Legacy coverage 75%

Artifact `b3592bc1bab2c49abcd8c18ac52f95d005ccb2efa75363a2418809fa23de98d0` at `build/factual-coverage-exploration42/coverage-75/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 0.25; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0.75; estimated cost 233.181544984 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.975000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 1.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.975000.

Probability on zero-clean-coverage strategies: 0.25.

Scenarios (expected false counts out of forty):
- clean: coverage 75.000000%, false accept/reject 0/0, uncertainty 25.000000%, validation loss 0.05, expected cost 220.308644050 ms, old cost-inclusive diagnostic 0.0517004957759.
- forced_support: coverage 75.000000%, false accept/reject 15/0, uncertainty 25.000000%, validation loss 0.425, expected cost 220.308644050 ms, old cost-inclusive diagnostic 0.426700495776.
- forced_rejection: coverage 75.000000%, false accept/reject 0/15, uncertainty 25.000000%, validation loss 0.425, expected cost 220.308644050 ms, old cost-inclusive diagnostic 0.426700495776.
- confidence_inflation: coverage 75.000000%, false accept/reject 0/0, uncertainty 25.000000%, validation loss 0.05, expected cost 220.308644050 ms, old cost-inclusive diagnostic 0.0517004957759.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 220.308644050 ms, old cost-inclusive diagnostic 0.201700495776.

## Informative contributors, old objective

Artifact `a7099f0659e65476f31766b9b530126b85dc1f68d801a6a0c0f2b0c77fffb6c9` at `build/factual-reliability-first42/informative-old-objective/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 1; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.

Probability on zero-clean-coverage strategies: 1.

Scenarios (expected false counts out of forty):
- clean: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- forced_support: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- forced_rejection: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- confidence_inflation: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 181.689941246 ms, old cost-inclusive diagnostic 0.201402409692.

## Informative contributors, reliability first

Artifact `7163d5c448504374081be9133b9b9977a8d873cd36e30ea8e25985c86ab98550` at `build/factual-reliability-first42/reliability-first/policy.json`.

Every strategy:
- ('confidence', 'evidence') / reputation_weighted: probability 0.947368421053; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence') / dependency_group: probability 0; estimated cost 12903.808043734 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule') / reputation_weighted: probability 0.0526315789474; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule') / dependency_group: probability 0; estimated cost 181.689941246 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('evidence', 'semantic') / dependency_group: probability 0; estimated cost 233.181544984 ms; finalized clean coverage 0.000000.
- ('confidence', 'evidence', 'rule') / reputation_weighted: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule') / dependency_group: probability 0; estimated cost 12903.935088732 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'semantic') / dependency_group: probability 0; estimated cost 12955.426692471 ms; finalized clean coverage 0.950000.
- ('evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 233.308589982 ms; finalized clean coverage 0.000000.
- ('confidence', 'evidence', 'rule', 'semantic') / reputation_weighted: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.
- ('confidence', 'evidence', 'rule', 'semantic') / dependency_group: probability 0; estimated cost 12955.553737469 ms; finalized clean coverage 0.950000.

Probability on zero-clean-coverage strategies: 0.0526315789474.

Scenarios (expected false counts out of forty):
- clean: coverage 90.000000%, false accept/reject 0/0, uncertainty 10.000000%, validation loss 0.02, expected cost 12234.222880445 ms, old cost-inclusive diagnostic 0.114432265331.
- forced_support: coverage 92.368421%, false accept/reject 18.9473684/0, uncertainty 7.631579%, validation loss 0.488947368421, expected cost 12234.222880445 ms, old cost-inclusive diagnostic 0.583379633752.
- forced_rejection: coverage 92.368421%, false accept/reject 0/18, uncertainty 7.631579%, validation loss 0.465263157895, expected cost 12234.222880445 ms, old cost-inclusive diagnostic 0.559695423226.
- confidence_inflation: coverage 90.000000%, false accept/reject 0/0, uncertainty 10.000000%, validation loss 0.02, expected cost 12234.222880445 ms, old cost-inclusive diagnostic 0.114432265331.
- suppression: coverage 0.000000%, false accept/reject 0/0, uncertainty 100.000000%, validation loss 0.2, expected cost 12234.222880445 ms, old cost-inclusive diagnostic 0.294432265331.

## Every strategy under the informative contract


### ['confidence', 'evidence'] / reputation_weighted
Cost 12903.808043734 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence'] / dependency_group
Cost 12903.808043734 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'rule'] / reputation_weighted
Cost 181.689941246 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'rule'] / dependency_group
Cost 181.689941246 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'semantic'] / reputation_weighted
Cost 233.181544984 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'semantic'] / dependency_group
Cost 233.181544984 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'rule'] / reputation_weighted
Cost 12903.935088732 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'rule'] / dependency_group
Cost 12903.935088732 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'semantic'] / reputation_weighted
Cost 12955.426692471 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'semantic'] / dependency_group
Cost 12955.426692471 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'rule', 'semantic'] / reputation_weighted
Cost 233.308589982 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['evidence', 'rule', 'semantic'] / dependency_group
Cost 233.308589982 ms.
- clean: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_support: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- forced_rejection: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- confidence_inflation: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'1': 40}, uncertainty reasons {'minimum_contributors': 40}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted
Cost 12955.553737469 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

### ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group
Cost 12955.553737469 ms.
- clean: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_support: coverage 0.975000, validation loss 0.505000000, false accept/reject 20.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- forced_rejection: coverage 0.975000, validation loss 0.480000000, false accept/reject 0.0/19.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- confidence_inflation: coverage 0.950000, validation loss 0.010000000, false accept/reject 0.0/0.0, contributors {'2': 39, '1': 1}, uncertainty reasons {'minimum_contributors': 1}.
- suppression: coverage 0.000000, validation loss 0.200000000, false accept/reject 0.0/0.0, contributors {'0': 40}, uncertainty reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

## Certificates and interpretation

Stage A optimum 0.488947368421, primal/dual gap 5.55111512313e-17; loss tolerance 1e-8.
Stage B cap 0.488947378421; expected cost 12234.222880445 ms; cost dual bound 12234.222880445 ms; gap 0 ms; cost tolerance 1e-8 ms.
Epsilon is 1e-8 loss units; cap feasibility is checked at 1e-12 loss units. Coverage and probability normalization tolerance is 1e-12.
The 90% floor binds. About 5.263% of draws choose a zero-clean-coverage plan; the rest choose Evidence+Confidence, which has 95% clean coverage on these records. This is expected coverage, not request-specific adaptation. Sampling precedes verifier outcomes.
Evidence+Confidence is the least costly team with two informative history contributors. Evidence+Rule is the cheapest always-abstaining plan. Their mixture meets the approved floor at minimum primary loss, then minimum cost. The floor prevents Stage B from trading any further reliability for cost in this dataset.
Both aggregations on Evidence+Confidence have equivalent finalized empirical losses/coverage under this contract. Solver allocation is not evidence that reputation weighting is superior.
All informative verifiers remain in one modeled compromise group. Forced support is worst case and suppression gives zero coverage. Two informative contributors are not independent evidence.
Recommendation: use this variant for the next engineering review when two informative contributors and 90% expected clean coverage are required. Its high shared-group worst-case error precludes a robustness claim or automatic operational activation.
If the product forbids intentionally choosing an incapable plan, this variant still falls short. A future separately versioned, prospectively approved plan-admissibility contract could require enough positive-history potentially influential members before optimization. That rule is not implemented here; no strategy was removed after observing results.
Scope remains the constructed reference-assisted known-corpus capital-fact pilot, not open-domain factual reliability. These are exploratory development findings, not held-out superiority or paper settings.
