# Restricted prototype policy bundle

`multitask-prototype42-v1.zip` is the original, unchanged fitted-policy package.
Normal Git tracks this 41,243-byte ZIP; cloning this branch obtains it.

- ZIP SHA-256: `99516fbe460e816c68601509ca7e202cbcd3880d8d4250ec655f422244ec657c`
- Bundle ID: `98b8f2654163fe95e84a1b916a94174ddc37aa399429bba94f99890573168d34`
- Arithmetic artifact ID: `e4981bb78a278f216efb0ece9b79eca8381fbaacdf6315e8bcb4cbc6bbb638f2`
- Factual artifact ID: `c66e137fd64f61222e4a69cf0e025b91bc1d3ae075166743f2c795acd9d7cd79`

From the repository root, using the existing project Python environment:

```powershell
Get-FileHash -Algorithm SHA256 artifacts/policies/multitask-prototype42-v1.zip
# Choose a fresh destination; do not overwrite historical artifacts.
Expand-Archive -LiteralPath artifacts/policies/multitask-prototype42-v1.zip -DestinationPath build/prototype-from-git-v1
.venv/Scripts/python.exe -m app.game.offline.prototype validate --bundle build/prototype-from-git-v1
```

The archive has no enclosing directory. Policies are
`build/prototype-from-git-v1/arithmetic/policy.json` and
`build/prototype-from-git-v1/factual/policy.json` after this extraction.
Validation must report the bundle ID and both artifact IDs above. It validates
hashes, numerical certificates, episode bindings and compatibility expectations;
it does not establish live resource readiness.

Arithmetic uses the approved 50% expected clean-development coverage policy;
factual uses the experimental 25% policy. Both require reference context and are
restricted to their respective 40 prepared question identities. Unseen questions
fail safely. Semantic equivalence has no supported decisive policy. All
positive-probability plans contain two verifiers; three verifier types used across
the policies do not run together on every request. Always-abstaining probability
remains approximately 39.394% arithmetic and 33.333% factual. Scores are not
calibrated correctness probabilities. Development diagnostics and simulated
attacks do not establish held-out superiority.

The integration owner must use the included episode settings, declared task
routing and scope, compatible external resources and live resource observation.
Models, corpus/index payloads and services are not bundled. Do not rewrite resource
identities to bypass mismatches. See the included README, runtime requirements and
resource-adapter template, plus [the integration handoff](../../docs/multitask_prototype_bundle.md).
Committing, extracting or validating this ZIP does not activate game mode or change
API/runtime defaults. Integration and activation require separate work.
