# Final Test custody and partition record

## Final Test v2 custody (2026-11-11)

The dataset creator, Raunak, is the designated Final Test custodian for `research_v1_final_test_v2_exploratory_v1`. There is no independent custodian. This appointment does not authorize evaluation or label release.

| Field | Value |
|---|---|
| Previous status | `PENDING_NO_INDEPENDENT_CUSTODIAN` |
| Custody status | `DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR` |
| Independence | `NOT_INDEPENDENT` |
| Appointment | `evaluation/config/final_test_v2_custodian_appointment.json` |
| Custody record | `DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR:Raunak` |
| Evaluation authorization | `PENDING` |
| Label release | `NOT_AUTHORIZED` |
| Protocol freeze | `PENDING` |
| Manifest status | `NOT_AUTHORIZED`, `enabled: false` |
| Manifest SHA-256 | `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee` |

The custodian's recorded responsibilities are:

- Maintain label confidentiality.
- Prevent Final Test leakage into Development, training, tuning, reputation fitting, or policy selection.
- Preserve the existing Final Test v2 dataset and its hashes.
- Release labels only after protocol freeze and explicit authorization.

Label protection is a caller gate, not an operating-system boundary. `read_custodian_labels` refuses `verifier_developer` and `development_experiment_runner`, refuses Development, training, tuning, reputation-fitting, policy-selection, and verifier-development purposes, and refuses every caller while `evaluation_authorization` is `PENDING`. The custodian appointment cannot be passed as the authorization record. The labels stay in `evaluation/datasets/_custodian/final_test_research_v1_v2/`. A process with direct filesystem access can still read that Git-ignored directory. No OS ACL boundary is claimed.

The custody update did not change candidate labels, question text, candidate IDs, reservation entries, or example content hashes. Preserved hashes: label file `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6`, roster `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208`, reservation entries `a33be6afcd2233479a05ee9c9444d1457d5b98d07c0c10e5bbef5191fab4d496`. The reservation file hash changed from `adc199f6eb77e62b53b72121bb021642c663f8e57ccf7b72c6ce6ac7b3b9d1e8` to `e7cea941837697093bd18e499f2d78f8bea550a33fee4a9dff2e9738995d7611` because its `custody_record` field was updated. The previous manifest hash was `478001c764dd17424127652cfc6b587a12e94e30aa5f74b4871dd3e0cb499031`.

`final_test_workflow readiness` on this manifest stays **NOT APPROVED** (`evaluation_authorization_pending`). Confirmatory readiness stays **BLOCKED** until the protocol approvals and readiness checks are complete and a separate authorization record is signed. Custody does not clear that gate.

## Retired provisional partition

**The provisional `research_v1_final_test_provisional_v1` partition is retired (2026-11-11) and must never be used for confirmatory evaluation.** 807 of its groups were previously exposed (`final_test_contamination_audit.md`), and `read_custodian_labels` now refuses its manifest. It was generated from GSM8K test and HotpotQA validation source rows, audited against research_v1 History and Development only, and hash-validated. It remains **disabled and NOT_AUTHORIZED**. It is **not genuinely protected**: Windows ACL inspection shows inherited `NT AUTHORITY\Authenticated Users` Modify permission and `BUILTIN\Users` read permission on the custodian directory. There is no independent custodian identity configured. An ordinary process with filesystem access can bypass the Python authorization gate and read the labels. Do not use these files for confirmatory evaluation or treat the answers as secret.

## Generated artifacts and freeze record

- Evaluation roster and audit: `evaluation/datasets/final_test_research_v1_eval_v1/`
- Custodian label payload and duplicate manifest: `evaluation/datasets/_custodian/final_test_research_v1_v1/`
- Configuration: `evaluation/config/final_test_research_v1_provisional.yaml`
- Source: GSM8K `openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866`; HotpotQA `hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab`.
- Groups: 1,319 per benchmark (2,638 total); candidates: 2,638, one benchmark-gold candidate per group.
- Labels: 2,638 verified correct, 0 verified incorrect, 0 unresolved. Provenance is source-backed deterministic benchmark-gold validation, not human adjudication. The all-correct label distribution makes this pool unsuitable for estimating false acceptance or serving as a complete validation benchmark.
- Operational sample rationale: equal benchmark allocation at the full fresh GSM8K test source-pool limit, after exact leakage/context exclusions. This is provisional, not a power calculation; no effect-size, variance, confidence-width, or statistical guarantee is claimed.
- Manifest SHA-256: `cc186376c9d884ecadbfed342e9ea40773840cc305e11c2d7327f42e1db87e46`.
- Evaluation roster SHA-256: `5af06474035ec00d0009b9fd5b9e232120500fc236302637238c74ee98f823c4`.
- Question roster SHA-256: `2845e24f45de71aaa1f7d4da5640f443d2731d2412c9ea469c903a55c92b448c`.
- Candidate roster SHA-256: `913a806e040bf64b53081f37430598524c44e1932c54240d1ae6fbbfb4d46f48`.
- Label payload SHA-256: `22a6274ded455acbf4a13f0456b2c7a47c056249d9c32793bf2f84f7eb567b93`.
- Leakage audit SHA-256: `1d32e0f685a4016f6a2a377175bd8bc7f84a07f43ced824bf253ee030e9f5bb0`.
- Source hashes and generator/config hashes are recorded in the manifest. `evaluation/datasets/` is Git-ignored; the labels are not committed to the normal developer branch.

The status `PROVISIONALLY_FROZEN_AFTER_HASH_AND_AUDIT` records reproducible outputs and integrity checks only. The builder refuses non-empty output directories; future changes require a new explicitly versioned output directory/configuration. This is not an OS write-protected or security-enforced freeze.

## Access workflow and actual enforcement

`read_custodian_labels` denies access unless an authorization file says `approved: true` and matches the named person, evaluation purpose, and exact manifest hash. Before returning rows it validates manifest, roster, label and audit hashes and writes an access event containing identity, purpose, time, and artifact hashes. The tests cover default denial and authorized event logging. This gate controls only clients that call this Python function. It does not prevent direct file reads, and the event log is not tamper-proof.

The custodian directory currently has broad inherited ACL entries (including Authenticated Users Modify and Users Read). The generated storage is therefore only an organizational path separation, not a protected boundary. Human custody remains pending; no custodian is invented. Final Test stays unauthorized and disabled.

Before protection can be claimed, a named independent custodian must move or recreate the label payload in a separately controlled account/volume, remove inherited broad access, verify an unauthorized Windows account is denied direct reads, protect the authorization and access log, and independently verify hashes. This must be performed by the person administering that security boundary; the current sandbox identity cannot establish independent custody. Separately, an authorized protocol owner must approve benchmark population, candidate/label policy, license/citation, sample-size rationale, analysis plan, verifier settings, and confirmatory use. None of those approvals are implied by file creation.

## Manual decisions and limitations

- Confirm source license and citation terms and formally approve the source revisions.
- Approve or replace the provisional operational allocation; there is no power calculation.
- Decide whether an all-gold-only Final Test is scientifically useful and define a permitted negative-candidate policy if needed. Do not manufacture negatives.
- Obtain independent human custody and verified OS-level ACL protection.
- Complete method/readiness approvals before evaluation. The readiness validator remains confirmatory BLOCKED.
- Exact matching does not rule out semantic/paraphrase leakage. Some prior borrowed History/Development records lack donor provenance; see the leakage audit record.

To validate hashes and provenance without printing labels:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from evaluation.data_preparation.final_test_workflow import validate_artifacts; p=Path('evaluation/datasets'); print(validate_artifacts(p/'final_test_research_v1_eval_v1/evaluation_roster.jsonl', p/'_custodian/final_test_research_v1_v1/custodian_labels.jsonl', p/'_custodian/final_test_research_v1_v1/manifest.json'))"
```
