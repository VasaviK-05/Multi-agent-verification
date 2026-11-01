# Completed measured verifier-cost calibration

The single user-authorized pass completed on 2026-10-28. Actual audited counts:
344 measured verifier attempts, 430 local generation requests, four local metadata
requests. All 434 HTTP requests returned status 200. Each verifier has 86 returned
attempts, zero raised failures/timeouts/interruptions, zero missing observations.
No retries, replacements, warmups, exclusions, downloads or paid services occurred.

These are factory-bound, label-free attempt timings, not report-bearing recordings.
Returned reports, directional judgments and abstention counts are unavailable.
An internally handled verifier/provider error could return normally; status=returned
does not assert verifier correctness or success of its judgment. No correctness
labels, final-test contents or final outcomes were used. All 44 final metadata entries
were excluded. Procedural custody is explicitly recorded, not third-party custody.

Existing mean_attempt_wall_time_ms_v1 calibration, milliseconds:

- Semantic: n86; mean30.955616287280655; median28.301849961280823;
  nearest-rank p9539.26979983225465; execution failures0.
- Evidence: n86; mean42.12459068756204; median23.43365002889186;
  nearest-rank p95147.83600019291043; execution failures0.
- Rule: n86; mean0.1322023115705612; median0.08204998448491096;
  nearest-rank p950.16120006330311298; execution failures0.
- Confidence: n86; mean11831.109354651511; median11469.350849976763;
  nearest-rank p9512696.48199994117; execution failures0.

All 344 measured calls, including first calls, are included. Nearest-rank p95 is
the 82nd ordered observation out of 86 per verifier. These estimated costs are sums
of verifier-attempt wall times in ms, not money, CPU time or parallel request latency.
Initialization is excluded; lazy work inside verify is included.

Calibration ID: `1a2abc5663193e025f9c7e62805dbad5e9d6b720a1a6895b7f40e91f779ab992`.
Setup fingerprint: `93029e22dfadd1babdfb360f70252113ede0ca17f58bf106ee18b44aea8a9750`.
Calibration input digest: `4d927ec6749561b66742d4189f3b8353e489a778f27931ded75aa92108a687cc`.

Artifacts in this directory:

- `authorization.json`, `collection.authorized.json`: genuine scope-specific approval,
  procedural reservation and complete validated collection inputs.
- `resource-preflight.json`, `resource-postcheck.json`: matching approved local resources.
  The existing factory also checked live service/model metadata before/after initialization.
  This cost-only path does not perform per-attempt resource snapshots.
- `attempt-journal.jsonl`, `measurements.json`: actual same-attempt timings and statuses.
- `network-events.jsonl`, `execution-result.json`: actual request counts and run completion.
- `freeze-receipt.json`: actual input/setup/code/runner/request digests, complete inclusion
  roster, zero exclusions, recorded after collection and before calibration.
- `calibration.authorized.json`, `calibration-v1.json`: existing calibration CLI inputs/output.
- `calibration-validation.json`, `independent-validation.json`: successful reload/recomputation,
  counts, estimator checks, reservation consistency, frozen-file hashes, unchanged bound
  proposal and original factual diagnostic artifact hashes.
- `timings.csv`: full-precision statistics; blank abstention fields mean unavailable.

No remaining blocker to this calibration artifact. Evidence-contract defects and unknown
analyzer requirements remain limitations for verification usefulness/policy fitting; neither
was altered or concealed. No policy was fitted; no production algorithms, DB/API/frontend,
baseline defaults or reputation were changed. Unrelated working-tree changes were preserved.
Nothing was committed or pushed.

Scope: this arithmetic-heavy 80-arithmetic/six-factual preparation sample and measured
setup only. The estimate is not universal or representative project-wide cost, does not
cover long-form answers/structural rules/concurrent serving, and establishes no accuracy
or publication claim. No earlier arithmetic or diagnostic measurements were pooled.
