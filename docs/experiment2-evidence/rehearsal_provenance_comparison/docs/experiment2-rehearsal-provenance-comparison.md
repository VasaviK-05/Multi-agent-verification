# Derived Experiment 2 Rehearsal Provenance Comparison

> **Derived comparison artifact.** Created after the original rehearsal from immutable source records. This is not an original historical rehearsal artifact and does not alter or replace one.

## 1. Purpose and evidence boundary

This comparison tests whether retained Development rehearsal verifier inputs have exact input-level matches in the approved Experiment 2 Development eligibility population using the repository-defined SHA-256 contract. It preserves the rehearsal and approved candidate ID namespaces separately. It does not establish identical candidate IDs, canonical recording identity, label equivalence, or permission to use attempts in policy fitting. It does not authorize recording, collection, fitting, optimization, or Final Test evaluation.

## 2. Original evidence inputs

All listed items are original/source evidence, not outputs of this comparison. Hashes are SHA-256. The archive is CRC-readable and its internal artifact hash manifest matches the original run files. The rehearsal manifest source hashes also match its referenced subset files.

| Original evidence | Repository path | SHA-256 |
|---|---|---|
| Immutable rehearsal ZIP | `artifact_share_staging/research_v1_development_rehearsal_662bd5c.zip` | `f688faff1cf4a25abe30d7e6516a0eab58bd0015a78d6863054c0435491d10f0` |
| Rehearsal attempts | `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/attempts.jsonl` | `54b183679376e6f6279106fbe714c90c124e4dce117190242efc56b58f71bc46` |
| Rehearsal pilot manifest | `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/pilot_manifest.json` | `b380da97defa9031f77538e50bf6b29b4100a52895a6cdb350733d6c3eff6570` |
| Rehearsal artifact hash manifest | `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/artifact_sha256.json` | `26b9c23d6d552868e009fff3677df1fc3ccd4a2c7b35ce9779c644d5418ce77f` |
| Referenced prepared Development subset | `evaluation/datasets/development_pilot/rehearsal_subsets/research_v1_seed_42/development_prepared.jsonl` | `05e1ed50a5bb6673a9caa86d5eadfd40a7bd332ba3ace9372f04345a730c3b98` |
| Referenced source Development candidates (integrity checked) | `evaluation/datasets/development_pilot/rehearsal_subsets/research_v1_seed_42/development_candidates.jsonl` | `9eeece456ff1a665bd82cdfde7035baa69df021def3fa651d8d1684e9a4e655c` |
| Referenced subset manifest | `evaluation/datasets/development_pilot/rehearsal_subsets/research_v1_seed_42/subset_manifest.json` | `a044f0fddf4f33f7c9be07ae482f1ae54005ac367442eee20983ceb7db0cf557` |
| Approved eligibility manifest | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json` | `75087c28f01e566be0572c149a182f5b02872f2973bcb32156bb607ecdac1eaa` |
| Approved manifest hash sidecar | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.file_sha256.txt` | `8141e37bef5a72cd93a3323417022338ca7aab6564e5a92e5f08cbe3f7830cae` |
| Approved eligibility candidates | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/development_eligible.jsonl` | `7ce9d93faf27a61b8fc810025febc4d375629f525565574b55208569bbd462ea` |
| Approved group assignments (reference file) | `evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/group_assignments.jsonl` | `8d73ffae8b91e66fce53278f665de6ecfa0ab69a5a51168976a52e231950df73` |
| Linked Development source manifest | `evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/manifest.json` | `5e55dbd17bf968eaa7768819945ab3adfc3b30d850817b859c63015e9db03764` |
| Linked Development verifier inputs | `evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/development_verifier_inputs.jsonl` | `51e001863d7622819c1f0a69755f041b476d89d28989a2054c04d1ab9675ad42` |
| Hash method implementation | `evaluation/data_preparation/run_verifier_attempts.py` | `761349b966e62385b7a17578564e34c13d3d210cc8ad4cabe97608025179b8d6` |
| Canonical JSON implementation | `app/game/models.py` | `c23baf7af8d8524bd6b113cc3c35fcf4a600e1b824203c6d18f0b40cddcb1f73` |
| Pilot results (integrity check only) | `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/pilot_results.json` | `5a1711d8aa35b50502cac75fea24980e1c4e09ef0127d6c3bd799a22199a33dc` |
| Unresolved ledger (integrity check only) | `evaluation/datasets/development_pilot/runs/research_v1_rehearsal_662bd5c/unresolved_not_attempted.jsonl` | `50cbfb0c2ba209529bc79828ff3ffa67c0e3cdb7d1323e43c2cf1f17b7d5e630` |

The approved manifest identifies `research_v1_exploratory_eligibility_approved_v1`, dataset version `research_v1_exploratory_v1`, and approved Development eligibility. Its `recording_authorized` and `collection_authorized` flags are both false; `frozen_protocol` is false. The linked source package manifest also identifies dataset version `research_v1_exploratory_v1`.

## 3. Recovered comparison methodology

Implementation: `evaluation/data_preparation/run_verifier_attempts.py` (`permitted_input()` and the roster hash construction), SHA-256 `761349b966e62385b7a17578564e34c13d3d210cc8ad4cabe97608025179b8d6`. Canonical serialization: `app/game/models.py` (`canonical_json()`), SHA-256 `c23baf7af8d8524bd6b113cc3c35fcf4a600e1b824203c6d18f0b40cddcb1f73`.

For each prepared rehearsal row, `permitted_input()` reads `verifier_input.benchmark`, `question`, `candidate_answer`, and `evidence_context`. The hash payload contains exactly `question`, `candidate_answer`, and normalized `context`; benchmark is explicitly excluded. Context rules follow the implementation: null/empty becomes null; string is retained; a list of strings is joined with two newlines; a list of structured passages uses `title` plus `text` or `sentence_text_extracted`, formats title and text with a newline, strips each passage, drops empty passages, and joins the remainder with two newlines. Other context types are rejected.

The payload is serialized with repository `canonical_json`: sorted keys, compact separators, `ensure_ascii=False`, and `allow_nan=False` (including its negative-zero normalization); SHA-256 is computed over the UTF-8 bytes. The approved side uses the corresponding fields in `development_verifier_inputs.jsonl` for IDs in `development_eligible.jsonl`. Hashes are compared without changing candidate IDs.

## 4. Integrity checks

- The rehearsal ZIP hash matches the supplied expected SHA-256; `ZipFile.testzip()` reported no corrupt member.
- `artifact_sha256.json` matched the attempts, pilot manifest, pilot results, and unresolved ledger.
- `pilot_manifest.json` source hashes matched the referenced `development_candidates.jsonl` and `development_prepared.jsonl`; the subset manifest was included in the hashed input inventory.
- The approved manifest sidecar matched the manifest file hash. All 744 eligible candidate IDs resolved to exactly one linked Development verifier-input row.
- Recomputed repository-contract hashes matched the stored rehearsal hash on all 52 attempt rows (13 candidates x 4 attempts). The approved input hash set contained unique hashes.

## 5. Candidate-level provenance comparison

| Rehearsal candidate ID | Approved candidate ID (if exact match) | Dataset / benchmark | Question ID | Group ID | Verifier-input SHA-256 | Classification | Attempts |
|---|---|---|---|---|---|---|---:|
| `gsm8k_train_2101::candidate_0` | `rx1-d2939939f399fd4497e9` | `gsm8k_train_2101` / GSM8K | `GSM8K:gsm8k_train_2101` | `gsm8k-q-bb3c60a2b215fdfb` | `7f5c29dc0f370d8cccee506b00317fd887f9dec955588bcc2b30749276528887` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_2101::candidate_1` | `rx1-04e62b82327f24c3336d` | `gsm8k_train_2101` / GSM8K | `GSM8K:gsm8k_train_2101` | `gsm8k-q-bb3c60a2b215fdfb` | `53f25ff532818b701d6b9170fdc3103331e07f5d60d54b358c20b7ac29b79567` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_3539::candidate_0` | `rx1-ff486b25aef85ab21ce7` | `gsm8k_train_3539` / GSM8K | `GSM8K:gsm8k_train_3539` | `gsm8k-q-dff1612e4967a07f` | `b225b7fd924c412fbea6175bcd8fb1a20f3e6eaf4fed8355b9af6c592e62d2b0` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_3539::candidate_1` | `rx1-4e434baec9f71473b45a` | `gsm8k_train_3539` / GSM8K | `GSM8K:gsm8k_train_3539` | `gsm8k-q-dff1612e4967a07f` | `964efc9536108a644025b2ce581c3b67ead360cab097ff7189b53aa259aa8187` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_4500::candidate_0` | `rx1-0c82b8ed0e8c241bcf22` | `gsm8k_train_4500` / GSM8K | `GSM8K:gsm8k_train_4500` | `gsm8k-q-d11afd4863388512` | `a3b8ed34ba975281b7be8519d4ceb8f6aa8d09ccc52a3f564e2ec901d9325ed8` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_4500::candidate_1` | `rx1-4296177b918425f2269e` | `gsm8k_train_4500` / GSM8K | `GSM8K:gsm8k_train_4500` | `gsm8k-q-d11afd4863388512` | `520a8923a177a163cc77ae2cc390890c496203eca10fbafefc993fd2e0e298c7` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_5541::candidate_0` | `rx1-2e879c21e7503403fdd2` | `gsm8k_train_5541` / GSM8K | `GSM8K:gsm8k_train_5541` | `gsm8k-q-80a7b694f4ff7a8d` | `47036c06ef60fa80b7c6902c4ac76e557f7a42c5bd51451722e4c46ece8483b3` | `INPUT_EQUIVALENT` | 4 |
| `gsm8k_train_6691::candidate_0` | `rx1-9159837fc0687a096eab` | `gsm8k_train_6691` / GSM8K | `GSM8K:gsm8k_train_6691` | `gsm8k-q-60e26df320cfcb5d` | `e89d76e7bb2bce2fb334d28d4c1905259146b507581399a483d8f9c00b3ec2b7` | `INPUT_EQUIVALENT` | 4 |
| `hotpot_5a710d155542994082a3e520::candidate_0` | `NONE` | `hotpot_5a710d155542994082a3e520` / HotpotQA | `HotpotQA:hotpot_5a710d155542994082a3e520` | `hotpotqa-q-edfbcfe7ca058b5e` | `1d81c6b795ed71490100539a5c03d0f011cffde3534b82930db7d333dab6a37c` | `SAME_GROUP_NO_EXACT_INPUT_MATCH` | 4 |
| `hotpot_5a7147fd5542994082a3e758::candidate_0` | `NONE` | `hotpot_5a7147fd5542994082a3e758` / HotpotQA | `HotpotQA:hotpot_5a7147fd5542994082a3e758` | `hotpotqa-q-ddd3ab7b121be4fe` | `8f3047c4db44e01b92e73bcd0fc01860f9f033c6261b062fc1011c8b9e04313d` | `SAME_GROUP_NO_EXACT_INPUT_MATCH` | 4 |
| `hotpot_5ade66e1554299728e26c713::candidate_0` | `NONE` | `hotpot_5ade66e1554299728e26c713` / HotpotQA | `HotpotQA:hotpot_5ade66e1554299728e26c713` | `hotpotqa-q-01efd584ea7ae8cf` | `74cf4698ceb7c63c484c69b5aabf9a6f51d1150f4df1fdfbb309df8c24f93199` | `GROUP_NOT_PRESENT_IN_APPROVED_ROSTER` | 4 |
| `hotpot_5ae25c815542992decbdcccc::candidate_0` | `NONE` | `hotpot_5ae25c815542992decbdcccc` / HotpotQA | `HotpotQA:hotpot_5ae25c815542992decbdcccc` | `hotpotqa-q-507e4b2663857928` | `5e028e2324d8e125970743b6dcb388d3e728874c4c8ba349130294f590f1be0b` | `SAME_GROUP_NO_EXACT_INPUT_MATCH` | 4 |
| `hotpot_5ae785685542994a481bbd47::candidate_0` | `NONE` | `hotpot_5ae785685542994a481bbd47` / HotpotQA | `HotpotQA:hotpot_5ae785685542994a481bbd47` | `hotpotqa-q-4801fbf1b400048c` | `0b4a075aa04244e4b96cc30e57ea416c90d5b241835c055a1da19c0ca0013c2d` | `SAME_GROUP_NO_EXACT_INPUT_MATCH` | 4 |

No candidate IDs overlap between the rehearsal and approved roster. For the eight `INPUT_EQUIVALENT` rows, the approved and rehearsal verifier-input SHA-256 values are equal, and the recorded benchmark, question ID, and group ID also agree. Four rows share question/group identity without an exact input hash; one row has no corresponding approved group/question identity. The JSON crosswalk contains per-row verifier identities, states, and source-native execution IDs. The source schema does not provide a separate attempt ID; no synthetic attempt ID has been invented.

## 6. Attempt-level implications

The eight exact input-equivalent rehearsal candidates have four retained attempt rows each, totaling 32 of 52 rows. Each candidate's four rows identify the `confidence`, `evidence`, `rule`, and `semantic` verifier. The crosswalk lists the source-native `execution_id` and state for each row; where the source repeats an execution ID across a candidate's verifier rows, the verifier identity distinguishes the rows.

**Disposition: `CONDITIONAL: INPUT-LEVEL EQUIVALENCE ONLY`.** These are historical rehearsal attempts under the rehearsal run's own IDs and provenance. Hash equality does not make them canonical recordings for approved candidate IDs or establish labels or fitting eligibility.

## 7. What passed vs what remains conditional

| TESTED / VERIFIED | CONDITIONAL / NOT ESTABLISHED |
|---|---|
| Archive readability and integrity hashes | Candidate-ID identity/equivalence |
| Repository-defined hash method applied; stored rehearsal hashes reproduced | Canonical recording identity across the two candidate namespaces |
| 13 rehearsal candidates and 52 attempt rows | Label equivalence |
| 8 exact input hashes and 32 associated attempts | Automatic admission to policy fitting |
| 4 same-question/group nonmatches and 1 absent group | Authorization to use these records in fitting or collection |

## 8. Limitations and required review

Input-hash equivalence does not mean candidate IDs are identical. No IDs were remapped, aliased, or rewritten. The immutable rehearsal and approved eligibility/source files remain unchanged. Input equivalence alone does not establish canonical recording identity, label equivalence, or policy-fitting eligibility. Use beyond a provenance-preserving compatibility record requires explicit review and authorization. Collection, fitting, optimization, and Final Test evaluation remain unauthorized by this comparison. Contamination-flag reconciliation is outside scope.

## 9. Reproducibility information

- Repository branch: `tanmayee-integration`
- Repository HEAD: `58bb214671a6f9224b4b88b8a01c67233363711e`
- Comparison generation date (UTC): `2026-11-13`
- Reproduce using the source paths and hash contract in Sections 2-3; compare `candidate_id` namespaces only as separate identifiers.
- Machine-readable crosswalk: `docs/experiment2-rehearsal-provenance-crosswalk.json`
- Crosswalk SHA-256: `310c00ad8aad4a73522f38524f6d889d90d782b3eeaf1e3c290f5c3e61bb0119`.
