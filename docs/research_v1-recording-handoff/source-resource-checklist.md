# Source and resource compatibility checklist

| Requirement | Engineering status | Study/live status / owner |
|---|---|---|
| Original four ZIPs and internal hashes | Preserved and handoff checks verify exact supplied digests | Producer/freeze custody still pending, lead + producers |
| New game source | Narrow main-based patch; engineering manifest records actual bytes | Does not reproduce old 662bd5c whole-app digest; game owner + producer must review future source |
| Source question/answer/IDs | Verbatim strings retained; offline content validation separated from identifiers | Population/reference/label profile still pending, lead + custodian |
| Independent labels | Existing enums/provenance guards unchanged | Zero human-verified source labels; no synthetic-to-ground-truth cast; lead/custodian |
| Calibration input linkage | 464 exact /24 unresolved, including 8 exact warmups, preserved | Actual cost request/tuple ledger absent; producer must resolve or lead choose prospective profile |
| Verifier identities | Recorded per-verifier implementation hashes retained | Actual implementation/config/model observations required, Raunak + Tabmayee |
| Confidence model/samples | Freeze says llama3.2:3b, n_samples=5 | Actual prompt/sampling/service version/tag/digest/custody verification required |
| Evidence | Recorded corpus/index/receipt/model hashes retained | Suitability and actual bytes/receipt observations required, Raunak |
| Semantic | Reference required; model/config expectations retained | Exact permitted reference serializer/profile approval required |
| Rule | Recorded implementation identity retained | Actual implementation observation still required |
| Report adapter/normalization | Existing bodies and adapter enums retained; synthetic rejection checks | Future actual adapter source fingerprint must be pinned by Tabmayee/game owner |
| Resources before/after attempts | Synthetic tests retain/reject unknown or changed observations | No real resource observation performed; guards remain mandatory |
| Test environment | Separately constrained, recorded; production requirements unchanged | Not historical calibration environment or future collection certificate |
| Outcome-free reservation | Existing exclusion/custody checks retained | Independent custodian must supply approval without exposing payload |
| Filesystem | Local engineering contract only, see filesystem-support.md | Windows collection not certified; Tabmayee must resolve intended platform |

Expected historical manifest and setup fingerprints remain unchanged in source-resource-summary.json; full resource-compatibility.json is retained locally. No live actual values are invented. A future request's expected_setup is deliberately null in proposed configuration until actual reviewed source/environment/resource binding exists. Test metadata must never be substituted there.
