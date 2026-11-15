> Current Development eligibility update: [Handoff A — approved eligibility v1](eligibility-approved-v1/tabmayee-handoff.md), [scope/configuration](eligibility-approved-v1/recording-config.proposed.json), and [remaining decisions](eligibility-approved-v1/remaining-decisions.md). Eligibility is approved for 744 candidates /372 groups; collection and fitting remain blocked. Root proposals below retain their historical PR35 identities.

# research_v1 canonical pre-collection package

**Engineering proposal for review. Collection and fitting are NOT authorized.**

Start with [final-review.md](final-review.md), [recording-contract.md](recording-contract.md) and [Tabmayee Handoff A](tabmayee-handoff.md). The canonical configuration is [recording-config.proposed.json](recording-config.proposed.json); null approved values are intentional blockers. Public version control uses only public-commit-files.json; see publication-boundary.md. Full payloads, original archives and prior logs remain local-only. [Decisions](decisions-required.md), [blockers](blocker-register.csv) and [compatibility](source-resource-checklist.md) distinguish engineering checks from scientific/live-custody gates.

Package A's durable file layer is the authoritative implementation. Package B's compatible scope, interface and provenance are retained here. Both originals, including their superseded findings and logs, are preserved locally byte-for-byte (not proposed for public commit) in `archive/package-a/` (local only) and `archive/package-b/` (local only). Neither archive is current instruction, readiness or approval. [source-lineage.md](source-lineage.md) identifies supersession and traceability. Original shared checkouts were not edited.

No fitted policy, original verifier implementation or resource identity is replaced. Do not execute archived generators: historical code may access protected datasets. The current allowlisted extractor reads only permitted source ZIP members.

## Reproduce focused engineering tests

From repository root, export `TEST_PYTHON` and `HF_HOME` as documented in [environment.md](environment.md). Set `RESEARCH_V1_ARTIFACT_DIR` to the authorized external ZIP directory for private checks; its value is never committed:

```sh
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py handoff
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py filesystem
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py planning
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py input
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py boundaries
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py existing-boundaries
"$TEST_PYTHON" docs/research_v1-recording-handoff/validation/run_checks.py regression
```

Tests use synthetic reports/factories and temporary directories. They deny network, real verifier construction/execution, model loading and policy/calibration fitting. The full handoff checks require the local evidence bundle and fail rather than certify missing archives. Source-specific pytest cases explicitly skip absent private metadata in a public checkout; set RESEARCH_V1_REQUIRE_PRIVATE_INPUTS=1 for mandatory real-input revalidation. The synthetic boundaries smoke requires none of those private payloads. Production dependency requirements are unchanged.

The source-only extractor accepts `--artifacts-dir` and a new `--output-dir`. It regenerates source roster payloads (including History) and derivation hashes, not scientific configuration, prose or compatibility certificates. It refuses an existing output directory. Raw question/answer strings and IDs remain unchanged. Do not copy synthetic test records into study data.
