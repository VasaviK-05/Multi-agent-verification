# Final Test v2 custody amendment, 2026-11-13

This amendment changes the operational custody status to `SELF_CUSTODY`. It is not independent custody and not independent verification. The original designated appointment, the pending independent-appointment record, and the researcher self-custody declaration are preserved and were not rewritten.

## Label location

The label file is no longer in the Git working tree. It is stored, with a byte-for-byte backup, outside the repository. The location record is `evaluation/config/research_v1/final_test_label_custody_location.json`.

The recorded SHA-256 `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6` matched the file before the move and matched both the relocated file and the backup. The check hashed bytes. It did not parse the file. The copy in `evaluation/datasets/_custodian/final_test_research_v1_v2/` was removed only after those hashes matched. Its size remained 1,390,739 bytes.

The directory ACL now grants only the account that performed the relocation. Inherited `Authenticated Users` and `Users` entries were removed. That account can still read the file. This is self-custody, not an independent access boundary.

A dated access log is stored beside the label file. It records the relocation, the hash, and that no other account was granted access. It does not contain label rows.

## Previous exposure

The retired provisional Final Test is a different dataset. Its contamination audit found 807 of 2,638 groups already exposed and remains the record of that exposure. That audit did not open the v2 label file.

The v2 label file previously sat in the Git-ignored working tree, where the developer account could read it. Identity audits of v2 record `labels_opened` false. This amendment does not claim the labels were never readable. It records that this relocation hashed the bytes and did not parse them, and that no Final Test experiment was run.

## Seal and scoring

The labels stay sealed until the study configuration, policies, baselines, and evaluation rules are frozen. None of those is frozen.

The research lead has not approved this amendment. A separate research-lead scoring authorization is also pending. The researcher's earlier unsigned scoring confirmation remains in the preserved declaration. It does not unseal the labels and it is not research-lead approval. `signed_evidence` is false.

## Methodology

Self-custody and these limitations are part of the research methodology in `scientific_protocol_index.md`. Any later Final Test result must disclose that the dataset creator retained access, that repository controls do not stop a direct read, and that independent custody was not established.
