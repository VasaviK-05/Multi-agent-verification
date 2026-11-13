# Final Test v2 repository self-custody

The 2026-11-13 amendment sets operational custody to `SELF_CUSTODY` and moves the label file outside this repository. It preserves the records below. Research-lead approval of that amendment is pending, and the labels stay sealed until the study configuration, policies, baselines, and evaluation rules are frozen. See `final_test_self_custody_amendment_2026-11-13.md`.

This protocol records repository-level self-custody. It does not establish independent custody, freeze the research protocol, release labels, or authorize scoring.

## Identity and non-independence

The researcher is the dataset creator and developer. That identity is the appointee in `evaluation/config/final_test_v2_custodian_appointment.json`. This protocol does not repeat the appointee's name. The appointment roles are `dataset_creator` and `designated_final_test_custodian`. `independent_custodian` is false. `custody_independence` is `NOT_INDEPENDENT`.

No independent custodian is available. Independent custody remains `NOT_ESTABLISHED`. The pending record `evaluation/config/research_v1/independent_custodian_appointment.json` is unchanged. A self-custody record cannot satisfy `validate_independent_appointment`, `release_blockers`, or `scoring_decision`.

The self-custody declaration is `evaluation/config/research_v1/final_test_self_custody.json`. Its mode is `SELF_CUSTODY`. `independent_custody` is false. `independent_custodian` is false. It has no signature.

## Repository scope

Self-custody covers application checks and recorded metadata:

- The sealed dataset version is `research_v1_final_test_v2_exploratory_v1`.
- Recorded manifest content SHA-256: `e572093a4f0420c03316c89c83b6a7ab665af3af894d19a1428a6b091d3319ee`.
- Recorded roster SHA-256: `3f8fcbf1e698174a9a7cf6c586ec51048bcc07ca11154b36fdef0dadc7796208`.
- Recorded label SHA-256, not recomputed by this protocol: `35b126ba350a942f42f11d1845e16e01fd755516d20b53faf3aaf616143858a6`.
- Protocol SHA-256: null. Protocol freeze is `PENDING`.

These hashes are previously recorded values. This protocol does not open or hash the label file.

`assess_self_custody` reports self-custody `ACKNOWLEDGED` when the declaration stays non-independent and the limitations acknowledgment is true. It always reports independent custody `NOT_ESTABLISHED`, `signed_evidence` false, protocol freeze `PENDING`, and scoring `NOT_AUTHORIZED`. Release is `AUTHORIZED` only from the explicit release confirmation, and only when supplied dataset metadata matches the recorded version, manifest hash, and roster hash.

## Authorization pathway

`self_release_blockers` and `self_scoring_blockers` in `evaluation/research_readiness/v2_authorization.py` are separate from the independent gate.

- Release requires a signed protocol freeze bound to a protocol hash. A missing or null protocol hash blocks release.
- Release requires its own signed record. A protocol freeze does not release labels.
- Scoring requires a separate signed record with scope `final_test_v2_self_custody_scoring`. Release does not grant scoring. A protocol freeze alone does not grant scoring.
- Release and scoring must match the recorded manifest hash, roster hash, and protocol hash.
- Missing, unsigned, template, expired, and revoked records fail closed.
- A self-custody record that sets `independent_custody` true, `independent_custodian` true, or the role `independent_custodian` is rejected.
- The independent label gate, `refuse_sealed_label_without_release`, does not accept a self-custody release. The scoring command still calls the independent refusal and then `refuse_self_custody_live`.

The live declaration is not a signed protocol, release, or scoring record.

## Unsigned verbal acknowledgment

The same declaration records `protocol_approval.status` `VERBAL_TEAM_APPROVAL_STATED`. `signed_evidence` is false and `signature` is null. That states a verbal or team protocol approval. It is not a signature, not minutes, and not independent verification.

`unsigned_release_decision` and `unsigned_scoring_decision` accept a researcher confirmation with `evidence_form` `UNSIGNED_VERBAL_ACKNOWLEDGMENT` or `RESEARCHER_SELF_AUTHORIZATION`. A confirmation that carries a signature is rejected on this path. Protocol approval does not confirm release. A release confirmation does not confirm scoring. The live declaration has `self_custody_limitations_acknowledged` true and `release_confirmed` true. Scoring is a separate object, `scoring_authorization`, with `action` `SCORING` and `release_confirmed` false. The top-level `scoring_confirmed` field remains false so the release record does not grant scoring. `label_release` remains `NOT_AUTHORIZED`. Neither confirmation opens the label file or runs the experiment.

A permitted unsigned decision does not open labels and does not run the scorer. `score_final_test_v2.py` does not load a confirmation file.

## Leakage, access, and bias

The researcher who created the dataset can still read the Git-ignored label file through the filesystem. Repository checks do not remove that access. That leaves residual leakage and researcher-bias risk: selection, documentation, and later analysis were done by the same person who can see the sealed labels.

Existing metadata, not a new label inspection, records identifier overlap 0 and `semantic_leakage` `NOT_CLAIMED`. The retired provisional partition is a different dataset and remains retired. Exact identity checks do not rule out paraphrase leakage or knowledge the researcher already has.

Final Test labels must not be used for development, training, tuning, reputation fitting, policy selection, or verifier changes. Development collection stays on its own guard and must not receive a Final Test path.

## What this protocol does not do

No operating-system access restriction, account isolation, or external storage transfer is claimed or configured. Results scored under this pathway must disclose self-custody and the residual access risk. Verbal protocol approval is not signed evidence. Release and scoring are both recorded, and they remain separate unsigned confirmations. The experiment has not been run.
