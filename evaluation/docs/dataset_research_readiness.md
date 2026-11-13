# Dataset research readiness

## Canonical roster

Development eligibility `research_v1_exploratory_eligibility_approved_v1` is approved for eligibility only. Body SHA-256 `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. Counts: 744 candidates, 372 groups, GSM8K 187 and 187, HotpotQA 185 and 185. Fifteen groups were quarantined for shared context. Collection and Final Test remain unauthorized.

The pre-quarantine exploratory HotpotQA Development count was 200. The built `research_v1` population also has 200 HotpotQA Development groups and 400 Development groups in total. Those figures describe earlier artifacts. They are not the approved eligibility roster.

## Unified files

The unified files still contain History 8,000, Development 2,000, and Final Test 2,000, with 500 Development rows each of FEVER, GSM8K, HotpotQA, and MultiNLI. FEVER and MultiNLI are not the approved research population. The unified Final Test file is the older exposed partition, not Final Test v2.

The provenance-aware subset `v1_seed_20261104` remains 100 questions and 200 candidates per benchmark, 80 History and 20 Development. Its combined labels are 191 verified correct, 0 verified incorrect, and 209 unresolved. It is not the canonical roster.

## Labels

`VERIFIED_CORRECT` on the eligibility roster is a recorded validation class. `SYNTHETIC_INCORRECT` is not `HUMAN_VERIFIED_INCORRECT`. This package does not adjudicate the 3,000 unresolved GSM8K candidates or the 3,000 unresolved HotpotQA candidates in the older full overlay, and it does not turn unresolved rows into verified labels.

`evaluation/scripts/audit_research_datasets.py` recomputes unified counts, checks the eligibility manifest, and counts identifier overlap with the sealed Final Test manifest. It prints the overlap count only.

Broader dataset approval is `PENDING` in `evaluation/config/research_v1/dataset_approval_package.json`. That file does not replace the existing eligibility approval and does not authorize collection.
