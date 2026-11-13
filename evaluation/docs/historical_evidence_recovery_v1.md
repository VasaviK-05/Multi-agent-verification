# Historical evidence recovery

Inventory: `evaluation/artifacts/person1/historical_evidence_recovery_v1/recovery_inventory.json`

Final Test labels were not opened. No authorization was created. No file under `data/` was rewritten.

| Artifact | Status | What was found |
|---|---|---|
| `data/articles_13083.json` | `ORIGINAL_VERIFIED_IN_PLACE` | Working-tree file, 50,061,372 bytes, SHA-256 `b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8`, matching the documented hash. Git history has no blob for this path. |
| `data/evidence_index/articles_13083/` | `ORIGINAL_VERIFIED_IN_PLACE` | Manifest records that same corpus hash and index `idx-6d28c9c49dac`, chunk size 500, `all-MiniLM-L6-v2`. |
| `data/evidence_corpus.json` | `ORIGINAL_VERIFIED_IN_PLACE` | SHA-256 `668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5`. |
| `data/evidence_index/evidence_corpus/` | `ORIGINAL_VERIFIED_IN_PLACE` | Manifest records index `idx-9c87422f0357`. |
| `data/test_evidence_corpus.json` | `ORIGINAL_VERIFIED_IN_PLACE` | SHA-256 `0170d64b697dab9bbeb91e2f935b6bcad862ae8bb55958beea712ccf1e424795`. |
| `data/articles_13083_index/` in git | `ORIGINAL_RECOVERED` | Commit `be52b30c65afdd64a39b7e954d0af4ea32741f9a`, 2026-10-23. Recovered to `evaluation/artifacts/person1/historical_evidence_recovery_v1/recovered/data/articles_13083_index/`. The manifest's corpus path is `data/test_evidence_corpus.json`, corpus SHA-256 `0170d64b…`, index `idx-62d878fbb62f`. The directory name is not the 13,083-article corpus. |
| Execution-source custody ZIP | `NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE` | Later search of gitignored `evaluation/datasets/*.zip` found dataset and label-custody archives. None is documented as an execution-source ZIP. Labels inside them were not extracted. See `person1_custodian_completion_and_final_test_authorization_audit.md`. |
| Reviewed verifier collection adapter | `NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE` | `VERIFIER_COLLECTION_ADAPTER_CONFIG` is unset. `docs/verifier_project_adapter.template.json` and `docs/arithmetic_adapter.template.json` are templates. Embedding snapshot, NLI snapshot, index receipt, service observation, hardware, and collection timestamp are `UNKNOWN`. |
| Final Test evaluation authorization | `NOT_FOUND` | `evaluation/config/final_test_v2_custodian_appointment.json` records `evaluation_authorization: PENDING` and `label_release: NOT_AUTHORIZED`. An approval was not reconstructed. |

The recovered index files are the git bytes. They are not a substitute for `data/articles_13083.json`, which remains the on-disk original.
