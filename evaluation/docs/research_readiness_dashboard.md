# Research readiness dashboard

Generated from `evaluation/config/research_v1/readiness_status.json` after `python -m evaluation.scripts.check_research_readiness`. This dashboard does not approve or authorize anything.

## Overall

`READY_FOR_APPROVAL`. Execution is not ready. Empirical experiments are not complete. Development collection is not authorized. Final Test scoring is not authorized. Experiment 3 is `READY_FOR_APPROVAL`.

## Requirements

| Requirement | Status | Approval | Authorization |
|---|---|---|---|
| Supported task populations | TECHNICALLY_READY | PENDING | Not applicable |
| Verifier and resource configuration | READY_FOR_APPROVAL | PENDING | NOT_AUTHORIZED |
| Datasets and labels | READY_FOR_APPROVAL | Eligibility approved; collection not approved | NOT_AUTHORIZED |
| Development evidence corpus | READY_FOR_APPROVAL | PENDING | NOT_AUTHORIZED |
| Final Test custody | NOT_AUTHORIZED | Enforcement implemented; independent custody NOT_ESTABLISHED | NOT_AUTHORIZED |
| Scientific protocols | READY_FOR_APPROVAL | PENDING | NOT_AUTHORIZED |
| Collection and scoring | NOT_AUTHORIZED | PENDING | NOT_AUTHORIZED |

The Final Test v2 experimental configuration is not frozen. An unsigned researcher statement says the team approved the experimental decisions. The approved values and snapshot hashes were not recovered, so protocol freeze is `NOT_COMPLETE` and execution is not ready. See `final_test_v2_experimental_freeze_report.md`.

Final Test v2 custody status is `SELF_CUSTODY`, recorded by the 2026-11-13 amendment. Independent custody is `NOT_ESTABLISHED`. The label file and a backup are outside the Git repository. The recorded hash was verified without parsing the file. The directory ACL grants only the relocating account; that account can still read the file. Labels stay sealed until the study configuration, policies, baselines, and evaluation rules are frozen. Research-lead approval of the amendment is `PENDING`. A separate research-lead scoring authorization is `PENDING`. The researcher's earlier unsigned confirmation is preserved and does not unseal the labels. Final Test execution is `NOT_RUN`. The amendment is `final_test_self_custody_amendment_2026-11-13.md`.

Model-weight snapshot hashes remain `UNKNOWN`. The canonical evidence path is the corpus file and resolves. Failure groups are structural shared resources, not one group of all four verifiers, and they are not a measured correlation.

The dataset audit reports 8,000 / 2,000 / 2,000 unified rows, 372 eligible groups, HotpotQA 185, and zero identifier overlap with the sealed Final Test manifest. The corpus hash matches. Coverage counts are 184 HotpotQA supporting-title retrievals, 1 miss, and 20 questions with any chunk at cosine 0.78 or higher. FEVER is not in the canonical source. The label file was not opened.
