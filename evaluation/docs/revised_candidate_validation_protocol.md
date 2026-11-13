### Rationale for Subset-Based Candidate Validation

The initial candidate-adjudication pilot was designed to assess the feasibility and consistency of a manual review protocol using 30 GSM8K and 30 HotpotQA generated candidates. However, the pilot is a procedural assessment and does not establish the correctness of the remaining candidate population. Extending manual adjudication to all 6,000 generated candidates would require substantial annotation effort and introduce a scalability limitation, particularly given the availability of only one human reviewer.

Furthermore, the two benchmarks require different forms of correctness assessment. GSM8K candidates require independent mathematical verification, whereas HotpotQA candidates require question-conditioned factual assessment against supporting context. Applying a single manual-review process to both populations would not necessarily provide consistent or equally reproducible ground-truth labels.

Therefore, this study adopts a subset-based candidate-validation strategy. A reproducibly selected subset of benchmark examples will be used to construct an evaluation population containing candidates whose correctness can be established through independent arithmetic verification or benchmark-grounded factual evidence. Candidates for which correctness cannot be established will remain unresolved and will be excluded from primary binary correctness metrics.

This approach prioritizes ground-truth reliability, experimental comparability, and reproducibility over raw evaluation-set size. All competing verification strategies will be evaluated on the same eligible examples under identical experimental conditions. The subset selection procedure, validation method, label provenance, and exclusions will be documented to reduce selection bias and support reproducibility.

The resulting findings will be interpreted within the scope of the validated evaluation population. They will not be presented as evidence of performance across the entire original benchmark population unless supported by additional evaluation.
