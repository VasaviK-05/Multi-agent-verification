# Factual feasibility pilot — DRAFT, UNAPPROVED

Historical six-row draft, not approval. The latest separate proposal and seven-team
feasibility analysis are in [the factual team-selection handoff](../factual-team-selection-v1/README.md).
JSON labels, reservations, resource receipts and reports mentioned below remain local-only
and are not included in Git. Source publication authorizes no collection or fitting.


Use the repository's ten existing factual question/answer/reference rows with all
four real verifiers and the fixed ten-article test corpus. Proposed use is local
internal feasibility evaluation; the dataset owner must confirm permitted use.
This is a tiny reference-assisted pilot, not evidence for the full research claim.

**Data:** eight related-topic groups. Keep France/Paris together and AI/ML together;
future paraphrases/alternative answers stay in the same group. With seed 20261026,
propose two history groups (three examples), three development groups (three examples)
and three final groups (four metadata-only entries). The custodian must approve
grouping and witness the reservation. No final labels or reports were created/accessed.

**Labels:** six preparation answers have source-grounded proposed `true` labels,
supported by Berlin government, IBM, PSF, Delhi government and NIST sources in
[the label audit](label-review.draft.json). These are unapproved source comparisons,
not benchmark-flag reuse or framework verdicts. Definitions need explicit rubric
review. All six are positive; false-accept behavior cannot be estimated from them.

**Settings proposed for review:** one pass, no warmups/repeats; retain first-attempt
effects inside the existing timer. Keep five confidence samples, temperature 0.8
and existing per-request generation seeds 0..4. Propose losses 1/1/0.2 for false
accept/false reject/uncertainty, Beta prior 1/1, threshold 0.55, and existing minimum
two participants. Use offline `report_corruption_v1` with unavailable suppression,
shared model dependencies and conservative `shared_unknown` for all four candidates.
Retain every feasible team and both aggregations. **Budget and resource weight stay
undecided until measured millisecond costs exist.**

**Local preparation completed:** built a separate index of 10 chunks from 216 corpus
words using the cached embedding, produced a genuine receipt and verified the old
index remained unchanged. Resource-only preflight passes. No downloads or verifier
attempts ran. **Work to authorize next:** full recording of 24 verifier attempts,
up to 30 local generations and 100 local metadata GET requests. Observer hashing
reads approximately 33.5 GB of model-file bytes logically; caching may reduce disk
I/O. Generation timeouts sum to 1,800 seconds, not a runtime forecast. Initialization,
NLI and hashing add overhead; peak memory and monetary cost are not estimated.

**Limits before fitting:** the current evidence probe still fails three contract
tests. Four preparation rows have unknown analyzer requirements; the six rows cannot
be exported under one current context. All captured outputs are preserved. A
two-example Germany/India factual cohort is technically homogeneous but requires
an explicit scope amendment and evidence repair. No arithmetic pilot is substituted.

Prepared files and exact commands are in [the workflow guide](README.md).
[Validation](validation.json) identifies remaining authorization, custody, index
identity and measurement-freeze fields. Once approved, use only the detached
report-and-timing collector; estimate costs, review budget/penalty choices, derive
real history statistics, freeze configuration and fit only when all gates pass.

Approve/amend: **(1)** scope, grouped split, source labels and permitted use/custody;
**(2)** proposed settings; **(3)** diagnostic collection of 24 attempts/up to 30 local
generations now, or wait for fitting repairs. Budget/penalty stay undecided.
