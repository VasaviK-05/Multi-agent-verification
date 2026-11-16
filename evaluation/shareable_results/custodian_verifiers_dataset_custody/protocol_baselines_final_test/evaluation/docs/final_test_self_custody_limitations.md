# Final Test v2 self-custody limitations

Self-custody is not independent custody. The dataset creator and researcher is the custodian because no independent custodian is available. `evaluation/config/research_v1/final_test_self_custody.json` records that fact. It does not make `independent_custodian` true, and the independent appointment is unchanged.

Repository-level protections do not prevent direct filesystem access. The label file remains in the Git-ignored custodian directory. Application refusals in `read_custodian_labels`, `score_final_test_v2.py`, and the baseline runner apply only when code calls those paths. They do not stop a direct read.

No OS-level access restrictions exist. This protocol does not set Windows ACLs, account isolation, or filesystem permissions. `os_access_restriction` is `NOT_IMPLEMENTED`.

The researcher may have access to sealed labels. The label file is now outside the Git repository, and the directory ACL grants only the relocating account. That account can still read the file. This creates residual leakage and researcher-bias risk. Any future result must disclose this limitation. The 2026-11-13 amendment does not claim independent custody. Research-lead approval of the amendment, and a separate research-lead scoring authorization, are pending. The labels stay sealed until the study configuration, policies, baselines, and evaluation rules are frozen.

The researcher has explicitly acknowledged these limitations and confirmed release. That confirmation is `RESEARCHER_SELF_AUTHORIZATION` with `signed_evidence` false. It is not a signature and not independent verification.

Protocol freeze remains `PENDING` because no protocol hash is frozen. Self-custody release is `AUTHORIZED`. Scoring is `AUTHORIZED` by a separate unsigned confirmation. That confirmation is not a signature and not independent approval. The manifest `label_release` remains `NOT_AUTHORIZED`. Final Test labels remain sealed. No Final Test experiment has been run. Independent custody remains not established.
