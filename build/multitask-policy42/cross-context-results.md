# Task-conditioned engineering study

Exploratory history/development only; no held-out superiority or framework-wide coverage claim. No final-test verifier outcomes were collected or opened.

All task identities are derived from actual question requirements and subject-domain metadata. Subject domain remains general/unknown; histories and snapshots are separate by task.

## arithmetic

Collection: 320 executed / 320 planned; complete=True; returned states {('semantic', 'directional'): 42, ('evidence', 'abstention'): 80, ('rule', 'directional'): 80, ('confidence', 'directional'): 75, ('confidence', 'abstention'): 5, ('semantic', 'abstention'): 38}.
Task: `{'domain_status': 'unknown', 'question_rules_version': 'explicit_task_questions_v1', 'requirements': ['arithmetic'], 'subject_domain': 'general', 'version': 'domain_requirements_task_v1'}`; primary budget 21258.335265022 ms; maximum finalized clean coverage 82.500000%; primary status infeasible_coverage.

Frozen history (directional observations only; no development updates):
- semantic: n=23, successes/failures 15/8, Beta(16.0,9.0), mean 0.640000000, variance 0.008861538, log-odds 0.575364145, group reliability 0.280000000.
- evidence: n=0, successes/failures 0/0, Beta(1.0,1.0), mean 0.500000000, variance 0.083333333, log-odds 0.000000000, group reliability 0.000000000.
- rule: n=40, successes/failures 40/0, Beta(41.0,1.0), mean 0.976190476, variance 0.000540526, log-odds 3.713572067, group reliability 0.952380952.
- confidence: n=37, successes/failures 33/4, Beta(34.0,5.0), mean 0.871794872, variance 0.002794214, log-odds 1.916922612, group reliability 0.743589744.

Measured costs (all first/subsequent attempts, including failures):
- confidence: n=80, mean 21127.605638743 ms, median 12924.418149982, p95 16027.639199980, failed attempts 0.
- evidence: n=80, mean 81.452711276 ms, median 48.870350118, p95 83.028800087, failed attempts 0.
- rule: n=80, mean 9.678209995 ms, median 0.131999841, p95 0.214499887, failed attempts 0.
- semantic: n=80, mean 39.598705008 ms, median 32.885350054, p95 69.178599864, failed attempts 0.

Unconstrained cost-inclusive comparison (not the primary coverage-constrained result):
All strategy probabilities: [['d795e00a8d21ac1e182d750a9fe048d30c3c4492280e44b743b43b6757dd67af', 0.0], ['64b162c44dcbea1a090efbd170737e194dc8d94b9e7eb9c7d31dbf80d7a7587e', 0.0], ['7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac', 1.0], ['ad0b8ffb719c57171af3713fed9ef5ee56abfeb911bb36d093c9e29406ae23f0', 0.0], ['4740575c2e29074c1bfdc0e85077446d31884b4a0e65ad126156df4a5ed3bf95', 0.0], ['a2ea28d77c27dec2a4854796d14860e9876d1a4c7f2672a90d80a637f49c0b1f', 0.0], ['dea450431e59622e8ab01bcacdd36a476ac4178be40fd69aa9dd96827ca4a4cc', 0.0], ['540a5c0b689536093709b5679474795b804bad7cef677cd9f0b568cb424dd7b6', 0.0], ['af11eaa3ee6059ee3c6f347c12e36fc7e13ba2dac7b4abc089ac1401834d25bd', 0.0], ['e7f6a62bdd249067887d49775a0d48564437cccac307a41b977c6c0900f82fad', 0.0], ['0fe15a30015ee9a39c985f9da48410607557e8d2367fd93edd8c86cf811b42d8', 0.0], ['93f8f1735acd71696c00f71b470f27264d552eef589a6342b913525568f74273', 0.0], ['3622f462375d038af2cce7dfac0fdb65ccef7e5410c40f153d709b3d428fed04', 0.0], ['a4c895d6c9e9095ae7ff52c31be7bf0324109e4868d61f3d136ddeb23c27cc80', 0.0]]
Worst-case validation loss 0.200000000; cost-inclusive objective 0.200428683.
Repeated build: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}
- clean: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 91.130921271 ms; cost-inclusive objective 0.200428683.
- forced_support: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 91.130921271 ms; cost-inclusive objective 0.200428683.
- forced_rejection: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 91.130921271 ms; cost-inclusive objective 0.200428683.
- confidence_inflation: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 91.130921271 ms; cost-inclusive objective 0.200428683.
- suppression: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 91.130921271 ms; cost-inclusive objective 0.200428683.

### Budget 49.276915003 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 47.500000%; target remains 90%.
Feasible strategies:
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 91.130921271 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 47.500000%; target remains 90%.
Feasible strategies:
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 130.729626279 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 47.500000%; target remains 90%.
Feasible strategies:
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 21137.283848738 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 82.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'rule'] / reputation_weighted; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule'] / dependency_group; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 21176.882553747 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 82.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'rule'] / reputation_weighted; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule'] / dependency_group; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 21218.736560014 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 82.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'rule'] / reputation_weighted; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule'] / dependency_group; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / reputation_weighted; estimated cost 21218.736560014 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / dependency_group; estimated cost 21218.736560014 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 21258.335265022 ms (PRIMARY)

Status infeasible_coverage; maximum clean coverage 82.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'rule'] / reputation_weighted; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule'] / dependency_group; estimated cost 21137.283848738 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 91.130921271 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 49.276915003 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / reputation_weighted; estimated cost 21218.736560014 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / dependency_group; estimated cost 21218.736560014 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 38}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 21176.882553747 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 130.729626279 ms; probability undefined (infeasible); clean coverage 47.500000%.
  - clean: validation loss 0.105000000; coverage 47.500000%; false accept/reject 0.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_support: validation loss 0.280000000; coverage 47.500000%; false accept/reject 7.0/0.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.405000000; coverage 47.500000%; false accept/reject 0.0/12.0; uncertainty 21.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.140000000; coverage 30.000000%; false accept/reject 0.0/0.0; uncertainty 28.0/40; informative contributor counts {'1': 21, '2': 19}; reasons {'minimum_contributors': 21}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 21258.335265022 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group; estimated cost 21258.335265022 ms; probability undefined (infeasible); clean coverage 82.500000%.
  - clean: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_support: validation loss 0.485000000; coverage 95.000000%; false accept/reject 19.0/0.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - forced_rejection: validation loss 0.485000000; coverage 95.000000%; false accept/reject 0.0/19.0; uncertainty 2.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - confidence_inflation: validation loss 0.035000000; coverage 82.500000%; false accept/reject 0.0/0.0; uncertainty 7.0/40; informative contributor counts {'1': 2, '2': 19, '3': 19}; reasons {'minimum_contributors': 2}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

## semantic

Collection: 320 executed / 320 planned; complete=True; returned states {('semantic', 'directional'): 80, ('evidence', 'abstention'): 80, ('rule', 'abstention'): 80, ('confidence', 'directional'): 48, ('confidence', 'abstention'): 32}.
Task: `{'domain_status': 'unknown', 'question_rules_version': 'explicit_task_questions_v1', 'requirements': ['semantic_comparison'], 'subject_domain': 'general', 'version': 'domain_requirements_task_v1'}`; primary budget 15852.424223730 ms; maximum finalized clean coverage 0.000000%; primary status infeasible_coverage.

Frozen history (directional observations only; no development updates):
- semantic: n=40, successes/failures 20/20, Beta(21.0,21.0), mean 0.500000000, variance 0.005813953, log-odds 0.000000000, group reliability 0.000000000.
- evidence: n=0, successes/failures 0/0, Beta(1.0,1.0), mean 0.500000000, variance 0.083333333, log-odds 0.000000000, group reliability 0.000000000.
- rule: n=0, successes/failures 0/0, Beta(1.0,1.0), mean 0.500000000, variance 0.083333333, log-odds 0.000000000, group reliability 0.000000000.
- confidence: n=25, successes/failures 25/0, Beta(26.0,1.0), mean 0.962962963, variance 0.001273761, log-odds 3.258096538, group reliability 0.925925926.

Measured costs (all first/subsequent attempts, including failures):
- confidence: n=80, mean 15778.139943749 ms, median 15686.098299921, p95 16641.255100025, failed attempts 0.
- evidence: n=80, mean 31.851542497 ms, median 28.191750054, p95 49.679300049, failed attempts 0.
- rule: n=80, mean 0.109292485 ms, median 0.101899845, p95 0.155400019, failed attempts 0.
- semantic: n=80, mean 42.323444999 ms, median 37.747399998, p95 70.334500168, failed attempts 0.

Unconstrained cost-inclusive comparison (not the primary coverage-constrained result):
All strategy probabilities: [['9b8f912c18417466a3f39b8fcbfd1ead99adf476bb9acf08d076bd2cebe38955', 0.0], ['c29fd335d469ec5b3a677ce60bf87fe2c5cad8291a021d7d22b08222eace6bdf', 0.0], ['ffd37ff484bdd284b26b778b55d4a61643fccf8c16478dc823747108fda99a1a', 0.0], ['6217a7773c2d9d7810dfbe84246628041fd0811b167b5837df44af4e734c3dc8', 0.0], ['4740575c2e29074c1bfdc0e85077446d31884b4a0e65ad126156df4a5ed3bf95', 1.0], ['a2ea28d77c27dec2a4854796d14860e9876d1a4c7f2672a90d80a637f49c0b1f', 0.0], ['9875cf55b78231dd008cd3a76c2cad530d6c4e58235977c28238a5b481d1366a', 0.0], ['fceafaec57a919b560281d9bc960f5ced93866d6c58139b7c6d28ee25c4c5be9', 0.0], ['af11eaa3ee6059ee3c6f347c12e36fc7e13ba2dac7b4abc089ac1401834d25bd', 0.0], ['e7f6a62bdd249067887d49775a0d48564437cccac307a41b977c6c0900f82fad', 0.0], ['0fe15a30015ee9a39c985f9da48410607557e8d2367fd93edd8c86cf811b42d8', 0.0], ['93f8f1735acd71696c00f71b470f27264d552eef589a6342b913525568f74273', 0.0], ['3622f462375d038af2cce7dfac0fdb65ccef7e5410c40f153d709b3d428fed04', 0.0], ['a4c895d6c9e9095ae7ff52c31be7bf0324109e4868d61f3d136ddeb23c27cc80', 0.0]]
Worst-case validation loss 0.200000000; cost-inclusive objective 0.200267673.
Repeated build: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}
- clean: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 42.432737484 ms; cost-inclusive objective 0.200267673.
- forced_support: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 42.432737484 ms; cost-inclusive objective 0.200267673.
- forced_rejection: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 42.432737484 ms; cost-inclusive objective 0.200267673.
- confidence_inflation: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 42.432737484 ms; cost-inclusive objective 0.200267673.
- suppression: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 42.432737484 ms; cost-inclusive objective 0.200267673.

### Budget 42.432737484 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 74.174987496 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 74.284279981 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15820.463388748 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['confidence', 'semantic'] / reputation_weighted; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'semantic'] / dependency_group; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15820.572681233 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['confidence', 'semantic'] / reputation_weighted; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'semantic'] / dependency_group; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15852.314931244 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['confidence', 'semantic'] / reputation_weighted; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'semantic'] / dependency_group; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted; estimated cost 15852.314931244 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / dependency_group; estimated cost 15852.314931244 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15852.424223730 ms (PRIMARY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['confidence', 'semantic'] / reputation_weighted; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'semantic'] / dependency_group; estimated cost 15820.463388748 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 74.174987496 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / reputation_weighted; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['rule', 'semantic'] / dependency_group; estimated cost 42.432737484 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted; estimated cost 15852.314931244 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / dependency_group; estimated cost 15852.314931244 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'rule', 'semantic'] / dependency_group; estimated cost 15820.572681233 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 74.284279981 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 15852.424223730 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group; estimated cost 15852.424223730 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 23, '0': 17}; reasons {'minimum_contributors': 40}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

## factual

Collection: 320 executed / 320 planned; complete=True; returned states {('semantic', 'directional'): 80, ('evidence', 'directional'): 78, ('rule', 'abstention'): 80, ('confidence', 'abstention'): 48, ('confidence', 'directional'): 32, ('evidence', 'abstention'): 2}.
Task: `{'domain_status': 'unknown', 'question_rules_version': 'explicit_task_questions_v1', 'requirements': ['direct_fact'], 'subject_domain': 'general', 'version': 'domain_requirements_task_v1'}`; primary budget 15965.046464995 ms; maximum finalized clean coverage 37.500000%; primary status infeasible_coverage.

Frozen history (directional observations only; no development updates):
- semantic: n=40, successes/failures 20/20, Beta(21.0,21.0), mean 0.500000000, variance 0.005813953, log-odds 0.000000000, group reliability 0.000000000.
- evidence: n=38, successes/failures 37/1, Beta(38.0,2.0), mean 0.950000000, variance 0.001158537, log-odds 2.944438979, group reliability 0.900000000.
- rule: n=0, successes/failures 0/0, Beta(1.0,1.0), mean 0.500000000, variance 0.083333333, log-odds 0.000000000, group reliability 0.000000000.
- confidence: n=13, successes/failures 10/3, Beta(11.0,4.0), mean 0.733333333, variance 0.012222222, log-odds 1.011600912, group reliability 0.466666667.

Measured costs (all first/subsequent attempts, including failures):
- confidence: n=80, mean 15732.456318731 ms, median 15725.480849971, p95 16793.699200032, failed attempts 0.
- evidence: n=80, mean 188.798948753 ms, median 161.681699916, p95 218.529399950, failed attempts 0.
- rule: n=80, mean 0.104604999 ms, median 0.094049843, p95 0.165000092, failed attempts 0.
- semantic: n=80, mean 43.686592512 ms, median 38.552649901, p95 70.190300001, failed attempts 0.

Unconstrained cost-inclusive comparison (not the primary coverage-constrained result):
All strategy probabilities: [['521d922d91e2367835123c62acfae9d81b982483fd5d4ef79bb63ec38e1704be', 0.0], ['3a041262d6b0e951a3d2234de194f118dabb0c771712a30c9d4b96fd4fe7b109', 0.0], ['7bebbe44c42c138b65816273a8807e0be825e5543903862c49970aa7f92813ac', 1.0], ['ad0b8ffb719c57171af3713fed9ef5ee56abfeb911bb36d093c9e29406ae23f0', 0.0], ['ffd37ff484bdd284b26b778b55d4a61643fccf8c16478dc823747108fda99a1a', 0.0], ['6217a7773c2d9d7810dfbe84246628041fd0811b167b5837df44af4e734c3dc8', 0.0], ['dea450431e59622e8ab01bcacdd36a476ac4178be40fd69aa9dd96827ca4a4cc', 0.0], ['540a5c0b689536093709b5679474795b804bad7cef677cd9f0b568cb424dd7b6', 0.0], ['9875cf55b78231dd008cd3a76c2cad530d6c4e58235977c28238a5b481d1366a', 0.0], ['fceafaec57a919b560281d9bc960f5ced93866d6c58139b7c6d28ee25c4c5be9', 0.0], ['0fe15a30015ee9a39c985f9da48410607557e8d2367fd93edd8c86cf811b42d8', 0.0], ['93f8f1735acd71696c00f71b470f27264d552eef589a6342b913525568f74273', 0.0], ['3622f462375d038af2cce7dfac0fdb65ccef7e5410c40f153d709b3d428fed04', 0.0], ['a4c895d6c9e9095ae7ff52c31be7bf0324109e4868d61f3d136ddeb23c27cc80', 0.0]]
Worst-case validation loss 0.200000000; cost-inclusive objective 0.201183232.
Repeated build: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}
- clean: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 188.903553752 ms; cost-inclusive objective 0.201183232.
- forced_support: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 188.903553752 ms; cost-inclusive objective 0.201183232.
- forced_rejection: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 188.903553752 ms; cost-inclusive objective 0.201183232.
- confidence_inflation: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 188.903553752 ms; cost-inclusive objective 0.201183232.
- suppression: coverage 0.000000%; validation loss 0.200000000; false accept/reject 0/0; uncertainty 100.000000%; cost 188.903553752 ms; cost-inclusive objective 0.201183232.

### Budget 188.903553752 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 232.485541265 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 232.590146264 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 0.000000%; target remains 90%.
Feasible strategies:
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15921.255267484 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 37.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'evidence'] / reputation_weighted; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence'] / dependency_group; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15921.359872483 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 37.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'evidence'] / reputation_weighted; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence'] / dependency_group; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / reputation_weighted; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / dependency_group; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15964.941859996 ms (DESCRIPTIVE SENSITIVITY)

Status infeasible_coverage; maximum clean coverage 37.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'evidence'] / reputation_weighted; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence'] / dependency_group; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / reputation_weighted; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / dependency_group; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted; estimated cost 15964.941859996 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / dependency_group; estimated cost 15964.941859996 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

### Budget 15965.046464995 ms (PRIMARY)

Status infeasible_coverage; maximum clean coverage 37.500000%; target remains 90%.
Feasible strategies:
- ['confidence', 'evidence'] / reputation_weighted; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence'] / dependency_group; estimated cost 15921.255267484 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / reputation_weighted; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule'] / dependency_group; estimated cost 188.903553752 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / reputation_weighted; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'semantic'] / dependency_group; estimated cost 232.485541265 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / reputation_weighted; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule'] / dependency_group; estimated cost 15921.359872483 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / reputation_weighted; estimated cost 15964.941859996 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'semantic'] / dependency_group; estimated cost 15964.941859996 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['evidence', 'rule', 'semantic'] / dependency_group; estimated cost 232.590146264 ms; probability undefined (infeasible); clean coverage 0.000000%.
  - clean: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - forced_rejection: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40}.
  - confidence_inflation: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'1': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / reputation_weighted; estimated cost 15965.046464995 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.
- ['confidence', 'evidence', 'rule', 'semantic'] / dependency_group; estimated cost 15965.046464995 ms; probability undefined (infeasible); clean coverage 37.500000%.
  - clean: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - forced_support: validation loss 0.305000000; coverage 47.500000%; false accept/reject 8.0/0.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - forced_rejection: validation loss 0.380000000; coverage 47.500000%; false accept/reject 0.0/11.0; uncertainty 21.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21}.
  - confidence_inflation: validation loss 0.125000000; coverage 37.500000%; false accept/reject 0.0/0.0; uncertainty 25.0/40; informative contributor counts {'2': 19, '1': 21}; reasons {'minimum_contributors': 21, 'missing_achieved_coverage': 1}.
  - suppression: validation loss 0.200000000; coverage 0.000000%; false accept/reject 0.0/0.0; uncertainty 40.0/40; informative contributor counts {'0': 40}; reasons {'minimum_contributors': 40, 'missing_achieved_coverage': 40, 'selected_execution_incomplete': 40}.

No constrained policy or probabilities exist at this budget. This is not a zero-probability distribution, and the target was not relaxed.

## Runtime and limitations

Retained-report execution through actual TaskQuestionAnalyzer, scoped task router, captured plans, provider and public finalizer; not fresh inference
All primary outcomes and diagnostic baseline executions remain distinct. Infeasible primary routes fail safely; diagnostic unconstrained artifacts are not replacements for a 90%-coverage policy.
The prepared-question scope uses training/reservation metadata only. Unknown, unsupported, outside-study, missing-reference and incompatible-budget cases fail without cross-task/capital-history fallback.
Independent workers shared CPU/Ollama capacity. Costs are empirical summed verifier-attempt times, not money, isolated latency or a claim of efficiency improvement. Do not pool timing samples across cohorts.
The corpus/source files were previously inspected, so reservations are procedural source-known evaluation groups, not independently blinded unseen knowledge. No final-test outcomes were accessed.
Semantic similarity is not factual truth or a guarantee of equivalence. Confidence agreement is not independent evidence. All configured informative verifiers remain connected through actual shared models and conservative shared-unknown assumptions.
No verifier use or aggregation allocation was forced. Infeasible targets show limitations of existing outputs/history/contributor rules, not permission to weaken guards or relabel data.
All previous arithmetic, capital, coverage and reliability-first artifacts are preserved. No production integration, commit, push, merge or API activation occurred.
