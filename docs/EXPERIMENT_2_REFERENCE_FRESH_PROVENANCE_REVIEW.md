\# Experiment 2 — Reference Fresh Provenance Review



\## 1. Purpose



This note records the provenance review of `person3-prerequisite-artifacts.zip` and clarifies how its contents relate to the existing Experiment 2 evidence.



The archive is treated as a separate exploratory evidence package. It is not merged into the historical `multitask-policy42` campaign evidence.



\## 2. Archive identification



The archive contains artifacts associated with `reference-fresh-v1`, including:



\- Flexible-team study artifacts

\- History and Development records

\- Preparation, analysis, and policy-fitting artifacts

\- Reproducibility and persistence-validation documentation

\- `artifact-identities.json`

\- `partitions.json`

\- `protocol.json`

\- `groups.json`

\- `amendment.json`

\- `reserved-seal.json`

\- `fit/training-manifest.json`

\- `fit/development-evaluation.json`



\## 3. Provenance findings



\### 3.1 Study identity



The artifact identity record reports:



\- Study ID: `86d17f7baa56a0a7c3a1ffcfb4b5914aba643fa59c99d17e64f1a7f1f00431f6`

\- Matrix ID: `4d7126a8d652a35045b2682e222e0fd767fef43a5b8b6d9d9e4f5cc074fe90c9`

\- Unfitted contract ID: `284e7f29545d2d1cb26f783ee6d241a2d7224de5a5ba35afe2fbb7d60ddeb5a7`

\- Resource manifest ID: `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`

\- Projected resource manifest ID: `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`



The `policy\_id` and `candidate\_freeze\_id` fields are null. Therefore, this identity record does not establish a frozen fitted policy or candidate freeze.



\### 3.2 Protocol continuity



The protocol identifies:



\- Version: `reference-fresh-v1`

\- Resource transition: `current\_reference\_service\_v1`

\- Study description: resumed exploratory study, not an uninterrupted campaign



This is an explicit limitation on treating the archive as continuous historical campaign evidence.



\### 3.3 Development artifacts



The archive contains an empirical training manifest and a Development evaluation.



The Development evaluation reports:



\- Role: `development`

\- Manifest ID: `b4279d31ebc6a490bc3a576aa37094880f314b63ed9e1ce294d4632027536a2a`

\- Compatibility ID: `1fc178efc13e8862934fc09b2b60abcacddbfe96332e51075e6f91800ee46a17`

\- Execution configuration ID: `7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`



The manifest and compatibility IDs match those previously associated with `reference-50-v1`. Consequently, this archive does not establish an independent replacement Development dataset.



\### 3.4 Authorization amendment



The archive includes an amendment identified as `reference\_post\_development\_50\_v1`.



Its recorded authorization concerns the 50% post-development floor and 80 reserved calls / 100 generations within the stated cumulative ceilings.



This is evidence of the recorded amendment in this exploratory package. It does not establish continuity with the original historical campaign.



\### 3.5 Final Test reservation



The training manifest contains Final Test reservation metadata.



This review does not inspect, load, evaluate, or otherwise access any Final Test payload. Reservation metadata is not treated as authorization to access protected evaluation data.



\## 4. Relationship to the original Experiment 2 evidence



This archive does not resolve the previously identified historical provenance gaps, including:



\- Missing original Arithmetic and Factual training manifests

\- Missing original Arithmetic and Factual Development evaluations

\- Missing original execution-source custody archive

\- Unresolved source revision and collection-environment verification

\- Outstanding source-to-archive hash and compatibility questions



The `reference-fresh-v1` package must therefore remain distinct from the original `multitask-policy42` campaign.



\## 5. Classification and recommended handling



Classification: \*\*Separate exploratory evidence — Development artifacts present; historical campaign continuity not established.\*\*



Recommended handling:



1\. Preserve the original ZIP unchanged.

2\. Retain this review alongside the Experiment 2 documentation.

3\. Do not merge these artifacts into the original `multitask-policy42` provenance package.

4\. Do not describe the archive as closing the original provenance gaps.

5\. Do not access Final Test payloads.

6\. Do not initiate additional verifier executions as part of this documentation review.

7\. Keep the existing budget sensitivity results labelled as Development-only historical analysis.



\## 6. Status conclusion



The archive provides useful evidence of a separate `reference-fresh-v1` exploratory study and its Development artifacts. However, the protocol's resumed-study designation, missing policy and candidate-freeze identities, and shared Development manifest and compatibility IDs prevent it from serving as proof of uninterrupted original campaign provenance.



\*\*The original Experiment 2 provenance limitations remain open. This review does not change the formal completion status of Experiment 2.\*\*
