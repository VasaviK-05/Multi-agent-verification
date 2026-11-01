# Calibration proposal — no execution or approval yet

The preceding 344-attempt **diagnostic recording** proposal could never export calibration:
`collection.measurement_input()` rejects the DiagnosticRecordingRequest type unconditionally.
Changing its preparation_authorization cannot remove that guard. Its unwitnessed
DiagnosticExclusionRoster is also not the required FinalTestReservation. The diagnostic's
old measured attempts must not be relabelled, promoted or pooled with another setup.

This v2 proposal instead selects the existing **label-free cost collector**,
`app.benchmark.collect_costs`, and existing `mean_attempt_wall_time_ms_v1` calibrator.
It is fully populated except genuine authority records and future measured observations.
No application/production code or contract has been changed. No verifier has run.

## Every missing record and its legitimate source

1. `collection.pending.json: preparation_authorization` is null. It authorizes **new
   cost-measurement use of the exact 86 preparation examples**, under the attached design,
   not reuse of the old run allowance. The dataset/project owner or an authorized delegate
   supplies it; the current user can do so if empowered to authorize this use. The eventual
   MeasurementInput copies this reference unchanged. A collector may record the actual
   human approval reference, but cannot originate permission.
2. `collection.pending.json: final_test_reservation.custody_record` is null. The identical
   field is null in `calibration.pending.json`. **One real record is copied to both**, not
   two separate approvals. The custodian/split owner adopts the exact combined metadata-only
   exclusion roster: 44 reserved entries from both prior rosters, no final contents/outcomes.
   Original final split/group/content identities remain untouched. The combined dataset ID
   identifies an exclusion union for this measurement campaign, not a rewrite of either
   original final dataset. The record must truthfully say this is procedural reservation,
   not independently blinded/third-party custody. A user acting as custodian may adopt it;
   an agent can record that decision and verify hashes but cannot claim it happened.
3. `calibration.pending.json: freeze_record` is null. The measurement/study owner adopts
   the attached cost-only design and the immutable-input freeze procedure. Before the
   calibrator runs, the recorder must save the actual collected MeasurementInput digest,
   setup fingerprint, request digest and included/excluded run IDs in a new freeze receipt,
   linked to that real approval. It freezes **these measurement inputs and estimator choices**,
   not a policy, correctness labels, final outcomes, budget or loss settings. The owner can
   authorize this deterministic recording procedure now; the factual receipt can only be
   completed after collection. Do not fill it now with an invented observed digest.

`calibration.pending.json: measurements` is intentionally null: this is future machine-
produced data, not a user decision. `--measurements` supplies it after execution.
Required verifiers, warm-up inclusion, sample/order, model settings and all other configuration
are populated proposals. Adopting the bound design approves them; no unspecified fitting
decisions are requested. No study_approval, correctness labels, loss/prior, budget/resource
weight or publication approval is required by this **cost-only** schema.

These are **project-schema/workflow requirements**, not evidence of a law, ethics-board,
provider or external institutional requirement. The schemas check nonblank references,
identity consistency and split exclusion; they do not authenticate ownership or witnesses.
No mandatory third-party custodian, notarization or independent signature is encoded.
External dataset/provider permissions still depend on actual applicable terms, which these
strings cannot confer. No external rights or approvals have been independently verified
here, and no new external approval requirement is being asserted.

## Why records for outcome-free costs?

The purpose of custody is split exclusion, not correctness scoring: timing/model calls on
reserved examples would still use held-out inputs and could contaminate later decisions.
Validators compare example, question, group, content and run identities without opening
final payloads. Freezing inputs prevents post-hoc dropping of slow/failed calls or selecting
a favorable setup/mix after seeing durations. The calibrator includes failed measured
attempts, and the explicitly adopted no-warmup design retains first calls. Its artifact
embeds actual measurements and recomputes the input digest and calibration ID on reload.
No external rule makes such records intrinsically necessary for every timing experiment;
they are the existing project's calibration admission contract and remain intact.

## What previous permission actually covers

- The factual authorization explicitly covered one diagnostic pass (24 attempts/30
  generations/100 metadata), already consumed, with labels/study/custody/freeze unapproved.
  It does **not** authorize new calibration collection or promote the stored diagnostic.
- The arithmetic request records authorization for the constructed seed42 pilot and its
  procedural holdout. That pilot already has a valid rule/semantic calibration. Its later
  approval.json explicitly scopes permission to that arithmetic pilot/configuration and
  says recalibration_authorized=false. It is not permission to run these rows through
  evidence/confidence in a new mixed-population campaign or to pool incompatible setups.
- Both preparation payloads are locally available and can be inspected/prepared here;
  **new measurement use of all 86 rows is pending the explicit v2 permission**. Original
  roles/groups/answers/references are unchanged; no final contents or outcomes were read.
  Arithmetic labels are not used by this design. The six proposed factual correctness
  labels remain unapproved. Approval of cost measurement does not approve those labels.

## Exact measurement design

See `design.json`, populated `roster.json`, `collection.pending.json`, and `adapter.json`.
86 runs, 43 history/43 development: addition 14, subtraction 24, multiplication 22,
division 20, factual 6; all four verifiers, 86 attempts per verifier. One seeded shuffle
(20261028), fixed semantic/evidence/rule/confidence order, one repetition, no warmups,
sequential CPU, existing caches, five confidence generations at temperature0.8/seeds0..4,
60-second per-generation timeout. First-call effects and all measured failures retained.
Mean estimator, median and nearest-rank p95; units are summed attempt wall-time ms.

**Cost-only upper workload: 344 verifier attempts, 430 loopback local generations,
4 loopback metadata GETs, zero downloads, zero paid services, no retries.** Saved-metadata
preflight adds zero HTTP calls. Metadata formula: tags+version before and after factory
initialization. This route does not perform the recording observer's per-call metadata
requests. The existing collector stops on a raised exception after writing valid partial
measurements; later verifiers are not marked failed. Missing required-verifier observations
block calibration. Invalid resources/setup block attempts. No silent setup substitution.

The current inspected setup is `93029e22dfadd1babdfb360f70252113ede0ca17f58bf106ee18b44aea8a9750`.
It matches the factual setup, differs from arithmetic. Only fresh attempts under the
approved observed setup enter this new artifact. Changes require fresh inspection and
approval of the changed binding, never pooling incompatible measurements.

This is an arithmetic-heavy convenience estimate for short reference-assisted examples
(1–29 answer words), not a representative project-wide sample. Existing evidence defects
and four unknown analyzer requirements affect verification usefulness/fitting, not this
cost-only schema. No scientific accuracy or policy-usefulness claim follows.

## Can reports and measurements come from the same attempts?

**Yes in the existing standard RecordingRequest workflow**, which writes linked reports,
pre/post resources and measurements.json in one run. But it requires IndependentLabel
for every row: answer_is_correct, label_method, label_source and provenance. The 80
arithmetic labels have existing independent construction provenance; reuse would need
new use permission. The six factual labels need real adjudication/rubric approval.
The standard cache contract also requires a truthful complete-team-independent attestation;
these are replay-oriented requirements, not prerequisites intrinsic to timing calibration.
With real labels/records it would use 344 attempts/430 generations/1,380 metadata GETs,
not a second verifier pass. This is not the selected v2 proposal.

**No existing label-free path retains both full reports and calibration inputs.**
The diagnostic path retains reports but its export is categorically blocked. The label-free
cost path returns MeasurementInput only and discards returned report objects. Therefore
abstention counts/public judgments cannot be reconstructed from its `status=returned` rows.
Returned rejection/abstention is not an execution failure. If retaining actual reports and
their abstention counts is mandatory while labels remain unapproved, the precise remaining
implementation gap is a report-retaining calibration-only path with genuine reservation
and permission, prohibited training export, and the existing resource checks. It needs a
separately scoped implementation decision; no amount of custody text repairs that gap.
No such code is being slipped in or diagnostic guard weakened in this proposal.

## One approval statement (proposed; not yet given)

“As the person authorized to permit this preparation-data use and act as its procedural
split custodian, I approve the exact v2 proposal identified in approval-binding.json for
local measured-cost calibration only: use its 80 arithmetic and six factual preparation
examples with their existing history/development roles, exclude all 44 reserved metadata
entries without opening final contents/outcomes, and run one sequential CPU pass with
the attached seed/order/model settings, no warmups or retries, retaining first calls and
all measured failures. I authorize at most 344 verifier attempts, 430 local generations,
four local metadata requests, no downloads or paid services. I adopt its estimator and
authorize freezing the actual measurement/request/setup digests and inclusion roster
before creating and reload-validating one calibration artifact. I understand this selected
existing cost-only collector retains statuses and timings but not returned reports or
abstention counts. This does not approve correctness labels, scientific/publication claims,
policy fitting, final evaluation, or independent third-party custody.”

If the user lacks that data-use/custodian authority, the relevant owner must supply those
parts instead; the statement must not be accepted as a fictional role assignment.

## Commands after genuine records exist

Record the actual approval and custody reference in new `collection.authorized.json` and
the identical reservation in `calibration.authorized.json`. Populate freeze_record with
the real approved freeze receipt only after measurements exist. Keep pending files unchanged.

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
$env:NO_PROXY='localhost,127.0.0.1,::1'
$env:VERIFIER_COLLECTION_ADAPTER_CONFIG=(Resolve-Path build/verifier-cost-calibration-proposal-20261028-v2/adapter.json).Path
.venv/Scripts/python.exe -m app.benchmark.project_adapter preflight build/verifier-cost-calibration-proposal-20261028-v2/adapter.json --output build/verifier-cost-calibration-proposal-20261028-v2/preflight-before-run.json
.venv/Scripts/python.exe -m app.benchmark.collect_costs build/verifier-cost-calibration-proposal-20261028-v2/collection.authorized.json --output build/verifier-cost-calibration-proposal-20261028-v2/measurements.json
# Save actual frozen input/setup/request digests and inclusion roster under the approved procedure before calibration.
.venv/Scripts/python.exe -m app.game.offline.calibration build/verifier-cost-calibration-proposal-20261028-v2/calibration.authorized.json --measurements build/verifier-cost-calibration-proposal-20261028-v2/measurements.json --output build/verifier-cost-calibration-proposal-20261028-v2/calibration-v1.json
.venv/Scripts/python.exe -c "from app.game.offline.calibration import CalibrationArtifact,read_json; a=CalibrationArtifact.model_validate(read_json('build/verifier-cost-calibration-proposal-20261028-v2/calibration-v1.json')); print(a.calibration_id)"
```

Do not execute a diagnostic alternative as part of this approval. If complete same-attempt
reports are required, resolve the implementation gap or genuine labels first, before spending.
