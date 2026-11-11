# Research protocol readiness

## Current assessment

**Exploratory readiness: LIMITED. Confirmatory readiness: BLOCKED.** The readiness validator keeps missing or unapproved items blocked/not approved; data-file existence does not approve a protocol or enable evaluation.

The Development feasibility pilot is recorded as blocked before verifier execution because no adapter configuration was available. It produced no real verifier Attempts and no Offline Examples. Policy fitting remains disabled.

A provisional Final Test partition now exists at `evaluation/datasets/final_test_research_v1_eval_v1/`, with its separated label payload in `evaluation/datasets/_custodian/final_test_research_v1_v1/`. It has 1,319 groups per benchmark, benchmark-gold candidates only, and a passing exact leakage audit. Its status remains `NOT_AUTHORIZED`, `enabled: false`, and `PROVISIONALLY_FROZEN_AFTER_HASH_AND_AUDIT`. The label directory is Git-ignored but its Windows ACL inherits broad user read/modify access; no independent custodian exists. It is not genuinely protected and must not be used for confirmatory evaluation.

### Person 1 data readiness (2026-11-11)

The dataset side is validated: `python -m evaluation.data_preparation.person1_validation validate` reports 17 PASS, 0 FAIL, and 3 BLOCKED (Final Test custody, the unlocated "700 results", and policy-fitting readiness). The Development eligible roster (387 groups / 478 candidates), the ordered Person 2 and live-runtime rosters, the unresolved review queue, and the experiment input contracts exist in `evaluation/datasets/person1/research_v1_person1_v1/`. The full status is in `person1_compliance_matrix.md` and decision owners are in `person1_approval_checklist.md`. Data readiness does not change the overall assessment above. Experiments remain blocked on verifier Attempts (adapter configuration unset) and on approvals.

## Readiness checks

The machine-readable configuration is `evaluation/config/protocol_readiness.yaml`. The validator checks:

- Approved benchmark population and source versions.
- Candidate label policy, unresolved handling, label audit and limitations.
- Verifier eligibility by benchmark.
- Evidence corpus, index, retriever, embedding configuration and hashes.
- Loss, thresholds, resource budget, attack scenarios, metrics and outcome definitions.
- Statistical analysis plan, development pilot, sample-size justification, Attempts and Offline Examples.
- Policy-fitting readiness, Final Test partition/custody, and license/citation status.

Current requirements remain unapproved or unavailable, including source/license approval, verified negative labels, verifier settings and Attempts, statistical plan and sample-size justification, independent custody, and confirmatory method approvals. The Final Test contains zero verified incorrect candidates, so it cannot estimate false-acceptance performance from its labels.

## Human decisions still required

An accountable protocol owner must approve the benchmark/source population, source licenses/citations, candidate/label policy, verifier eligibility, loss/threshold/resource settings, attack scenarios, metrics, and statistical analysis plan. A sample-size justification must use approved effect-size and uncertainty assumptions; the current 1,319-per-benchmark allocation is a provisional operational allocation, not a power result. A named independent custodian must establish and verify an OS-enforced label boundary and access log. Confirmatory evaluation requires explicit approval after these dependencies are met.

Run the validator with:

```powershell
.\.venv\Scripts\python.exe -m evaluation.data_preparation.final_test_workflow readiness --config evaluation/config/protocol_readiness.yaml --manifest evaluation/datasets/_custodian/final_test_research_v1_v1/manifest.json
```
