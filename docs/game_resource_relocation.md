# Explicit resource relocation for game policies

`inspect_setup()` remains strict by default. A collection/game deployment may
opt in by setting `resource_relocation_binding` in its explicit
`AdapterConfiguration` to a separate JSON binding file. The legacy
`VERIFIER_RESOURCE_RELOCATION_BINDING` environment variable remains an explicit
override. The historical manifest and receipt are never rewritten. The binding
is deployment metadata, not a replacement policy artifact.

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

The adapter factory accepts a binding only when the stored manifest and the
current manifest differ in `corpus_path` and/or `corpus_mtime`, with every
other field equal. It hashes the corpus, vectors, chunks, physical historical
manifest, models, and receipt, checks the complete chunking/semantic settings,
and confirms the receipt against current corpus/vector/chunk/embedding bytes.
It computes a current logical index identity from the verified current
manifest without writing that manifest. The resulting proof is passed to
`EvidenceRetriever` only by the adapter factory. The retriever rechecks the
binding, manifest fields, current file hashes, and receipt immediately before
loading the existing FAISS index and chunks. A failed proof aborts; it does not
fall back to rebuilding or saving the index. Ordinary callers without a proof
retain the existing behavior.

Game-mode `ValidationService` injects the verifier pool returned by the same
adapter factory used by Phase 2 collection. Baseline construction stays lazy
and unchanged. The game resource observer uses that same explicit adapter
configuration and verifies the binding again when it snapshots resources.

The binding ID and both resource-manifest IDs, paths, timestamps, differing
manifest fields, and verified content hashes are included in the preflight and
execution audits. A binding that is absent,
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

Create a fresh binding only after the resource preflight has identified a
manifest whose differences are strictly path and timestamp relocation. For
example, with `adapter.json` configured to name the output binding path:

```powershell
python -c "from pathlib import Path; from app.benchmark.project_adapter import AdapterConfiguration,create_relocation_binding; from app.game.offline.calibration import read_json; c=AdapterConfiguration.model_validate(read_json('adapter.json')); p=Path(c.resource_relocation_binding); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(create_relocation_binding(c).model_dump_json(indent=2),encoding='utf-8')"
```

This creates only the binding file. It does not rewrite the manifest/receipt,
rebuild the index, load verifier models, or make provider calls.

Focused checks:

```powershell
python -m pytest -p no:cacheprovider tests/test_game_resource_relocation.py -q
python -m pytest -p no:cacheprovider tests/test_game_runtime.py tests/test_game_prototype_bundle.py tests/test_game_reliability_first.py tests/test_game_three_outcomes.py -q
```
