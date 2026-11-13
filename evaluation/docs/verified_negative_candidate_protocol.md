# Controlled negative-candidate protocol v1

## Purpose and scope

This artifact is a small, controlled corruption set for validating whether answer-validation methods detect deliberately incorrect responses. It is not a sample of naturally occurring model errors, does not estimate benchmark error prevalence, and is not one of the four main research experiments. The source population is the existing verified subset v1, restricted to History and Development. Final Test records were not read or included.

The implementation is `evaluation/data_preparation/build_verified_negative_candidates.py`. It reads `evaluation/datasets/verified_subset/v1_seed_20261104/` and the GSM8K raw **train** split only. It does not load the unified Final Test file, GSM8K test, or HotpotQA's mixed raw validation split. It refuses to write into a non-empty output directory.

## Selection and provenance

The fixed seed is `20261105`. Eligible rows are source-linked, benchmark-gold candidate records marked `verified_correct` in verified subset v1. Sampling is without replacement from sorted source IDs, using separate deterministic seeds per benchmark and partition. The target is 40 History and 10 Development questions for each benchmark, up to 50. Selected IDs, partition membership, source paths, and SHA-256 hashes are in `evaluation/datasets/verified_negative_candidates/v1/manifest.json`.

The observed selection is 50 GSM8K and 50 HotpotQA questions: 40 History and 10 Development per benchmark. Selected related-group IDs were checked against the v1 source records; all selected groups were unique within each benchmark. No source rows were removed or relabeled.

## GSM8K construction and verification

The eligible population is restricted to questions that request a discrete count using “how many,” have an exact integer source answer, and do not contain rounding, approximation, percentage, ratio, probability, fraction, or “how many times” cues. The raw train question and worked solution are matched to the existing subset source ID. The builder independently recomputes every tagged arithmetic equation using exact rational arithmetic, then checks that the final-answer marker and last checked equation equal the benchmark answer. Incomplete or failed replays are excluded from candidate selection.

The controlled alternative is exactly one integer unit above the established count (`gold + 1`). Exact rational normalization is used to confirm it is numerically distinct; the transformation itself is not used as the validation procedure. The incorrectness claim is conditional on the question's discrete-count interpretation and the benchmark's unique exact answer. This narrow eligibility rule avoids claiming that a numerical change is wrong where units, acceptable rounding, fractions, or alternative representations could make the issue ambiguous. The generated alternative is not a natural language answer and does not model realistic solver errors.

## HotpotQA construction and verification

The eligible population is restricted to concise gold answers of two to five normalized content tokens, excluding yes/no answers and questions with obvious alternative/uncertainty cues. The canonical answer phrase must occur as a contiguous token sequence in a supplied context paragraph linked to a supporting-fact title/sentence reference. The output stores the exact supplied paragraph text, title, sentence ID, source path, supporting-fact references, and paragraph hash.

The controlled alternative explicitly denies the benchmark answer (for example, “The answer is not [gold answer].”). The validation basis is the source-linked benchmark answer plus the cited benchmark-context paragraph that supports the canonical answer; a string mismatch alone is never used. This is an evidence-assisted, constructed contradiction condition. It is **not** retrieval from the project's shared 13,083-article corpus and does not establish shared-corpus retrieval performance. Paragraph-level context and sentence-ID provenance are retained; the source subset does not provide reliably extracted support sentence text for every reference. If the context or answer semantics do not support an unambiguous contradiction, that example is not eligible and should be unresolved in any broader adjudication.

## Observed outputs

| Benchmark | Generated | Verified incorrect | Unresolved | History | Development |
|---|---:|---:|---:|---:|---:|
| GSM8K | 50 | 50 | 0 | 40 | 10 |
| HotpotQA | 50 | 50 | 0 | 40 | 10 |

These status counts describe the deterministic construction and verification rules above. They are not human adjudication results. The framework under evaluation was not used as a correctness judge. The existing verified subset v1, original benchmarks, adjudication records, and experiment results were not modified.

## Reproduction and validation

From the repository root, build a new empty output directory with:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_verified_negative_candidates.py build --seed 20261105
```

Validate the generated files without rebuilding them with:

```powershell
.\.venv\Scripts\python.exe evaluation/data_preparation/build_verified_negative_candidates.py validate
```

The validator checks allowed partitions/statuses, unique candidate and source IDs, required provenance and evidence, complete GSM8K arithmetic replay, the declared HotpotQA negation/evidence condition, manifest ID consistency, and that unresolved rows are not counted as incorrect. It does not open Final Test. The actual run passed these checks; details are recorded in `validation_summary.json`.

## Limitations and next steps

1. The GSM8K set is deliberately narrow and may overrepresent simple exact-count questions.
2. GSM8K verification replays benchmark worked equations; it does not independently solve each problem from first principles or provide human review.
3. HotpotQA candidates are explicit negations of benchmark answers, not naturally generated distractors. Their support is drawn from supplied benchmark context, not the shared retriever.
4. The HotpotQA source context retains support paragraphs and references, but some references are paragraph-level rather than extracted sentence-level evidence.
5. The selected counts do not justify broad performance claims. Before main experiments, freeze the condition definitions, ensure all comparison methods receive the same allowed context, review evidence sufficiency, and keep Final Test protected.

No main research experiment was run as part of this preparation.
