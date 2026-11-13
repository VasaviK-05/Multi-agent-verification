# Candidate-answer adjudication pilot v3

## Purpose

The readiness audit found 3,000 unresolved GSM8K synthetic candidates and 3,000 unresolved HotpotQA borrowed candidates. `expected_correct: false` records how an alternative was generated; it is not independent evidence that it is wrong. A benchmark gold answer establishes the canonical benchmark answer but does not prove that every alternative is semantically incorrect. Alternatives may be equivalent, valid under another interpretation, or coincidentally correct.

This 60-candidate pilot is intended to check whether one reviewer can apply the process consistently and record sufficient evidence. It is not a benchmark performance evaluation. No decisions have been entered and no adjudication or consistency check is claimed complete.

## Selection and preservation

The fixed selection remains the original 30 GSM8K and 30 HotpotQA candidates selected with seed **20261102**. The partition distribution is unchanged:

| Dataset | History | Development | Final Test | Total |
|---|---:|---:|---:|---:|
| GSM8K | 26 | 4 | 0 | 30 |
| HotpotQA | 22 | 8 | 0 | 30 |
| **Total** | **48** | **12** | **0** | **60** |

All candidate IDs are retained. The pilot still excludes Final Test. The single-reviewer schema backup is `evaluation/datasets/adjudication/pilot_v3/schema_backup_two_reviewer_20261102/`; it contains the pre-change template and queue JSONL files, including the previous reviewer-specific copies. Original datasets and pilots v1/v2 were not changed.

## One-reviewer procedure

There is one human reviewer and one initial review per candidate. The decision template and queues use these fields:

- `reviewer_id`
- `adjudication_status`: `verified_correct`, `verified_incorrect`, or `unresolved`
- `adjudication_evidence`
- `adjudication_provenance`
- `adjudication_rationale`

An empty status with null reviewer ID and empty evidence fields means pending. Do not add or populate a second reviewer. The optional `adjudicator` field is reserved for exceptional later review or audit; it does not imply a second initial reviewer. If it is used, preserve the original decision and record the adjudicator's identity, decision, evidence, provenance, and rationale separately.

### GSM8K

Independently solve the arithmetic problem and record the answer, units, derivation, and any ambiguity before consulting the supplied benchmark worked solution. Then compare the candidate with the independently obtained result under the stated interpretation. A `gold + 1` construction alone is not grounds for `verified_incorrect`.

### HotpotQA

Assess whether the borrowed answer answers the target question using the supplied context and supporting facts. Consider aliases, scope, multi-hop requirements, and ambiguity. A substring match is not proof. If context is insufficient or the answer is ambiguous, choose `unresolved`. The source builder did not retain the donor ID; it remains null and is not inferred.

## Intra-reviewer consistency check

After all 60 initial reviews are complete, create a separate second-review sample of 15 candidates. The fixed default seed is **20261103**. Sample without replacement from candidate IDs in sorted order, stratifying to **8 GSM8K and 7 HotpotQA**. The second-review queue includes question/candidate/reference information but omits all initial decisions, evidence, provenance, and rationale. The same reviewer completes the second review without seeing their first decision. Save second-review decisions in a separate file; never overwrite the initial decisions.

Once all 15 second reviews are complete, calculate exact categorical agreement (`adjudication_status` matches exactly) and disagreement counts and rates. Report transition counts between initial and second statuses. This measures **intra-reviewer consistency**, not inter-reviewer agreement or accuracy. A disagreement identifies a case requiring reconsideration or a clearer rubric; it does not determine which decision is correct.

From the repository root, after recording all initial decisions in a copy of the template:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\create_candidate_adjudication_pilot_v3.py validate --pilot-dir evaluation\datasets\adjudication\pilot_v3 --decisions-file path\to\completed_initial_decisions.jsonl
.\.venv\Scripts\python.exe evaluation\data_preparation\create_candidate_adjudication_pilot_v3.py prepare-consistency --pilot-dir evaluation\datasets\adjudication\pilot_v3 --initial-decisions path\to\completed_initial_decisions.jsonl --seed 20261103 --output-dir evaluation\datasets\adjudication\pilot_v3\consistency_check_seed_20261103
```

Complete the resulting `second_review_queue.jsonl`, save it as `second_review_decisions.jsonl` in that consistency directory, then calculate agreement into a new report file:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\create_candidate_adjudication_pilot_v3.py analyze-consistency --initial-decisions path\to\completed_initial_decisions.jsonl --second-decisions evaluation\datasets\adjudication\pilot_v3\consistency_check_seed_20261103\second_review_decisions.jsonl --consistency-manifest evaluation\datasets\adjudication\pilot_v3\consistency_check_seed_20261103\consistency_manifest.json --output evaluation\datasets\adjudication\pilot_v3\consistency_check_seed_20261103\consistency_results.json
```

The initial and second decision inputs must each contain the appropriate required reviewer/evidence/provenance/rationale fields. Commands refuse to overwrite non-empty consistency outputs or existing reports.

## Validation and limitations

Run the pilot validator with:

```powershell
.\.venv\Scripts\python.exe evaluation\data_preparation\create_candidate_adjudication_pilot_v3.py validate --pilot-dir evaluation\datasets\adjudication\pilot_v3
```

It checks exactly 60 unique candidate IDs, the original benchmark and partition counts, zero Final Test rows, one pending decision per candidate, absence of second-reviewer fields, allowed decision values, and required evidence/provenance/rationale on completed decisions. Consistency commands separately require all 60 initial reviews and all 15 second reviews to be complete and preserve the initial file.

The pilot cannot establish population-wide label quality. Full adjudication remains necessary for the unresolved candidates, and ambiguous or under-evidenced cases should remain unresolved. The evaluated multi-agent framework must not be used as the correctness judge.
