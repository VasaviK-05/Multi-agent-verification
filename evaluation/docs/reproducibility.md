# Reproducibility

## 1. Purpose and scope

This document defines the reproducibility requirements and evidence for the capstone's frozen-policy transfer evaluation.

The evaluation follows `docs/upstream_transfer_evaluation.md`.

It is an additive transfer-evaluation contract, not strict historical reproduction, a new fitting objective or a deployment policy.

The original historical source snapshot and environment are unavailable. Historical/current collector equivalence is therefore not established.

The transfer procedure applies the unchanged frozen decision rule to fresh verifier reports produced under a separately declared current implementation.

This document records source, environment, policy, resource, experiment and output reproducibility requirements. It distinguishes verified software behaviour from actual empirical experiment results.

## 2. Reproducibility principles

- Preserve original policy artifact bytes, IDs and strategy probabilities.
- Do not refit policies or update reputation during transfer evaluation.
- Keep historical, current-clean and current-altered recordings separate.
- Compare current-clean and current-altered as the paired intervention conditions.
- Record all actual source and resource differences.
- Preserve failures, abstentions and every started attempt.
- Keep experiment configurations, labels and source snapshots private under ignored `build/` paths.
- Do not claim historical source equivalence or held-out poisoning resistance.

## 3. Source-code reproducibility

Before collecting fresh reports, snapshot the exact current collector source and environment.

Record:
- Git revision and working-tree dirty status.
- Application source digest.
- Source archive SHA-256.
- Snapshot manifest and snapshot metadata.
- External runner, network guard and fixture-helper hashes.

The transfer snapshot establishes the identity of the newly declared current implementation. It does not establish equivalence with the unavailable historical source.

The historical arithmetic/factual recordings identify revision `17b695373f935dc1f5fd09c37cf8917969367f7a` and application digest `47597967da7d8f05aa56ef1ed6fbd544eb70e607aaf8804e5163e650cea35e4d`.

The inspected historical revision and source exports did not reproduce that digest. Strict historical reproduction therefore remains unavailable.

Do not check out a guessed historical revision, modify historical reports or describe a current-source snapshot as a historical recovery.

## 4. Environment reproducibility

Use one frozen current checkout and environment for both clean and altered conditions.

Record the environment and dependency versions in the source and setup evidence. Record actual installed model and resource fingerprints through the declared resource-observation process.

The paired preflights must agree on:
- Code revision.
- Application source digest.
- Environment.
- Dependency versions.
- Evidence kind.

The clean and altered resource manifests must be separately observed and validated. A declared fingerprint is evidence of consistency with the supplied observation; it is not independent proof that a model, corpus or index is truthful or operational.

Do not silently replace unavailable resources or change implementation, model or service versions between conditions.

## 5. Frozen policy reproducibility

The original prototype bundle is the fixed decision-rule reference for transfer evaluation.

Before evaluation:
- Validate the original bundle hashes and artifact IDs.
- Validate the original question scope and policy certificates.
- Preserve strategy definitions and every probability, including zero-probability strategies.
- Preserve reputation, thresholds, minimum requirements, units, loss settings and configured costs.
- Record the original artifact identity and SHA-256.

No optimizer, policy fitting, refitting, probability replacement, strategy rebinding, reputation update or threshold tuning is permitted during transfer evaluation.

The original certificate applies to the original fitted matrix. It must not be presented as a new certificate for altered resources.

## 6. Resource reproducibility

Prepare separate clean and altered resource configurations.

Record the actual observed resource manifests and their fingerprints, including applicable:
- Verifier implementation and configuration.
- Model identity.
- Evidence corpus.
- Evidence index.
- Confidence prompt and service configuration.

Run paired setup preflights before collection. Validate each EvidenceValidation proof against its own observed resource manifest.

The clean and altered conditions must differ only through the predeclared, authorized corpus/index/config-path intervention. Do not change verifier implementations, models or services between conditions.

A resource proof establishes the specified contract for the observed setup. It does not prove historical implementation equivalence or independently establish resource truth.

Both conditions must retain the complete original verifier roster.

## 7. Experiment controls and collection reproducibility

The transfer experiment must be authorized before any study collection begins.

The original prepared-development scope remains fixed:
- 20 development groups and 40 candidate answers per task.
- Reference-assisted evaluation.
- No expanded question or answer sets.
- No final-test payloads or labels.
- Independent labels remain separate from verifier inputs.

Declare the altered intervention before collection. Preserve the original questions, answers, references, labels and grouping. Do not select examples based on verifier success or change label truth.

For one altered scenario, collect one fresh clean condition and one fresh altered condition. Record the complete verifier roster in both.

Readiness probes must be run separately for both resource setups. Each proof covers four controlled cases and three installed-NLI cases, with zero study candidates and zero generations. Validate each proof against its corresponding observed resources before full collection.

## 8. Rehearsal, budgets and recovery

Conduct a bounded eight-call rehearsal separately for each condition, using the full unchanged request and a separate journal.

The planned stop before the ninth start must be recorded as status 130 with `planned_stop=true`. An ordinary failure is not a successful rehearsal.

Inspect the attempt and start journals:
- Every started attempt must have a retained completion.
- Preserve failures and abstentions.
- Do not accept duplicate attempts, resource drift or unresolved producer issues.
- Do not evaluate incomplete recordings or score a favorable subset.

Resume only unattempted IDs, using the existing journals, identical request, source and setup, and a new output directory.

Count actual rehearsal network usage against the approved total. Do not reset budgets, retry previously attempted failures, overwrite journals or change setup values.

An ambiguous in-flight start blocks resumption. All started attempts and their outcomes must remain auditable.

## 9. Assembly and evaluation reproducibility

Before evaluating, run `assemble-transfer` to validate and save the complete paired input.

Assembly requires complete recordings and valid evidence proofs. It is a validation and handoff step, not policy fitting or deployment-artifact export.

Keep the assembled input private because it contains development labels.

Run `evaluate-transfer` only after the paired input has been reviewed. The evaluation uses the original frozen policy and performs no model inference, fitting or recalibration.

Use the appropriate factual task, original artifact and historical inputs for the experimental factual policy. Preserve the original development scope and policy binding.

The output path must be new. Transfer evaluation must not write a new policy artifact.

## 10. Saved-output validation

Validate the saved transfer input and evaluation against their schemas.

Recompute the expected frozen transfer evaluation from the saved input and compare it with the saved output, excluding only the separately bound original artifact hash and prototype bundle ID.

Verify that the recorded artifact hash matches the original policy file.

This check validates saved-output consistency without performing model inference or fitting.

## 11. Reporting and interpretation

The transfer report should retain:
- Original policy and artifact identities.
- Strategy definitions and probabilities.
- Frozen reputation, thresholds, requirements, units and configured cost diagnostics.
- Historical and fresh collector setup identities.
- Intervention declaration identity.
- Separate clean and altered condition metrics.
- Errors, coverage, uncertainty, selective risk and validation loss.
- Failures, per-strategy outcomes and reasons.
- Ordered attempt IDs, execution flags, durations and timing status.

Report observed attempt durations separately from configured cost estimates.

Attempt timings are not request latency, monetary cost, recalibrated costs or evidence of efficiency improvement. Timing changes do not authorize changes to the frozen policy.

Retain source bundles and observations needed to interpret full reports and failure details. Keep development labels and assembled inputs private.

## 12. Current status and limitations

The transfer implementation and its software checks have been documented, but no new real paired preflights, approvals, altered resources, recordings or Evidence proofs have been supplied or executed.

A real transfer experiment is therefore **not ready**.

The historical software verification recorded in `docs/upstream_transfer_evaluation.md` includes:
- 244 tests passing in the working tree and 244 in an isolated clean source export.
- After the pre-collection scope guard, all 23 transfer tests passing in both locations.
- Four selected production Evidence-verifier tests (support, contradiction, neutrality and conflict) passing with fake retrievers/NLI only.
- Successful reload of the original prototype package without inference.
- A historical source audit rejecting the current checkout because of revision and application-digest mismatch, without initializing a factory.

These are previously recorded software checks, not tests rerun during the current Person 3 documentation review. They establish implementation behaviour, not empirical poisoning resistance or installed-model readiness.

Historical/current source equivalence remains unestablished. The transfer workflow does not supply a historical source-equivalence proof, automatic poisoning detector, verifier repair, deployed protection or immunity claim.

## 13. External dependencies and next steps

Before a real run:
1. The study owner must approve the transfer interpretation, implementation, controls, report compatibility, budgets and rehearsal.
2. The dataset owner must supply the original artifacts and recordings, unchanged independent development labels, references and metadata-only reservation.
3. The resource owner must supply compatible installed models, clean and altered corpus/index receipts, and actual resource observations.
4. The collection owner must snapshot and freeze the current source/environment, execute authorized paired calls, and audit proofs and checkpoints.
5. The evaluator must validate the contracts and score the unchanged frozen decision rule.

Until these prerequisites are met, reproducibility documentation and software validation must not be represented as a completed empirical experiment.



