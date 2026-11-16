# Rehearsal contamination-flag audit

Date: 2026-11-16. Read-only. No rehearsal was rerun, and no manifest or report was regenerated or repaired. No rehearsal attempt was added to a research dataset. Final Test outcome files were not used as evidence.

Conclusion: **unrecoverable within available sources**. The reported false-to-true change of four contamination-related flags is not explained by a recovered original manifest and derived report. This is a limit of the sources that could be inspected, not a claim that the pair is gone from every machine.

## Reported discrepancy

The original pilot manifest is said to record four contamination-related flags as `false`. A derived validation report is said to record all four as `true`. The derived report is said to concern 32 rehearsal attempts, which must stay out of the research population.

## Artifacts located

The named rehearsal archive is not in this checkout.

| Record | Value |
|---|---|
| Archive name | `research_v1_development_rehearsal_662bd5c.zip` |
| Recorded SHA-256 | `f688faff1cf4a25abe30d7e6516a0eab58bd0015a78d6863054c0435491d10f0` |
| Recorded size | 18,333 bytes |
| Recorded external path | `/Users/vasavi/Downloads/research_v1_development_rehearsal_662bd5c.zip` |
| Phase C payload status | `payload_members_opened: false` |

Phase C listed these members and did not open them:

| Member | Recorded bytes |
|---|---:|
| `research_v1_rehearsal_662bd5c/artifact_sha256.json` | 380 |
| `research_v1_rehearsal_662bd5c/attempts.jsonl` | 184,910 |
| `research_v1_rehearsal_662bd5c/pilot_manifest.json` | 8,188 |
| `research_v1_rehearsal_662bd5c/pilot_results.json` | 9,926 |
| `research_v1_rehearsal_662bd5c/unresolved_not_attempted.jsonl` | 1,951 |

Those two JSON files are the original pilot manifest and the derived pilot results named by the archive. Their flag values were not read here because the archive is absent. `attempts.jsonl` was not opened, so the count of 32 attempts was not recomputed.

Local pilot files that do exist are a different run. Both sides keep `final_test_accessed` false, and both record zero verifier calls:

| Path | Role |
|---|---|
| `evaluation/datasets/development_pilot/research_v1_feasibility_v1/pilot_manifest.json` | Blocked preflight manifest |
| `evaluation/datasets/development_pilot/research_v1_feasibility_v1/pilot_results.json` | Blocked preflight report |
| `evaluation/datasets/development_pilot/research_v1_feasibility_v2/pilot_manifest.json` | Blocked preflight manifest |
| `evaluation/datasets/development_pilot/research_v1_feasibility_v2/pilot_results.json` | Blocked preflight report |

The v1 and v2 manifests also set `history_inputs_read` and `policy_fitting_ready` to false. They do not contain `labels_or_gold_sent_to_verifiers` or `policy_fitting_performed`. They are not a 32-attempt rehearsal.

## Four flags in the recovered producer

Commit `662bd5cdbf2c8b2dc9885f6bb80e42abf7c5205e` (2026-11-08, “Fix benchmark package eager import for adapter isolation”) contains `evaluation/data_preparation/run_development_feasibility_pilot.py`. Its completed-run manifest assigns these four booleans, all `false`:

| Flag | Meaning in that assignment | Manifest value in source | Derived `analyze_attempts` report |
|---|---|---|---|
| `final_test_accessed` | The runner did not open Final Test | `false` | copied as `false` |
| `history_inputs_read` | The runner did not read History inputs | `false` | not copied |
| `labels_or_gold_sent_to_verifiers` | Labels or gold answers were not sent to verifiers | `false` | not copied |
| `policy_fitting_performed` | No policy fit was performed | `false` | not copied |

`false` means the named event did not happen. The same commit’s `validate_output` rejects a manifest unless `final_test_accessed` and `history_inputs_read` are `false`. A search of the repository source found no assignment of any of these four names to `true`.

That producer therefore does not explain a derived report in which all four flags are `true`. No schema, field migration, or validation rule that rewrites them from `false` to `true` was recovered.

## Search coverage

Inspected:

- This clone, including Git-ignored Development feasibility pilots and adjudication pilots.
- `git grep` at `662bd5c` and the working tree for the four flag names.
- `git log -S contamination` on the two pilot scripts: no matching commits.
- Reachable commits that name the rehearsal archive: Phase C notes, the recording-handoff evidence index, and the Experiment 3 run manifest. None stores the archive payload.
- Stash list: two WIP stashes on other branches. Their trees were not applied.
- Filename search for the archive in this repository, Downloads, Desktop, Documents, and OneDrive to depth 5. The archive was not found.
- Experiment 3 `run_manifest.json`: `historical_rehearsal.used_as_experiment3_dataset` is `false` and `present_in_checkout` is `false`.

Not inspected:

- The machine that held `/Users/vasavi/Downloads/research_v1_development_rehearsal_662bd5c.zip`.
- Remote CI artifacts. No local `.github` workflow store and no `gh` client were used for that query.
- A full content hash of OneDrive.

## Exclusion of the 32 attempts

No list of 32 rehearsal attempt identities was recovered, because `attempts.jsonl` inside the missing archive was not opened. This investigation did not copy, replay, or insert those attempts into a research dataset. The Experiment 3 manifest already records that this archive is not the Experiment 3 Development collection. An explicit identity-level exclusion list for all 32 attempts remains unverified until the archive is available.

## Classification

**Unrecoverable within available sources.** The flag discrepancy cannot be confirmed or explained from the original pair. The recovered producer only writes the four boundary flags as `false` and does not transform them to `true`.
