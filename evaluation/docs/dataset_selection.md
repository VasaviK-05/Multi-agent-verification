# Dataset selection recommendation

## Recommendation

Use **GSM8K as the arithmetic population**, after a development-only candidate audit and with the limitation that existing rule verification supports narrow/direct arithmetic patterns rather than the full word-problem distribution. Consider a separately labeled direct-arithmetic stratum only if the team defines and validates a deterministic classifier or manual annotation protocol before splitting. Existing data have no direct-arithmetic flag, so no direct-arithmetic count is claimed.

Use **HotpotQA as a factual question-answering population only for a reference-assisted condition** unless a frozen configured corpus with adequate supporting evidence is selected and verified. The existing shared corpus has virtually no supporting-page coverage. The supplied HotpotQA contexts contain reference material and supporting-fact annotations, making it the strongest of the available factual QA sources for a reference-assisted interface-compatible condition. Every method must get the same permitted paragraphs. The current synthetic negative candidate needs independent adjudication.

Treat **FEVER as an optional separate claim-verification task**, not as ordinary question-answer validation. It has independent SUPPORTS/REFUTES/NOT ENOUGH INFO labels, but the present adapter puts the claim in both question and candidate answer and supplies no evidence text. Direct title checks find no FEVER cited title in the configured corpus. NOT ENOUGH INFO is an abstention/unknown-evidence class and must not be converted into a false candidate. Include FEVER only if the team accepts this task mapping and chooses an evidence condition that is explicit and shared.

Do not force **MultiNLI** into the answer-validation interface. Its labels concern premise-hypothesis entailment, not answer correctness for a question.

## Observed scale and suitability

| Dataset | Local source size | Existing unified sample | Candidate construction | Interface/evidence fit |
|---|---:|---:|---|---|
| GSM8K | 7,473 train; 1,319 test | 2,000 history, 500 development, 500 final-test questions | Gold numeric answer plus gold+1 synthetic candidate | Fits question/answer interface; no reference text; candidate negative needs validation. |
| HotpotQA distractor | 90,447 train; 7,405 validation | 2,000/500/500 questions | Gold answer plus another question's gold answer | Fits question/answer interface; reference context available; shared corpus lacks supporting pages for nearly all sampled questions. |
| FEVER v1.0 | 311,431 train rows; 18,999 paper-dev rows; 18,567 paper-test rows (annotation rows before grouping) | 2,000/500/500 unique claims | One claim with benchmark label; no correct/incorrect candidate pair | Claim-verification task; referenced evidence text absent; 0 sampled titles overlap configured corpus. |
| MultiNLI | 392,702 train; 9,815 matched validation; 9,832 mismatched validation | 2,000/500/500 | No answer candidates | Not compatible with this interface. |

The “existing unified sample” is not endorsed as a final selection or split. Its samples are audit material and the present final-test file is already locally exposed.

## Candidate-quality conditions

GSM8K gold answers are derived from the benchmark's final-answer marker. The existing wrong answer is a numeric increment, not a naturally generated or independently adjudicated error. Validate numeric equivalence, units, formatting and whether the problem admits the candidate through a different interpretation. If any item is ambiguous, record it and exclude only under a predeclared exclusion rule with a reason; do not silently discard it.

HotpotQA gold answers are benchmark labels. The cross-example negative is a heuristic only: it may be correct by coincidence, be a valid alias, or be compatible with a broad question. Independently verify every proposed negative against the gold reference and permitted context; store annotator/reviewer, adjudication, and provenance. Candidate correctness should be attached to each question-answer pair.

## Computational feasibility

The existing baseline contains 1,232 completed records and demonstrates that selected batches have been processed. It does not establish the cost of the game-theoretic protocol. Begin with a Development pilot, record wall time and attempt count, estimate per-example cost, then approve a sample size and method budget. Do not infer a universal split ratio from the current 2,000/500/500 files.

## Decisions before final inclusion

Approve benchmark populations and task mapping; decide corpus-only versus reference-assisted factual evaluation; independently adjudicate negative candidates; define direct-arithmetic labeling if used; define exclusion and group rules; and reserve a new, protected final-test pool. Until then, neither benchmark is ready as a final research dataset.
