# Owned project publication and laptop preservation, 1 November 2026

This publication adds the original owned study inputs and outputs to the existing
feature branch. It does not authorize activation, inference, collection, indexing,
calibration, fitting, final evaluation or database writes. Historical bytes,
observations, configurations and policy identities are preserved without rebinding.

The exact reviewed paths, sizes and SHA-256 hashes are in
[publication-files.sha256.json](publication-files.sha256.json). Exact per-file
ignore exceptions expose these files; other build outputs and custody remain
ignored. The source, tests and original prototype ZIP were already tracked.
The pre-existing empirical audit Markdown and its JSON are included unchanged.

## Integration inputs

- Original bundle: [multitask-prototype42-v1.zip](../artifacts/policies/multitask-prototype42-v1.zip).
  Its identical extracted layout is now at `build/multitask-prototype42-v1/`.
  Bundle ID: `98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34`.
- Policies: `build/multitask-prototype42-v1/arithmetic/policy.json` and
  `build/multitask-prototype42-v1/factual/policy.json`. Episode, reputation,
  resource expectations, costs and metrics are adjacent. Read the original
  [runtime handoff](multitask_prototype_bundle.md) and bundle README for scope.
- Authentic configuration: `build/multitask-policy42/adapter.json`. The corpus,
  `index-v2/`, `index-receipt.json` and `service-observation.json` are in that
  same directory. They are original observations, not attestations of a new host.
- A supported history question, answer and required reference context are in
  [prototype-history-request.example.json](prototype-history-request.example.json),
  copied from the arithmetic history/development request. This is a request example,
  not an instruction to activate the API. Both task policies require reference
  context and prepared question identities. Semantic comparison is unsupported.

The embedding snapshot is all-MiniLM-L6-v2 revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; NLI is nli-deberta-v3-small
revision `fa2804872c3b4bd748f38c0185cc85775361e735`. The authentic adapter records
their original absolute paths. The local Ollama service/model is `llama3.2:3b`
at `http://localhost:11434/api/generate`; its retained observation is supplied.
No service was started or queried. Preserve model files and notices from the
separate local archive; do not redistribute weights through this public project.

Relocation instructions are separate from the historical configuration: restore
the original relative corpus/index layout, use the portable resource-adapter
template in the bundle as guidance, and let the live observer check actual model,
service, implementation and resource identities. A changed path/configuration or
resource identity may fail compatibility. Do not modify old observations or
artifacts to bypass that failure. There is no turnkey API activation in this work.

## Research and transfer inputs

`build/multitask-policy42/{arithmetic,factual,semantic}/` contains the independent
history/development examples and labels (`preparation.json`), requests,
`training-manifest.json`, `collection/recordings.json`, attempt journals,
measurements, observed setup, calibration, original policy inputs and development
evaluation. Final reservations contain metadata only; actual final payloads are
withheld. The semantic study's diagnostic policies do not add a deployable task.

Earlier studies are retained in `build/arithmetic-pilot42/`,
`build/factual-policy42-20261029/`, `build/factual-reliability-first42/`,
`build/factual-coverage-exploration42/`, `build/multitask-uncertainty-sweep42/`,
`build/factual-diagnostic-20261026-01/` and the preparation/cost-study directories
enumerated in the file manifest. Failed and rejected preparations remain historical
records, not approved inputs. Diagnostic recordings remain diagnostic.

For poisoning-transfer research use the original arithmetic/factual
`build/multitask-policy42/<task>/collection/recordings.json`, training manifests,
policy inputs, frozen policies and reservations together with
[the transfer contract](upstream_transfer_evaluation.md). Fresh paired current
clean/altered recordings, declarations and current resource validation are still
required and were not created. Historical recordings cannot substitute for them.
These research inputs are additional to the API integration inputs above.

The exact historical collector application digest
`47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`
remains unrecovered. Available distinct owned source snapshots and source-hash
records are preserved in
[owned-historical-source-snapshots.zip](../artifacts/studies/owned-historical-source-snapshots.zip)
with [their manifest](../artifacts/studies/owned-historical-source-manifest.json).
They do not establish the missing digest or source equivalence. Previously deleted
or never-inventoried files have not been recovered.

## Attribution and redistribution

The `sources/` directories retain original files and the complete mledoze countries
ODbL notice. Attribution: [mledoze/countries](https://github.com/mledoze/countries),
source revision `6031f5df137c41c76d180c55a0782185ae3ed05b`.
The supplied source snapshots and derived country-fact databases/corpora are made
available under the accompanying ODbL terms; this does not relicense project code.
GeoNames countryInfo data is attributed to [GeoNames](https://www.geonames.org/),
whose [export terms](https://www.geonames.org/export/) permit reuse with attribution
under CC BY. Corpus/index transformations and deliberate retrieval omissions are
documented in the study workflow; source facts are snapshot values, not current
census claims. Notices and upstream provenance remain with the originals.

## Restricted and external preservation

The separate repository
`https://github.com/VasaviK-05/multi-agent-study-preservation-20261101` was verified
private before the custody upload. Its `codex/preservation` branch contains an
opaque ZIP, restricted relative-path/size/hash manifest and verification record.
No evaluator access, invitations or messages were sent. Restricted inventories and
archives are outside this project. Final payload bytes were hashed/copied/extracted
for integrity checks, never parsed or printed.

The durable local migration directory is
`C:\Users\jhaan\Project-preservation-20261101`. It contains full workspace
classification metadata, restricted material, archive manifests and verification
records. Its `model-resources-NOT-REMOTELY-BACKED-UP.zip` is 2,689,720,522 bytes,
SHA-256 `497442ac6e95e5497bb03229565effb80b70b3d776c33887ca88c7a74da34835`.
It preserves 40 files from the installed Hugging Face hub and Ollama model stores.
Extraction and every model-file hash were verified. No approved external storage
destination was available; no paid storage or Git LFS was introduced.

**Laptop migration is not complete.** Upload that model ZIP and
`model-resource-manifest.json` to owner-approved private external storage, download
and verify the archive SHA-256 and all extracted file hashes before retiring the
laptop. The local `historical-unique-local.zip` and its manifest preserve distinct
review exports, draft bundles, test artifacts and historical records without
duplicating existing tracked/public bytes. They also remain local: copy the ZIP,
`historical-unique-manifest.json`, `workspace-inventory.json` and verification JSON
to the same approved external destination. Those local manifests enumerate every
remaining file individually, including redundant/unrelated categories. Do not
publish this mixed archival material publicly without its own content review.

## Exclusions and verification

- Reserved final payloads and custody: only in the private preservation repository.
- Model weights and model-store metadata: local migration archive, external upload
  still required; Git size and third-party redistribution constraints.
- Historical mixed review exports, archived source trees, old ZIPs and synthetic
  model fixtures: deduplicated local archive; usable distinct owned source snapshots
  are separately published. Other teammate implementations/frontend/DB files were
  not newly published as duplicate copies.
- Existing unrelated corpus/index data and teammate outputs: left unchanged;
  already tracked files remain available through the existing project. Untracked
  unrelated resources are identified in the local-only manifest, not silently
  claimed as owned or remotely backed up.
- Virtual environments, bytecode, reproducible test caches and frontend dependency
  caches: reproducible disposable categories, excluded without deleting originals.
- Credentials: no credentials intentionally included in either repository.
  Migrate Git Credential Manager, Hugging Face tokens and any service credentials
  through the corresponding secure sign-in/credential mechanism, never these ZIPs.
  Credential-bearing filenames and any scan findings belong in the local records.
  The current tracked `.env.example` and two historical blobs contain
  credential-shaped database URLs. Their validity was not tested; values are not
  repeated and history was not rewritten. Treat them as requiring owner review
  and rotate any real credentials through their provider. The existing Ollama
  private-key filename was inventoried separately and its bytes were excluded.
- Historical machine links and absent outputs in old reports remain unchanged.
  In particular the empirical audit's old Canvas link is a laptop-local link;
  its companion JSON is published here. Original logs may mention unavailable
  historical source trees or outputs. They are records, not portable setup steps.

All 20 published original policy JSONs were reloaded through `PolicyArtifact`
validation, and the original prototype was loaded without inference; see
[publication-policy-validation.json](publication-policy-validation.json).
The public and custody archives were extracted and each file hash verified.
Historical unique archive members were verified by reading their ZIP entries.
Prior implementation-test results in the existing handoffs are reused; no
implementation changed. Commit/tree and remote-byte verification records are
kept beside the local migration archives.
