# Prototype game policy compatibility diagnosis

Date: 2026-11-02. This is a read-only compatibility diagnosis after commit
`6ba543890bf2d70bb2be4cce992056835ed4e6b1`. The concurrent
`app/game/deployment.py` observer wiring remains in the worktree and is not part
of that commit. No verifier generation, strategy sampling, DB write, study,
calibration, or fit was run for this diagnosis.

## Enforced resource identities

`GameRuntime.run()` requires the observed `ResourceManifest` to equal the
artifact contract. The relocation change allows one explicitly bound
`index:evidence-index` difference after verifying index inputs; it does not map
implementation or service identities. `ProjectObserver` also re-observes the
Ollama metadata and requires it to match the saved local observation.

The core relocation checks remain as recorded in
`build/multitask-policy42/game-resource-relocation-gate-audit.json`: manifest
fields other than `corpus_path`/`corpus_mtime`, corpus bytes, receipt, FAISS,
chunks, embedding/NLI snapshots, chunking, index version, and adapter semantic
settings match the current bound inputs. The historical and current aggregate
`evidence-index` fingerprints differ (`e8023002…` vs `dfe45878…`) because that
resource fingerprint includes the raw `manifest.json` digest. This is the one
difference the explicit relocation binding can cover.

## Verifier implementation fingerprints

The fingerprint recipe in `app/benchmark/project_adapter.py` hashes each row's
listed source files as raw bytes and combines the filename/hash pairs. The
shared inputs for every verifier are:

- `app/verifiers/base_verifier.py`
- `app/models/schemas.py`
- `app/benchmark/project_adapter.py`

The verifier-specific additions are:

| Verifier | Additional fingerprint inputs | Artifact fingerprint | Current fingerprint |
|---|---|---|---|
| confidence | `app/verifiers/confidence_verifier.py`, `app/verifiers/self_consistency.py`, `app/verifiers/evidence_verifier.py`, `app/verifiers/claim_generator.py` | `9d33739bb0216d198b0b2ce2d14aaab724abb07d486a354c05df84700e460a4d` | `7075d43b488baa62481d195f5a883c542ce2c44d1887d8f388e5ade9f83d6308` |
| evidence | `app/verifiers/evidence_verifier.py`, `app/verifiers/evidence_retriever.py`, `app/verifiers/claim_generator.py` | `0fdcbbb419738a57a262b1f730cf8ff4ea357d562967b52bde85bb19356f60b4` | `2fa79f7e568082734cf18b31cbd5a6add154082d4e5d9038b2c0fcc80ceb9c88` |
| rule | `app/verifiers/rule_verifier.py` | `2f870d6cfb93c2918a38616627a0be8bc42f624afbad49338e69f8bf5a00059f` | `f790e4269f746f81d4dedc1a14a9921c2549158b8f08a04ccebe28d1741a3403` |
| semantic | `app/verifiers/semantic_verifier.py`, `app/verifiers/claim_generator.py`, `app/verifiers/confidence_verifier.py` | `9b76f1ea898782cfbdb43a702e2d9e85f3cbf0f99c8f0bdcb7e67551fbe45098` | `e79326f49985fda44e7bde0f03ad5878933e7f1b40f5995711474378ec4fa776` |

The bundle records source revision `17b695373f935dc1f5fd09c37cf8917969367f7a`
and application digest `d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf`.
The clean Git tree at that revision produces different verifier aggregates
(confidence `fc20ce7e…`, evidence `4c0b07a8…`, rule `83cc37d7…`, semantic
`3d11ad55…`). Therefore the artifacts were produced from a dirty source tree;
the digest does not retain its file-level contents. No local backup contained
the original Python source snapshot.

The working tree uses CRLF (`core.autocrlf=true`), while Git blobs use LF. For
the verifier source inputs, normalizing the current files to LF makes every file
match that recorded Git revision except `app/models/schemas.py`. That schema
change adds minimum-length constraints to `ValidationRequest.question` and
`.answer`, and adds `ValidationResponse.uncertainty_reasons`. These change the
request/response contract, although the verifier algorithm files themselves
have no text-level changes against the recorded revision. The artifact's
expected aggregate still does not equal the clean-revision aggregate, so it is
not possible to prove the missing dirty source was equivalent. The relocation
observer changes in `recording_adapters.py` and `deployment.py` are not inputs
to the four verifier implementation hashes, but they do change the overall
application source digest.

This is an enforced blocker: `GameRuntime` compares the exact implementation
resource rows. No code hash was mapped or ignored. Passing current unit tests is
not evidence that the lost source snapshot was equivalent.

## Ollama identity

`ServiceObservation` hashes these fields into the confidence service resource:
`version`, `url`, `model`, `model_digest`, and `server_version`. The artifact's
service fingerprint is `5347e328e94b1736cbad1c2d65a812c6255665f92d7e297d2944f1420d97f895`;
the current record hashes to `c167e5133b0c0f9cb650c1d51cb5592a9be4c5d73133076389fb89ecaf5b0be9`.

A metadata-only `observe_service()` call (version and tags endpoints; no
generation) returned the saved current record exactly: URL
`http://localhost:11434/api/generate`, model `llama3.2:3b`, model digest
`sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`,
server version `0.40.11`. The URL/model are also bound by the matching adapter
configuration fingerprint; the model digest is separately bound by the
matching `ollama-model` resource; the observation schema version is fixed.
Consequently the differing service fingerprint is attributable to
`server_version`. The expected historical server version is not stored in the
bundle and cannot be recovered from its aggregate digest. The current live
service matches its saved observation, but not the policy's historical service
identity. This remains an enforced blocker.

## Runtime-version diagnostics

Recorded versus installed values include Python `3.11.5` vs `3.10.0`, NumPy
`2.4.6` vs `2.2.6`, and Requests `2.34.2` vs `2.33.1`. The other listed
recording dependencies match, and `sentencepiece` is absent as recorded. Only
Python 3.10 was available from the local Python launcher.

These version differences are **recorded diagnostics**, not exact-version
comparisons in the live resource gate. `inspect_setup()` adds a blocker when a
required package is missing, but otherwise records versions in
`MeasurementSetup`; `ProjectObserver` returns only its `ResourceManifest`, and
`GameRuntime` compares that manifest. The observed dependencies are installed.
Version drift is not authorized as equivalent, however; prior cost timings and
solver environment measurements do not establish equivalent performance in
this environment.

## Status and concrete route

No relocation binding was enabled. The two arithmetic requests were not sent to
`ValidationService`: strategy selection and verifier dispatch did not occur.
The recorded gate audit has null final status rather than a fabricated
uncertain result.

The smallest route that preserves the existing policy is for the original
artifact/source owner to provide (1) the exact dirty application source snapshot
whose digest is `d2565ca…`, and (2) the original Ollama `server_version` used
for the policy's service fingerprint, with the same pinned model digest. Then
run that code and service in a compatible isolated environment (the current
machine has no Python 3.11 interpreter), confirm all original fingerprints,
and enable the already implemented content-verified index relocation binding.
No old fingerprints should be changed.

If those historical inputs cannot be recovered, the concrete alternative is a
new compatible deployment artifact, under separate authorization. Preserve the
existing task identities, scope, resource bytes, thresholds, and decision
guards as inputs; recover the original prepared examples/references first
(the local bundle stores only question hashes, and the preparation source tree
is absent). Collect fresh verifier reports for the current implementation,
measure fresh per-verifier costs in the chosen environment, then fit separate
arithmetic and factual task policies with a new reputation snapshot. Do not
reuse old reports as current implementations, transplant their reputation as
fresh evidence, or treat the offline transfer-evaluation contract as production
authorization. No collection, calibration, fitting, or activation was started.
