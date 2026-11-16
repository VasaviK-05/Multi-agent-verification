# Readiness and outstanding items

| Deliverable | Status | Evidence | Missing requirement |
| --- | --- | --- | --- |
| Direct-arithmetic task support | PARTIAL | Rule path is `VERIFIED` for one explicit expression. Test named in [01_task_support.md](01_task_support.md). | No approved population, rubric, or annotation. GSM8K word problems are outside that path. |
| Direct-factual task support | PARTIAL | Rule patterns are `PARTIALLY_VERIFIED`. Semantic and evidence are partial signals. | Not general factual verification. HotpotQA is a different population. Confidence is `UNKNOWN` for `direct_facts`. |
| Verifier source hashes | COMPLETE | All four source SHA-256 values match `evidence/verifier_config.json`. | The config is still `DECLARED_PENDING_APPROVAL`. A source hash is not a model-weight pin. |
| Model, prompt, and weight hashes | PARTIAL | Names and the confidence prompt hash are recorded. | Semantic, evidence, and embedding weight hashes are `UNKNOWN`. Evidence prompt hash is `UNKNOWN`. Confidence generator digest is `UNKNOWN`. No prompt file is bound to the confidence hash. |
| Evidence corpus and index | PARTIAL | Corpus, index, chunk, and FAISS hashes are in `evidence/evidence_corpus_manifest.json`. | Manifest status `PROPOSAL_NOT_APPROVED`. Embedding-weight snapshot `UNKNOWN`. |
| Approved Development manifest | COMPLETE | `evidence/development_eligibility_manifest.json`: 372 groups, 744 candidates, research-lead approval 2026-11-13. | Approval does not authorize collection, recording, or Final Test. Labels remain provisional and synthetic. |
| Development group and candidate ids | COMPLETE | `evidence/development_group_assignments.jsonl` and `evidence/development_eligible.jsonl`. | The sidecar hash file does not match the current manifest bytes. |
| Approved History manifest | MISSING | Exploratory counts only, in `evidence/exploratory_dataset_manifest.json`. | No approved History eligibility manifest. Do not treat the exploratory file as approved. |
| Verifier cost calibration | PARTIAL | Freeze id `cc7e7ca8882f602b9854bf21b80b8a7bf70f6c70d05ccd12787322a84a12477d`. Experiment 3 and Experiment 1 share it. | Freeze authorizes measurement freezing only. It does not authorize policy fitting or budget selection. Model weights for the timed runs are not pinned. |
| Final Test v2 self-custody | UNVERIFIED | Appointment, location, access log, and self-custody JSON are in `evidence/`. | Independent custody is false. Scoring fields contradict each other. No signature. Label bytes were not rechecked. |
| Dated protocol amendment | PARTIAL | `evidence/final_test_protocol_amendment.json`, date 2026-11-13, before the Experiment 3 collection. | Research-lead approval is `PENDING`. Study configuration, policies, baselines, and evaluation rules are not frozen. |

## How to read the statuses

Implementation evidence is the verifier code, tests, source hashes, and copied manifests. Approved research artifacts are the Development eligibility decision and the cost-calibration freeze, each inside the scope written on that artifact. Pending governance is every `approved: false` record, the null signatures, and the `PENDING` research-lead fields. Sealed Final Test metadata is the manifest, roster, location, and access log. It is not the label file.

## Outstanding decisions

1. Research-lead approval of the 2026-11-13 custody amendment, with a signature and a date.
2. A protocol hash and a real freeze of study configuration, policies, baselines, and evaluation rules.
3. An independent custodian who is not the dataset creator, or a continued public statement that independent custody does not exist.
4. A scoring decision that does not contradict the seal. The current nested `scoring_authorized: true` is unsigned and is not that decision.
5. Human adjudication if `SYNTHETIC_INCORRECT` is to be treated as verified incorrect.
6. An approved History eligibility manifest, if History is going to be used. None exists now.
7. Pinned model-weight digests and an evidence prompt hash.
8. A corrected eligibility sidecar, written as a new recorded action. This package leaves the stale sidecar in place.

Until those exist, teammates can rely on the Development roster and the cost measurements for their stated scopes. They cannot treat Final Test as releasable, History as approved, or the verifier models as hash-pinned.
