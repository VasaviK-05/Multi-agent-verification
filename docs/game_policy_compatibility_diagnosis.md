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

ServiceObservation hashes version, url, model, model_digest, and server_version.
The artifact service fingerprint is
5347e328e94b1736cbad1c2d65a812c6255665f92d7e297d2944f1420d97f895; the current
record hashes to c167e5133b0c0f9cb650c1d51cb5592a9be4c5d73133076389fb89ecaf5b0be9.

A metadata-only observe_service call (version and tags endpoints; no generation)
returned the saved current record exactly: URL
http://localhost:11434/api/generate, model llama3.2:3b, model digest
sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72,
server version 0.40.11. The URL/model are also bound by the matching adapter
configuration fingerprint; the model digest is separately bound by the
matching ollama-model resource; the observation schema version is fixed. Thus
the differing service fingerprint is attributable to server_version.

Authentic records are available at published commit 1277e9d in both
build/factual-policy42-20261029/service-observation.json and
build/multitask-policy42/service-observation.json: server_version 0.40.5.
Recomputing content_id over the five exact observation fields with that version
reproduces the policy fingerprint 5347e328e94b1736cbad1c2d65a812c6255665f92d7e297d2944f1420d97f895.
The historical cause is verified. An original-compatible run still needs an
isolated 0.40.5 service with the pinned model digest; the current service
remains an enforced mismatch.

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

## Candidate current setup to freeze

The candidate is the current working-tree source snapshot: Git revision
`ab6bc1dc687452d72bfd6dffc67adfc0e87572ff`, plus the preserved
`app/game/deployment.py` observer change. The measured application-source digest
is `6fe4c7e5d373ecedc22a66224ebef9577e90831b6f6fac7f3f9ce215747ee364`;
`deployment.py` SHA-256 is `22ea98d6d3bdc9e7516c631a135227bfd9d0702b8594a8ebcc6d4b5095f1ccc0`
and its current Git diff SHA-256 is
`05be1949ba722c21e90dd2b994d03765aca2d414d9c03c588654974c807f90b8`.
The verifier-specific raw-source aggregates are the current values in the table
above. Freeze or review this exact modified file before collection, then use
the identical application source through fitting and live execution.

The observed runtime is Python 3.10.0, NumPy 2.2.6, Pydantic 2.13.5,
sentence-transformers 6.1.0, Transformers 5.17.0, PyTorch 2.14.0,
FAISS-CPU 1.15.1, Requests 2.33.1, Safetensors 0.8.0, and Tokenizers 0.23.2.
The resource setup uses CPU, chunk size 500, five Confidence samples at
temperature 0.8, and a 60-second request timeout. The verified corpus digest is
`28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a`; the
embedding and NLI model digests are
`23c61c55d84d9ab0045288ba589018e80ff90cf894514f5676e351c14624d255` and
`a28c08014f62b13be758a1f22d1cbfd30e9f7b0f91d19fbc3bd5c369b11fcf7e`.
The FAISS index and chunks digests are
`5bc44bf0f694d4ffd08b7d5a51191cd953a784d98f9041bd0b52867d42f7c287` and
`bce84c9632b231d0611da47d133c1bb444f2189f0b6ed1701fdbda3929dcec33`; the
receipt matches those inputs. The semantic adapter configuration digest is
`5f7c798ed72745bdbcb1c3f447120cd9373446fe307c60bb6cd7f936839b5ce8`. Ollama's
metadata-only observation is URL `http://localhost:11434/api/generate`, model
`llama3.2:3b`, digest
`sha256:a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`,
server version `0.40.11`. The index relocation binding remains limited to the
content-verified index mapping.

## Status and concrete route

No relocation binding was enabled. The two arithmetic requests were not sent to
ValidationService: strategy selection and verifier dispatch did not occur.
The recorded gate audit has null final status rather than a fabricated
uncertain result.

The published historical-source archive was checked at commit 1277e9d on
origin/codex/offline-policy-recording-pilots. Its 154-entry manifest and ZIP
contain historical-review-local clean-source review snapshots. None of the ten
verifier-fingerprint input paths listed above occurs in that archive. It is not
the missing dirty application snapshot. Recomputing the exact raw-byte
fingerprint algorithm for the current files and clean Git revision reproduces
the aggregate values in the table; neither set equals the policy values. No
archived candidate can be shown to reproduce the required fingerprints.

The smallest route that preserves the existing policy is for the original
artifact/source owner to provide the exact dirty application source snapshot
whose digest is
d2565ca4897a9e1f938900f4feb80fe675b9229c2acb7b27544781ec1c9bdcaf.
The historical service version is now known to be 0.40.5; an isolated service
of that version with the pinned model digest and a compatible Python environment
would also be required. No source archive currently reproduces the four verifier
hashes, so authentic restoration is not presently possible. Do not change old
fingerprints.

If the dirty source cannot be recovered, the concrete alternative is a new
artifact for the current implementation and service, using a distinct output
directory such as build/multitask-prototype42-v2/. The published preparation
inputs are available at commit 1277e9d on
origin/codex/offline-policy-recording-pilots; reuse only their 80
history/development examples per task (40 history, 40 development), including
the existing references, independent labels, and grouping. Do not pass the 40
final-test reservation rows per task to collection.

The exact full-roster ceiling from those inputs is 640 verifier attempts:
80 examples x four registered verifiers x two tasks. The recorded adapter
configuration uses Confidence n_samples=5; it is the only verifier that calls
Ollama, so the ceiling is 160 Confidence attempts x five = 800 Ollama
generations. The prepared analyses are supplied to collection, so these limits
exclude analyzer calls. Use a new output directory, frozen source/resource
manifest, checkpoint/resume, and no automatic retries. Failures and abstentions
remain recorded. Old reports, costs, and reputation are not reusable as fresh
evidence.

For the replacement artifact, preserve the packaged arithmetic/factual coverage
targets (expected_clean_coverage 0.50 and 0.25), threshold 0.55, losses
false-accept 1.0 / false-reject 1.0 / uncertain 0.2, Beta(1,1) history prior,
informative_history_influence_v1, task_output_contract_v2,
all_selected_returned, existing minimum-informative-contributor and dependency
guards, and the reliability-first validation-loss then attempt-cost objective
with its existing tolerances. Preserve task scopes, references, strategies,
and the existing all-feasible-strategies behavior. Fit on development only,
estimate reputation from history only, compute fresh attempt costs, export with
new IDs/provenance, and keep the final-test reservation outcome-free. The old
90% research target remains a separate infeasibility result and is not a reason
to silently alter the packaged 50%/25% targets.

The project owner has now approved the fresh collection within the 640-attempt
and 800-generation ceilings. Phase A stopped before collection because the
approved collector/runtime identity assumptions do not hold. The frozen local
audit is build/multitask-prototype42-v2/phase-a-snapshot.json. It records source
revision 13c420169a96b2deaa0e20de5f63d3158257e5f3, the full app Python file
manifest, verifier fingerprints, dependency versions, model/resource hashes,
live metadata-only Ollama observation, approved input counts, and the exact
deployment.py diff identity. The concurrent deployment.py change remains
unmodified and unstaged.

Two blockers were observed. First, the approved collector adapter.json points
to build/multitask-policy42/corpus.json and index-v2. Its preflight returns
index_provenance: index manifest is stale/legacy; explicit separate index
preparation is required. The relocation implementation at 6ba5438 permits the
runtime ProjectObserver to use an explicit verified binding, but the collector
factory calls strict create_verifiers/inspect_setup before that observer and
does not apply the binding. Second, the deployed VerifierSelector constructs
default verifiers. EvidenceVerifier resolves EVIDENCE_CORPUS_PATH from .env as
data/evidence_corpus.json (SHA-256 668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5)
and derives data/evidence_index/evidence_corpus. The collector instead observes
the 9,206-byte build corpus (SHA-256
28e6241079b1afab419ebdbaea580510796c648d1855dcc91759ab3d8950b95a) and
build/multitask-policy42/index-v2. The runtime corpus is 12,875,871 bytes and
its FAISS/chunks hashes are 3893b97dca2804ecab0fabb26fc9cee52f34b759058ba3d11b2bd7d617ce4168
and ed205cb4a4ac1b665dcffa521af021eef43674a1c3f34ad26674fc59a53e6b7e; no
index receipt exists beside that default index. ProjectObserver reads adapter.json
and does not inspect the verifier instances built by VerifierSelector.

I did not change production resource configuration after finding this mismatch.
The next owner action is to choose one resource configuration and freeze its
exact source/config state: either make the deployed game
verifier construction use the already approved adapter resources, or approve a
revised campaign snapshot that measures the deployed default resources and
includes a valid receipt. Then update the collector factory to honor only the
explicit content-verified relocation proof when applicable, and re-run Phase A.
Until both sides attest the same corpus/index/model/config and the collector
preflight succeeds, collection must not start. Attempts and generations consumed
remain zero; no strategy sampling or live verifier dispatch occurred.
