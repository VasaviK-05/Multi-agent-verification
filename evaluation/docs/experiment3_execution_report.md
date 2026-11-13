# Experiment 3 execution report

Empirical collection did not start. The experiment was not executed on the 372 Development groups. Final Test labels were not opened.

## What ran

- Corpus and eligibility audit: `evaluation/experiments/experiment3/corpus_audit.py`.
- Collection gate: `evaluation/experiments/experiment3/collection_gate.py`.
- Read-only export of the existing synthetic fixture: `evaluation/experiments/experiment3/export_synthetic_figures.py`.

A later collection-gate check returned the same state: `READY_FOR_APPROVAL`, `collection_started` false, recordings 0, costs unavailable, and reputation observations 0. The specification hash is still `f64b47cfe206548c57f60d48ebf2404dacce65b46ed05e4210fe68fb8250f529`. The settings proposal hash is `77d773fa7aad43bc0591244b64b78f37dd1142f2a9628d89ead7ad9847d8665f`. The corpus hash is still `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. No empirical figure directory was created.

## What did not run

Protocol approval, settings approval, corpus approval, dependency approval, and collection authorization are unsigned templates. Resource coefficient, verifier budget, cost unit, reputation initialization, and reputation update have no approved values. Model-weight snapshot hashes and the confidence generator digest are `UNKNOWN`. The collection seed is null.

No verifier was called. No Person 2 recording was created. No Person 3 policy was fitted. No Development loss, coverage, or interval was computed. The synthetic runner was not re-executed, because its source is missing and its bytecode imports dependency helpers that are not in the current `app.game.dependencies`.

## Dataset checks that did pass

Corpus SHA-256 `f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b`. CR bytes: 0. Unique sorted article IDs: 1,844. Index `idx-c1dc6980912b`. Index manifest, chunks, and FAISS hashes match the corpus approval template. Eligibility body SHA-256 matches `f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d`. Eligible groups: 372. Ineligible groups in the assignment file: 15, with no overlap. LF-normalized hashes of the eligibility outputs match the manifest. The working-tree JSONL files contain CR bytes and were not rewritten. Leakage clearance is `NOT_CLAIMED`.

Git commit observed during the audit: `65115a530d2939ecc35b7e214f4b32c3e800fab0`. Python 3.12.1. Platform `Windows-11-10.0.26300-SP0`. Hardware is `UNKNOWN`.
