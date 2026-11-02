# Explicit resource relocation for game policies

`inspect_setup()` remains strict by default. A game deployment with a relocated
corpus/index must opt in through `VERIFIER_RESOURCE_RELOCATION_BINDING`, which
points to a separate JSON file outside the prototype bundle directory. The
historical manifest and receipt are never rewritten. The binding is reviewed
deployment metadata, not a replacement policy artifact.

The supported binding schema is `verified_resource_relocation_v1` in
`app/game/offline/resource_relocation.py`. It binds:

- the exact expected `ResourceManifest.manifest_id` from the policy contract;
- historical and current corpus and index-manifest paths;
- historical and current corpus modification times;
- corpus bytes and size, FAISS bytes, chunks bytes, and manifest bytes;
- the receipt bytes and receipt identity;
- embedding and NLI snapshot identities, chunk size, embedding name, index
  version, and the complete semantic adapter configuration fingerprint;
- the policy's historical `evidence-index` fingerprint and the current observed
  `evidence-index` fingerprint.

At runtime, the observer accepts a binding only when the stored manifest and a
freshly computed manifest differ in `corpus_path` and/or `corpus_mtime`, with
every other field equal. It independently hashes the current corpus and index
files, validates the existing receipt against the current corpus, vectors,
chunks, and embedding snapshot, and checks the recorded model and semantic
settings. The observer reports a current `ResourceManifest`; it does not rewrite
it to look historical. `GameRuntime` permits only the explicitly bound
`index:evidence-index` fingerprint pair. All other resource fingerprints,
including verifier implementations, service identity, models, configuration,
and corpus, must still match exactly.

The binding ID and both resource-manifest IDs, paths, timestamps, and verified
content hashes are included in the execution audit. A binding that is absent,
malformed, stale, for another policy contract, or inconsistent with any current
content rejects. Callers without the explicit binding keep the original strict
preflight behavior.

Do not create a binding by copying fingerprints from an unrelated run. First
compare the bundle's expected resource manifest with the current observer
inventory. A changed corpus, index, chunk file, model, receipt, semantic setting,
implementation, or service is a compatibility failure and requires the
corresponding resource owner to restore the exact bound resource or prepare a
separately authorized compatible policy. Relocation does not authorize those
changes.

Focused checks:

```powershell
python -m pytest -p no:cacheprovider tests/test_game_resource_relocation.py -q
python -m pytest -p no:cacheprovider tests/test_game_runtime.py tests/test_game_prototype_bundle.py tests/test_game_reliability_first.py tests/test_game_three_outcomes.py -q
```
