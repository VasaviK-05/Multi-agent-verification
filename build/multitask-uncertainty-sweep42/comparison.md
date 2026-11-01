# Optional coverage / uncertainty development sweep



Exploratory development tradeoffs; expected coverage is population-level, not runtime confidence or per-request routing



No final-test access, new inference, calibration or activation. Independent binary labels remain unchanged.

Costs are summed measured verifier-attempt wall milliseconds under the recorded shared-machine setup, not money or request latency.

FA/FR below are expected counts out of 40 examples (fractional for mixtures); selective risk is errors among decided cases.

Validation loss excludes resource penalty. The separately reported old cost-inclusive diagnostic is not the reliability-first Stage-A objective.

Tiny positive probabilities and floating-point residuals are preserved; target-zero negligible coverage is not useful verification.



## arithmetic / target 0%



Status: complete; maximum finalized clean coverage 82.5%; fixed budget 21258.335265022 ms.

Artifact: `build\multitask-uncertainty-sweep42\arithmetic\coverage-00\policy.json`; ID `bdf3673c1e63a3c5a6e5937ca6c920bccb0b38acd0754696104717270c5c628d`.

Probability on zero-clean-coverage strategies: 0.99999995121951235.

Worst-case validation loss: 0.20000001.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['evidence', 'rule'] / reputation_weighted: p=0.99999995121951235; estimated team cost 91.130921271 ms.

- ['rule', 'semantic'] / reputation_weighted: p=4.8780487742428736e-08; estimated team cost 49.276915003 ms.



Finalized scenarios:

- clean: coverage=2.31707316777e-08; uncertainty=0.999999976829; FA=0; FR=0; selective risk=0; validation loss=0.199999995366; estimated cost=91.130919229 ms; separate old cost-inclusive diagnostic=0.2004286786.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.99999907317069, 'weak_or_conflicting_signal': 0.0}

- forced_support: coverage=2.31707316777e-08; uncertainty=0.999999976829; FA=3.41463414197e-07; FR=0; selective risk=0.368421052632; validation loss=0.200000003902; estimated cost=91.130919229 ms; separate old cost-inclusive diagnostic=0.200428687137.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.99999907317069}

- forced_rejection: coverage=2.31707316777e-08; uncertainty=0.999999976829; FA=0; FR=5.85365852909e-07; selective risk=0.631578947368; validation loss=0.20000001; estimated cost=91.130919229 ms; separate old cost-inclusive diagnostic=0.200428693235.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.99999907317069}

- confidence_inflation: coverage=2.31707316777e-08; uncertainty=0.999999976829; FA=0; FR=0; selective risk=0; validation loss=0.199999995366; estimated cost=91.130919229 ms; separate old cost-inclusive diagnostic=0.2004286786.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.99999907317069, 'weak_or_conflicting_signal': 0.0}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=91.130919229 ms; separate old cost-inclusive diagnostic=0.200428683235.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.999999999999915, 'missing_achieved_coverage': 39.999999999999915, 'selected_execution_incomplete': 39.999999999999915}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## arithmetic / target 25%



Status: complete; maximum finalized clean coverage 82.5%; fixed budget 21258.335265022 ms.

Artifact: `build\multitask-uncertainty-sweep42\arithmetic\coverage-25\policy.json`; ID `0206b2b8b3cbfd45562008a2839bbd50987f8b5e2f7aeae1d0c5f78d8ef51c36`.

Probability on zero-clean-coverage strategies: 0.69696959326599317.

Worst-case validation loss: 0.286363646364.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['confidence', 'rule'] / reputation_weighted: p=0.3030301622895622; estimated team cost 21137.283848738 ms.

- ['evidence', 'rule'] / reputation_weighted: p=0.69696959326599317; estimated team cost 91.130921271 ms.

- ['rule', 'semantic'] / dependency_group: p=2.4444444457753958e-07; estimated team cost 49.276915003 ms.



Finalized scenarios:

- clean: coverage=0.25; uncertainty=0.75; FA=0; FR=0; selective risk=0; validation loss=0.15; estimated cost=6468.750048221 ms; separate old cost-inclusive diagnostic=0.180429240896.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 28.48484918855218, 'weak_or_conflicting_signal': 1.515150811447811}

- forced_support: coverage=0.287878770286; uncertainty=0.712121229714; FA=5.75757479461; FR=0; selective risk=0.49999994693; validation loss=0.286363615808; estimated cost=6468.750048221 ms; separate old cost-inclusive diagnostic=0.316792856704.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 28.48484918855218}

- forced_rejection: coverage=0.287878770286; uncertainty=0.712121229714; FA=0; FR=5.75757601684; selective risk=0.50000005307; validation loss=0.286363646364; estimated cost=6468.750048221 ms; separate old cost-inclusive diagnostic=0.316792887259.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 28.48484918855218}

- confidence_inflation: coverage=0.249999957222; uncertainty=0.750000042778; FA=0; FR=0; selective risk=0; validation loss=0.150000008556; estimated cost=6468.750048221 ms; separate old cost-inclusive diagnostic=0.180429249451.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 28.48484918855218, 'weak_or_conflicting_signal': 1.5151525225589237}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=6468.750048221 ms; separate old cost-inclusive diagnostic=0.230429240896.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.999999999999936, 'missing_achieved_coverage': 39.999999999999936, 'selected_execution_incomplete': 39.999999999999936}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## arithmetic / target 50%



Status: complete; maximum finalized clean coverage 82.5%; fixed budget 21258.335265022 ms.

Artifact: `build\multitask-uncertainty-sweep42\arithmetic\coverage-50\policy.json`; ID `e4981bb78a278f216efb0ece9b79eca8381fbaacdf6315e8bcb4cbc6bbb638f2`.

Probability on zero-clean-coverage strategies: 0.39393929023568991.

Worst-case validation loss: 0.372727282727.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['confidence', 'rule'] / reputation_weighted: p=0.6060604653198649; estimated team cost 21137.283848738 ms.

- ['evidence', 'rule'] / reputation_weighted: p=0.39393929023568991; estimated team cost 91.130921271 ms.

- ['rule', 'semantic'] / dependency_group: p=2.4444444528158352e-07; estimated team cost 49.276915003 ms.



Finalized scenarios:

- clean: coverage=0.5; uncertainty=0.5; FA=0; FR=0; selective risk=0; validation loss=0.1; estimated cost=12846.372147454 ms; separate old cost-inclusive diagnostic=0.160429812529.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 16.9696976734007, 'weak_or_conflicting_signal': 3.0303023265993243}

- forced_support: coverage=0.575757558165; uncertainty=0.424242441835; FA=11.5151505522; FR=0; selective risk=0.499999973465; validation loss=0.372727252172; estimated cost=12846.372147454 ms; separate old cost-inclusive diagnostic=0.433157064701.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 16.9696976734007}

- forced_rejection: coverage=0.575757558165; uncertainty=0.424242441835; FA=0; FR=11.5151517744; selective risk=0.500000026535; validation loss=0.372727282727; estimated cost=12846.372147454 ms; separate old cost-inclusive diagnostic=0.433157095256.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 16.9696976734007}

- confidence_inflation: coverage=0.499999957222; uncertainty=0.500000042778; FA=0; FR=0; selective risk=0; validation loss=0.100000008556; estimated cost=12846.372147454 ms; separate old cost-inclusive diagnostic=0.160429821085.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 16.9696976734007, 'weak_or_conflicting_signal': 3.03030403771044}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=12846.372147454 ms; separate old cost-inclusive diagnostic=0.260429812529.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.999999999999964, 'missing_achieved_coverage': 39.999999999999964, 'selected_execution_incomplete': 39.999999999999964}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## arithmetic / target 75%



Status: complete; maximum finalized clean coverage 82.5%; fixed budget 21258.335265022 ms.

Artifact: `build\multitask-uncertainty-sweep42\arithmetic\coverage-75\policy.json`; ID `202b675a7332e3aea7fd043f202efebc0cbab329a6576a157d03c06c2b7d1b5a`.

Probability on zero-clean-coverage strategies: 0.090908987205386718.

Worst-case validation loss: 0.459090919091.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['confidence', 'rule'] / reputation_weighted: p=0.90909076835016767; estimated team cost 21137.283848738 ms.

- ['evidence', 'rule'] / reputation_weighted: p=0.090908987205386718; estimated team cost 91.130921271 ms.

- ['rule', 'semantic'] / reputation_weighted: p=2.444444456065268e-07; estimated team cost 49.276915003 ms.



Finalized scenarios:

- clean: coverage=0.75; uncertainty=0.25; FA=0; FR=0; selective risk=0; validation loss=0.05; estimated cost=19223.994246686 ms; separate old cost-inclusive diagnostic=0.140430384162.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 5.454546158249164, 'weak_or_conflicting_signal': 4.545453841750838}

- forced_support: coverage=0.863636346044; uncertainty=0.136363653956; FA=17.2727263098; FR=0; selective risk=0.49999998231; validation loss=0.459090888535; estimated cost=19223.994246686 ms; separate old cost-inclusive diagnostic=0.549521272698.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 5.454546158249164}

- forced_rejection: coverage=0.863636346044; uncertainty=0.136363653956; FA=0; FR=17.272727532; selective risk=0.50000001769; validation loss=0.459090919091; estimated cost=19223.994246686 ms; separate old cost-inclusive diagnostic=0.549521303253.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 5.454546158249164}

- confidence_inflation: coverage=0.75; uncertainty=0.25; FA=0; FR=0; selective risk=0; validation loss=0.05; estimated cost=19223.994246686 ms; separate old cost-inclusive diagnostic=0.140430384162.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 5.454546158249164, 'weak_or_conflicting_signal': 4.545453841750838}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=19223.994246686 ms; separate old cost-inclusive diagnostic=0.290430384162.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 39.99999999999999, 'missing_achieved_coverage': 39.99999999999999, 'selected_execution_incomplete': 39.99999999999999}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## arithmetic / target 90%



Status: infeasible; maximum finalized clean coverage 82.5%; fixed budget 21258.335265022 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## semantic / target 0%



Status: complete; maximum finalized clean coverage 0.0%; fixed budget 15852.424223730 ms.

Artifact: `build\multitask-uncertainty-sweep42\semantic\coverage-00\policy.json`; ID `efcb6be9b6d46d34b923efbcb385cf24e226d9961fffc8baa3fa07ac94f5d027`.

Probability on zero-clean-coverage strategies: 1.

Worst-case validation loss: 0.2.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['rule', 'semantic'] / reputation_weighted: p=1; estimated team cost 42.432737484 ms.



Finalized scenarios:

- clean: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=42.432737484 ms; separate old cost-inclusive diagnostic=0.200267673492.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- forced_support: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=42.432737484 ms; separate old cost-inclusive diagnostic=0.200267673492.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- forced_rejection: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=42.432737484 ms; separate old cost-inclusive diagnostic=0.200267673492.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- confidence_inflation: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=42.432737484 ms; separate old cost-inclusive diagnostic=0.200267673492.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=42.432737484 ms; separate old cost-inclusive diagnostic=0.200267673492.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0, 'missing_achieved_coverage': 40.0, 'selected_execution_incomplete': 40.0}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## semantic / target 25%



Status: infeasible; maximum finalized clean coverage 0.0%; fixed budget 15852.424223730 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## semantic / target 50%



Status: infeasible; maximum finalized clean coverage 0.0%; fixed budget 15852.424223730 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## semantic / target 75%



Status: infeasible; maximum finalized clean coverage 0.0%; fixed budget 15852.424223730 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## semantic / target 90%



Status: infeasible; maximum finalized clean coverage 0.0%; fixed budget 15852.424223730 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## factual / target 0%



Status: complete; maximum finalized clean coverage 37.5%; fixed budget 15965.046464995 ms.

Artifact: `build\multitask-uncertainty-sweep42\factual\coverage-00\policy.json`; ID `3c2d2aa651a4630b501df56e9f232ecc171cc56f81d2d92e4b829957297f8e5e`.

Probability on zero-clean-coverage strategies: 1.

Worst-case validation loss: 0.2.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['evidence', 'rule'] / reputation_weighted: p=1; estimated team cost 188.903553752 ms.



Finalized scenarios:

- clean: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=188.903553752 ms; separate old cost-inclusive diagnostic=0.201183232095.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0, 'weak_or_conflicting_signal': 0.0, 'missing_achieved_coverage': 1.0}

- forced_support: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=188.903553752 ms; separate old cost-inclusive diagnostic=0.201183232095.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- forced_rejection: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=188.903553752 ms; separate old cost-inclusive diagnostic=0.201183232095.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0}

- confidence_inflation: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=188.903553752 ms; separate old cost-inclusive diagnostic=0.201183232095.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0, 'weak_or_conflicting_signal': 0.0, 'missing_achieved_coverage': 1.0}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=188.903553752 ms; separate old cost-inclusive diagnostic=0.201183232095.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.0, 'missing_achieved_coverage': 40.0, 'selected_execution_incomplete': 40.0}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## factual / target 25%



Status: complete; maximum finalized clean coverage 37.5%; fixed budget 15965.046464995 ms.

Artifact: `build\multitask-uncertainty-sweep42\factual\coverage-25\policy.json`; ID `c66e137fd64f61222e4a69cf0e025b91bc1d3ae075166743f2c795acd9d7cd79`.

Probability on zero-clean-coverage strategies: 0.33333333333333337.

Worst-case validation loss: 0.32.

Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):

- ['confidence', 'evidence'] / reputation_weighted: p=0.66666666666666663; estimated team cost 15921.255267484 ms.

- ['evidence', 'rule'] / reputation_weighted: p=0.33333333333333337; estimated team cost 188.903553752 ms.



Finalized scenarios:

- clean: coverage=0.25; uncertainty=0.75; FA=0; FR=0; selective risk=0; validation loss=0.15; estimated cost=10677.138029573 ms; separate old cost-inclusive diagnostic=0.216878214561.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 27.333333333333293, 'weak_or_conflicting_signal': 2.0, 'missing_achieved_coverage': 1.0}

- forced_support: coverage=0.316666666667; uncertainty=0.683333333333; FA=5.33333333333; FR=0; selective risk=0.421052631579; validation loss=0.27; estimated cost=10677.138029573 ms; separate old cost-inclusive diagnostic=0.336878214561.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 27.333333333333293}

- forced_rejection: coverage=0.316666666667; uncertainty=0.683333333333; FA=0; FR=7.33333333333; selective risk=0.578947368421; validation loss=0.32; estimated cost=10677.138029573 ms; separate old cost-inclusive diagnostic=0.386878214561.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 27.333333333333293}

- confidence_inflation: coverage=0.25; uncertainty=0.75; FA=0; FR=0; selective risk=0; validation loss=0.15; estimated cost=10677.138029573 ms; separate old cost-inclusive diagnostic=0.216878214561.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 27.333333333333293, 'weak_or_conflicting_signal': 2.0, 'missing_achieved_coverage': 1.0}

- suppression: coverage=0; uncertainty=1; FA=0; FR=0; selective risk=undefined (no decisions); validation loss=0.2; estimated cost=10677.138029573 ms; separate old cost-inclusive diagnostic=0.266878214561.

  Expected uncertainty reason counts (can overlap): {'minimum_contributors': 40.00000000000005, 'missing_achieved_coverage': 40.00000000000005, 'selected_execution_incomplete': 40.00000000000005}



Repeated-fit numerical equivalence: {'equivalent': True, 'matrix_atol': 1e-12, 'reputation_atol': 1e-12, 'probability_atol': 1e-12, 'relative_tolerance': 0.0}



## factual / target 50%



Status: infeasible; maximum finalized clean coverage 37.5%; fixed budget 15965.046464995 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## factual / target 75%



Status: infeasible; maximum finalized clean coverage 37.5%; fixed budget 15965.046464995 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## factual / target 90%



Status: infeasible; maximum finalized clean coverage 37.5%; fixed budget 15965.046464995 ms.

No PolicyArtifact or probability distribution created. Target not relaxed.



## Reference audit



Pairs chosen by first group in each partition, not by verifier success. Full raw metadata, independent labels and frozen task histories are in semantic-reference-audit.json.



### arithmetic / development / addition-307-503-correct

Question: What is 307 + 503?

Reference: 810

Candidate: 810

Independent correctness label: True (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.36212500721067314; decision: UNSURE; normalized abstention: True; uncalibrated vote strength: 0.0.

Compared text: What is 307 + 503? 810

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.64, 'n': 23}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.9761904761904762, 'n': 40}, {'verifier_name': 'confidence', 'mean': 0.8717948717948718, 'n': 37}]



### arithmetic / development / addition-307-503-incorrect

Question: What is 307 + 503?

Reference: 810

Candidate: 811

Independent correctness label: False (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.33843897010680235; decision: UNSURE; normalized abstention: True; uncalibrated vote strength: 0.0.

Compared text: What is 307 + 503? 811

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.64, 'n': 23}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.9761904761904762, 'n': 40}, {'verifier_name': 'confidence', 'mean': 0.8717948717948718, 'n': 37}]



### arithmetic / history / addition-328-536-correct

Question: What is 328 + 536?

Reference: 864

Candidate: 864

Independent correctness label: True (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.5308779495661211; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.5308779495661211.

Compared text: What is 328 + 536? 864

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.64, 'n': 23}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.9761904761904762, 'n': 40}, {'verifier_name': 'confidence', 'mean': 0.8717948717948718, 'n': 37}]



### arithmetic / history / addition-328-536-incorrect

Question: What is 328 + 536?

Reference: 864

Candidate: 865

Independent correctness label: False (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.5128555365415963; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.5128555365415963.

Compared text: What is 328 + 536? 865

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.64, 'n': 23}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.9761904761904762, 'n': 40}, {'verifier_name': 'confidence', 'mean': 0.8717948717948718, 'n': 37}]



### semantic / development / frame-Alex-correct

Question: Paraphrase this reference: Alex carried a parcel to the library.

Reference: Alex carried a parcel to the library.

Candidate: A parcel was carried to the library by Alex.

Independent correctness label: True (semantic frame preservation).

Raw cosine: 0.8843091327843677; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.8843091327843677.

Compared text: Paraphrase this reference: Alex carried a parcel to the library. A parcel was carried to the library by Alex.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.9629629629629629, 'n': 25}]



### semantic / development / frame-Alex-incorrect

Question: Paraphrase this reference: Alex carried a parcel to the library.

Reference: Alex carried a parcel to the library.

Candidate: Alex repaired a bicycle near the harbour.

Independent correctness label: False (semantic frame preservation).

Raw cosine: 0.7635674845846382; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.7635674845846382.

Compared text: Paraphrase this reference: Alex carried a parcel to the library. Alex repaired a bicycle near the harbour.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.9629629629629629, 'n': 25}]



### semantic / history / frame-Bailey-correct

Question: Paraphrase this reference: Bailey brought a basket to the station.

Reference: Bailey brought a basket to the station.

Candidate: A basket was brought to the station by Bailey.

Independent correctness label: True (semantic frame preservation).

Raw cosine: 0.8966010864224735; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.8966010864224735.

Compared text: Paraphrase this reference: Bailey brought a basket to the station. A basket was brought to the station by Bailey.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.9629629629629629, 'n': 25}]



### semantic / history / frame-Bailey-incorrect

Question: Paraphrase this reference: Bailey brought a basket to the station.

Reference: Bailey brought a basket to the station.

Candidate: Bailey repaired a bicycle near the harbour.

Independent correctness label: False (semantic frame preservation).

Raw cosine: 0.8171922839349361; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.8171922839349361.

Compared text: Paraphrase this reference: Bailey brought a basket to the station. Bailey repaired a bicycle near the harbour.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.5, 'n': 0}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.9629629629629629, 'n': 25}]



### factual / development / AO-correct

Question: What is the currency of Angola?

Reference: The currency of Angola is the Angolan kwanza.

Candidate: The currency of Angola is the Angolan kwanza.

Independent correctness label: True (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.9408068684505791; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.9408068684505791.

Compared text: What is the currency of Angola? The currency of Angola is the Angolan kwanza.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.9500000000000001, 'n': 38}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.7333333333333333, 'n': 13}]



### factual / development / AO-incorrect

Question: What is the currency of Angola?

Reference: The currency of Angola is the Angolan kwanza.

Candidate: The currency of Angola is the United States dollar.

Independent correctness label: False (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.8342057536290283; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.8342057536290283.

Compared text: What is the currency of Angola? The currency of Angola is the United States dollar.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.9500000000000001, 'n': 38}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.7333333333333333, 'n': 13}]



### factual / history / BE-correct

Question: What is the population of Belgium?

Reference: The population of Belgium is 11941781.

Candidate: The population of Belgium is 11941781.

Independent correctness label: True (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.9616148877440465; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.9616148877440465.

Compared text: What is the population of Belgium? The population of Belgium is 11941781.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.9500000000000001, 'n': 38}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.7333333333333333, 'n': 13}]



### factual / history / BE-incorrect

Question: What is the population of Belgium?

Reference: The population of Belgium is 11941781.

Candidate: The population of Belgium is 11954126.

Independent correctness label: False (independent arithmetic/source-snapshot answer correctness).

Raw cosine: 0.9497761764055327; decision: SUPPORT; normalized abstention: False; uncalibrated vote strength: 0.9497761764055327.

Compared text: What is the population of Belgium? The population of Belgium is 11954126.

Frozen task history: [{'verifier_name': 'semantic', 'mean': 0.5, 'n': 40}, {'verifier_name': 'evidence', 'mean': 0.9500000000000001, 'n': 38}, {'verifier_name': 'rule', 'mean': 0.5, 'n': 0}, {'verifier_name': 'confidence', 'mean': 0.7333333333333333, 'n': 13}]
