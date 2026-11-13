# Experiment 3 team data requirements

Empirical collection is blocked until the research lead signs the records below against the current file hashes. A signature needs an approver and a date. This repository does not supply either.

## Research lead

1. Accept or replace the proposed settings in `evaluation/config/experiments/experiment3_settings_proposal.json`, hash `77d773fa7aad43bc0591244b64b78f37dd1142f2a9628d89ead7ad9847d8665f`. The unsigned settings template is `evaluation/config/experiments/approvals/experiment3_settings_approval_record.json`. Copy the accepted numbers, including a resource coefficient and one budget in Person 2's cost unit, into `approved_settings` on `experiment3_protocol_approval_record.json` and sign that record against specification `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`.
2. Sign `experiment3_corpus_approval_record.json` against corpus `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. A freeze requires `freeze_status` `FROZEN` on that signed record. The recorded limitations stay attached.
3. Sign `experiment3_dependency_approval_record.json` against `experiment3_dependency_configuration.json` hash `c7dc14f867bedd8345184869fa8c10f7fabb554d843ed44df4d8606e993d7c2d`. State whether hypothetical heatmap rows are in scope. That signature is not a measured-dependence claim.
4. Sign `experiment3_collection_authorization_record.json` only after the three records above. Its artifact hash is `6f539d60464d684e9633b102f8b06ae6f598c5c4035e0d34f7e8a8d8be3adcda`.

## Person 1

The approved eligibility manifest is unchanged: 372 eligible groups and 744 eligible candidates. No further roster edit is required for this experiment. Do not open Final Test labels. Do not rebuild the corpus unless a signed decision says the current hash is wrong. The current hash matches.

## Person 2

The empty recording schema is `evaluation/experiments/experiment3/collection_recording_schema.json`. It contains no rows. After collection authorization, supply the missing collection fields and the recordings. Required before `READY_FOR_DEVELOPMENT_COLLECTION`: model-weight snapshot hashes, prompt hashes, the rule version hash, hardware, software lock, code revision, random seed, timeout, retries, and warmup. Required with the recordings: question and group ids from the approved roster, benchmark, candidate id, gold provenance, attack condition, verifier reports, confidence, evidence citations, execution status, attempt count, runtime and cost in a named unit, timeout or failure detail, and configuration hashes. Do not impute failures. Do not send Final Test attempts.

The resource coefficient and the single matched verifier budget stay empty until that cost unit exists.

## Person 3

After the recordings and the approved loss settings exist, export the reputation policy. Choose initialization, the update rule, and smoothing. Observations are currently 0. The synthetic fixture is not a reputation source. Development outcomes are not a reputation source.

`evaluation/experiments/experiment3/collection_gate.py` refuses to start collection while those records are absent.
