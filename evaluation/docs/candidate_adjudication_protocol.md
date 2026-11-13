# Independent candidate adjudication protocol

## Purpose and scope

This workflow resolves candidate correctness independently of the multi-agent validation framework. It starts from the existing unified GSM8K and HotpotQA candidate records in History, Development, and the already exposed `final_test` file. It does not generate splits, edit source datasets, or inspect framework results. The current workspace's final-test identities are already exposed; this workflow does not make them protected or unseen.

## Status definitions

- `verified_correct`: supported by the benchmark's canonical answer or independent review evidence under the approved rubric.
- `verified_incorrect`: independent review establishes that the candidate does not answer the target question under the approved rubric.
- `unresolved`: insufficient evidence, ambiguity, disagreement awaiting resolution, or no independent review.

Source integrity is recorded separately. A candidate/source mismatch is an integrity problem and is not automatically a verified incorrect answer. The original `expected_correct` value is retained as an unverified construction annotation.

## Workflow and files

Run from the repository root:

```text
.venv\Scripts\python.exe evaluation\data_preparation\candidate_adjudication.py prepare
```

Outputs are isolated in `evaluation/datasets/adjudication/v1/`:

- `gsm8k_adjudications.jsonl` and `hotpotqa_adjudications.jsonl`: source-linked records, current status, provenance, evidence, and rationale fields.
- `gsm8k_blinded_review_queue.jsonl` and `hotpotqa_blinded_review_queue.jsonl`: first-pass reviewer inputs. They do not expose `expected_correct`, candidate construction source, or benchmark gold answer. The GSM8K queue omits the worked solution; HotpotQA includes the supplied reference context and supporting facts.
- `manifest.json`: source-file hashes, protocol version, and preservation notice.
- `statistics.json`: benchmark-wise, partition-wise, and combined counts.

The prepare command refuses to write into a non-empty output directory unless `--resume` is supplied. Resume regenerates source-derived fields while preserving existing adjudication decisions by stable candidate ID. It errors if candidate identities have changed.

Reviewers append decisions to a separate UTF-8 JSONL file and apply them with:

```text
.venv\Scripts\python.exe evaluation\data_preparation\candidate_adjudication.py apply --decisions path\to\decisions.jsonl
```

Each decision row must use `candidate_id`, `adjudication_status`, `adjudication_method`, `adjudication_provenance`, `adjudication_rationale`, `adjudication_evidence`, and at least two `reviewer_decisions` containing independent reviewer IDs and decisions. If reviewers disagree on a resolved status, include an `adjudicator` and use `third_party_adjudication`. The apply step rejects missing evidence, unsupported methods/statuses, duplicate or unknown candidate IDs, and incomplete reviewer records. Decisions can be applied incrementally; reapplying a candidate ID replaces that candidate's existing adjudication record and the output statistics are recomputed.

## GSM8K review procedure

The automatic check parses the benchmark `####` answer into `Decimal` and compares canonical numeric values, removing grouping commas and a leading dollar sign. This avoids treating `1,000`, `1000`, and `1000.0` as different numeric values. It does not infer units, acceptable rounding, fractional or spelled-number equivalence, or what alternate interpretation the word problem permits.

For each candidate, two reviewers independently solve from the question without seeing the benchmark worked solution, expected label, or construction source. They record their numeric result, units, rounding/tolerance rule, derivation, and ambiguity. Then compare candidate and benchmark answers using the approved normalization rubric. Resolve disagreement with a third reviewer; otherwise leave unresolved. Benchmark-gold matches may be marked `verified_correct` by source matching, clearly distinguished from a fresh independent re-solution.

## HotpotQA review procedure

Two reviewers independently assess whether the candidate answers the target question. In the reference-assisted protocol they may use the target's supplied context and supporting-fact annotations, which are included in the review queue. Record the exact paragraph title/sentence or independently sourced reference supporting the decision. Consider aliases, semantic equivalence, answer scope, comparison/multi-hop requirements, ambiguity, and whether the supplied evidence is sufficient. A borrowed answer appearing as a substring in context is not proof of correctness. If evidence is absent, contradictory, or inadequate, leave the candidate unresolved. Resolve disagreements through a documented third-party decision.

The current source builder does not retain the donor ID for borrowed answers. Do not infer the donor row from value matches; record missing donor provenance until it can be reproduced from an immutable source-order receipt.

## Evidence and audit trail

For every independent decision record method, rubric version, reviewer roles/IDs, provenance, evidence references or derivations, rationale, timestamp, and disagreement resolution. Evidence should identify a GSM8K derivation/source answer or a HotpotQA supporting paragraph/fact and source version. A verifier's prediction or output is not admissible adjudication evidence.

Automated statuses presently cover only benchmark-gold source matches. Synthetic GSM8K and borrowed HotpotQA candidates start unresolved. Construction labels remain visible only in the full audit record; blinded reviewers must work from the separate review queue.

## Limitations and safeguards

This workflow does not automatically establish synthetic-negative correctness, semantic equivalence, or factual falsity. Review quality depends on the approved rubric, reviewer competence, and evidence. Human decisions must not be fabricated or inferred from missing labels. Output files are new versioned artifacts; never overwrite source datasets, existing results, or the existing partition files. No new train/development/final-test split is produced here.
