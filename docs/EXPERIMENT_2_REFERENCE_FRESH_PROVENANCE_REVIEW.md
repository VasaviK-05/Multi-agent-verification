# Experiment 2 — Reference Fresh Provenance Review

## 1. Purpose

This note records the provenance review of `person3-prerequisite-artifacts.zip` and clarifies how its contents relate to the original historical `multitask-policy42` campaign.

The archive is treated as a separate exploratory evidence package. It is not merged into the historical campaign evidence.

This review incorporates the subsequent recovery of original Arithmetic and Factual historical artifacts documented in `recovery_package_v2.zip`.

## 2. Archive identification

The archive contains artifacts associated with `reference-fresh-v1`, including:

- Flexible-team study artifacts
- History and Development records
- Preparation, analysis, and policy-fitting artifacts
- Reproducibility and persistence-validation documentation
- `artifact-identities.json`
- `partitions.json`
- `protocol.json`
- `groups.json`
- `amendment.json`
- `reserved-seal.json`
- `fit/training-manifest.json`
- `fit/development-evaluation.json`

## 3. Provenance findings

### 3.1 Study identity

The artifact identity record reports:

- Study ID: `86d17f7baa56a0a7c3a1ffcfb4b5914aba643fa59c99d17e64f1a7f1f00431f6`
- Matrix ID: `4d7126a8d652a35045b2682e222e0fd767fef43a5b8b6d9d9e4f5cc074fe90c9`
- Unfitted contract ID: `284e7f29545d2d1cb26f783ee6d241a2d7224de5a5ba35afe2fbb7d60ddeb5a7`
- Resource manifest ID: `e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`
- Projected resource manifest ID: `310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`

The `policy_id` and `candidate_freeze_id` fields are null. Therefore, this identity record does not establish a frozen fitted policy or candidate freeze.

### 3.2 Protocol continuity

The protocol identifies:

- Version: `reference-fresh-v1`
- Resource transition: `current_reference_service_v1`
- Study description: resumed exploratory study, not an uninterrupted campaign

This is an explicit limitation on treating the archive as continuous historical campaign evidence.

### 3.3 Development artifacts

The archive contains an empirical training manifest and a Development evaluation.

The Development evaluation reports:

- Role: `development`
- Manifest ID: `b4279d31ebc6a490bc3a576aa37094880f314b63ed9e1ce294d4632027536a2a`
- Compatibility ID: `1fc178efc13e8862934fc09b2b60abcacddbfe96332e51075e6f91800ee46a17`
- Execution configuration ID: `7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`

The manifest and compatibility IDs match those previously associated with `reference-50-v1`. Consequently, this archive does not establish an independent replacement Development dataset.

### 3.4 Authorization amendment

The archive includes an amendment identified as `reference_post_development_50_v1`.

Its recorded authorization concerns the 50% post-development floor and 80 reserved calls / 100 generations within the stated cumulative ceilings.

This is evidence of the recorded amendment in this exploratory package. It does not establish continuity with the original historical campaign.

### 3.5 Final Test reservation

The training manifest contains Final Test reservation metadata.

This review does not inspect, load, evaluate, or otherwise access any Final Test payload. Reservation metadata is not treated as authorization to access protected evaluation data.

## 4. Relationship to the original Experiment 2 evidence

The `reference-fresh-v1` archive remains separate from the original historical `multitask-policy42` campaign.

Subsequent recovery work has established that the following original historical artifacts are now available:

- Original Arithmetic training manifest.
- Original Factual training manifest.
- Original Arithmetic Development evaluation.
- Original Factual Development evaluation.
- Arithmetic and Factual calibration files.
- Arithmetic and Factual recording bundles.
- Arithmetic and Factual collection reports.
- Original producer script, recovered and independently hash-verified.
- Four original country-data source snapshots, recovered and hash-verified.

The updated recovery package is `recovery_package_v2.zip`.

Its recorded package SHA-256 is:

`b8b070eb96a2a608c52e9a504965cc88f06a97a444efabc7db526fc8810504c2`

Independent package verification established:

- 30 ZIP members.
- 29 manifest entries.
- All 29 manifest hashes and file sizes matched.
- The recovered producer script matched its exact recorded SHA-256.

The producer script SHA-256 is:

`174a7b965a15e9a6540f06705c7d330b81de9de45187a638dded4acb1bfaa5ea`

These recovered historical artifacts address the earlier missing-manifest and missing-Development-evaluation findings. They do not change the classification of `reference-fresh-v1` or establish continuity between the two studies.

## 5. Remaining historical provenance limitations

The following limitations remain outstanding in the original historical campaign evidence:

1. The original application source corresponding to the recorded application source digest has not been recovered or independently verified.
2. The original execution-source ZIP remains unavailable.
3. The collection and fit application source digests could not be independently reproduced from the available source trees.
4. Detailed hardware inventory is not available.
5. A separate signed authorization document has not been recovered, although authorization references exist in the recovered records.

The additional source investigation covered Git history, dangling Git objects, accessible working-tree sources, and available source snapshots.

The exact original producer script has been recovered. It must not be confused with the still-unavailable application source.

These remaining limitations do not mean the recovered historical manifests, evaluations, recordings, or producer script are missing.

## 6. Classification and recommended handling

Classification:

**Separate exploratory evidence — Development artifacts present; historical campaign continuity not established.**

Recommended handling:

1. Preserve the original `person3-prerequisite-artifacts.zip` unchanged.
2. Retain this review alongside the Experiment 2 documentation.
3. Do not merge these exploratory artifacts into the original `multitask-policy42` provenance package.
4. Do not describe `reference-fresh-v1` as an uninterrupted continuation of the original historical campaign.
5. Do not access Final Test payloads.
6. Do not initiate additional verifier executions as part of this documentation review.
7. Keep the existing budget sensitivity results labelled as Development-only historical analysis.
8. Use `recovery_package_v2.zip` as the separately verified source of the recovered original historical artifacts.

## 7. Status conclusion

The `reference-fresh-v1` archive provides useful evidence of a separate exploratory study and its Development artifacts.

Its resumed-study designation, null policy and candidate-freeze identities, and shared Development manifest and compatibility IDs prevent it from serving as proof of uninterrupted original campaign provenance.

The original historical Arithmetic and Factual training manifests and Development evaluations have since been recovered and hash-verified. The original producer script and four country-data source snapshots have also been verified.

However, the original application source and execution-source ZIP remain unavailable.

**The `reference-fresh-v1` archive remains separate exploratory evidence. The original historical campaign is substantially recovered but retains source-provenance limitations. Formal Experiment 2 completion is not established by this review.**