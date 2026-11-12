# Experiment 1 Phase B — input assembly and readiness only

No final-test payload was opened, replayed, scored or released. No verifier call,
optimizer, policy fit, database operation, production API, push or merge ran.
Available canonical metadata/training inputs were validated without reconstructing
missing custody files from redacted views.

## Preserved implementation commits

- Phase 1: `6480ba7bf4a3ef66501e22268030e24a2f02cb46` — compatible frozen coverage-constrained comparisons.
- Phase A: `9f8b64aa18cbd25292699888b2ee1f5ff0ca554e` — retrospective manifest, metrics, paired statistics and component reporting.

Only the intended 14 implementation/test/documentation files were committed in
those two logical commits. The Phase 1 test prefix was committed separately and
then the original complete Phase A test bytes were restored before its commit.
No prior user changes were discarded. Phase B candidates and this evidence remain
uncommitted for review, pinned to the Phase A source commit. Committing later
metadata changes HEAD; a readiness run must use the exact declared source checkout
or a newly reviewed retrospective candidate. Never rewrite historical freeze IDs.

## Outputs and validation boundary

- `input-inventory.json`: exact paths, actual SHA-256/byte sizes, publication hash
  comparisons, policy/context/matrix/resource IDs, source bindings, partitions,
  group identities, missing custody paths and recorded expected original hashes.
- `historical-comparisons.json`: original method definitions/statistical protocols,
  separate from expanded retrospective methods; no claim of new preregistration.
- `experiment1-candidate.json`: combined real-input candidate with explicit blockers.
- `arithmetic-candidate.json`, `factual-candidate.json`, `reference-candidate.json`,
  `compound-candidate.json`, `original_semantic-candidate.json`: focused candidate
  IDs carrying the same complete five-cohort disposition roster. The current
  schema requires all dispositions; these are not assertions of independent
  per-cohort readiness or pooled results.
- `readiness-results.json`: exact readiness commands, return codes, manifest IDs
  and machine-readable blockers for all six candidates.
- `assemble_inputs.py`, `check_readiness.py`: reproducible metadata-only utilities.

The assembly reads 39 explicitly permitted metadata/training files. All input
bytes covered by the existing publication inventory match it. Publication registry
and file-hash index metadata are not signed custodial originals. One redacted
flexible-heldout freeze is read **only as a locator** for unavailable training
hashes/IDs. It does not satisfy any freeze/custody gate. The publication registry
explicitly forbids substituting derived views for canonical whole-freeze bytes.

Tests forbid replay, optimizer entry points, baseline preparation and opening
`/test/` data, final partitions, final report/outcome files or reserved requests.
The read ledger is retained in the inventory. Final resource `observed-setup.json`
files are metadata only; they are not verifier reports, answers or truth labels.

## Verified real-cohort evidence

| Cohort | Validated available inputs | Readiness |
|---|---|---|
| Arithmetic | Typed current minimum-one policy/certificate/context/contract; original fixed/greedy row definitions; outcome-free reservation; archived final resource metadata equals frozen contract | Blocked: canonical training/development and internal freeze/seals absent; research specification and expanded comparison freeze not assembled |
| Factual | Same checks using its genuine Evidence policy and direct-fact requirement | Same blockers; evidence-validation metadata/specification also required |
| Reference | Published authentic training manifest/bundle and development evaluation; 20 history, 20 development, 20 reserved examples, ten paired groups per role; frozen mixed policy; matching history/resource binding; reserved-seal metadata | Blocked: canonical `seal.json` / `fit/freeze.json` absent, reviewed research specification and expanded comparison freeze missing |
| Compound | Typed joint policy/certificate; both recorded training partitions, 48 examples and 12 entity groups per component/role; complete bundles and recorded resources; exact scoped E/R projection and all four transfer source hashes | Blocked: canonical study/preparation seal/candidate freeze missing; no expanded component comparison freeze |
| Original Semantic | Existing 0.90 constrained game/result; maximum stored development coverage 0.575 and empty probabilities | Infeasible, excluded. Its disposition validates; it has no scoring policy and is not replaced by Reference |

All six whole-experiment readiness commands exited **2**, with four fitted-cohort
blockers. Source commit, source-byte fingerprint and reporting environment match;
there is no incidental source/environment mismatch hiding the scientific blockers.
An infeasible Semantic disposition may show `ready:true` in the cohort metadata
row: that means the exclusion record validates, **not** that a policy can be scored.

### Policy and provenance identities

| Cohort | Frozen policy ID |
|---|---|
| Arithmetic | `c6a1f9c14bf2337aa3202124a2ed087616d48a46d70f56e7f37aba0a2a446e14` |
| Factual | `0df33426333e0f7bbe6418fdf7900719dbda5182f68d50405b593b3341ec9d0d` |
| Compound | `0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532` |
| Reference | `c05a50fb5fc3651c8dc5d1bd55ec02086c3f4c26e49e7145393cb007e7149cda` |

Arithmetic/Factual canonical artifact triplets are under
`artifacts/flexible-heldout-v1/{arithmetic,factual}/{policy,context,contract}.json`.
Their full resource ID is
`e23c6f034a4c660d30433d133be3a197db620abbdf22a78907ef5e3687d45ccb`.
Their internal evaluation specification names freeze
`bcba68b5bd2857246fb3c4d9248f0eb2af4fd891b5b694335799826942ae519e`.
Final reservation IDs and every reserved example/group key are in the inventory;
full history/development group lists cannot be verified without the missing manifests.
Training IDs/digests obtained from the public locator remain explicitly noncanonical
locator evidence until the custodian supplies original bytes.

Reference policy is `artifacts/remaining-category-studies-v1/reference-50-v1/fit/policy.json`;
training and development files are adjacent, with the raw training bundle under
`training/reference/bundle.json`. Its resource ID is
`7dc5ab6098f803133284f413ad577970073c99f12fb020c6b4a2dc75b9642ffb`.
Its reserved seal names freeze
`94e3a7dcbe2b6ccb3d0155018f04419a9513abce8f3752aaeb32f1c38d2d4596`
and canonical freeze SHA-256
`8d9f2259a4f5b119a0a26b95770fa77c2ab4e4d922ec8892864a53e3ffc279e2`.
The reservation is outcome-free. The sealed reserved request is present but was
not opened or hashed. Its hash is copied only from the original reserved-seal
metadata, with `hash_verified:false`. This is historical authorization evidence,
not authorization to score now. Genuine probabilities remain exactly
0.16666666666666663 Semantic and 0.8333333333333334 Confidence+Semantic; floor 0.50
was explicitly chosen after development.

Compound policy is `artifacts/remaining-category-studies-v1/compound-85/candidate/policy.json`.
Canonical available history/development bundles are
`artifacts/compound-study-36-v1/{history,development}/joint.json`.
Joint reservation identity is retained from the original joint development binding;
final group/source assignment requires the missing canonical study. The unchanged
base-fact Evidence / derived-sum Rule obligations retain the submitted-answer
binding and joint decision rules, threshold 0.55 and floor 0.85.
Its E/R resource scope is
`310364dae8d9d6c001622d4bbe1866ca0646fb8f50c9c50a022e05f5353688c1`.
Transfer `artifacts/remaining-category-studies-v1/scoped-er-v1/transfer.json` names
`b6eef0e3b178bafb87368a2884a8209f45e7368448bf05ec82c215f01626d343`
and original freeze
`d327793b940b356a0e8cd418c9a6a7ae3d93c3f6a21035a0f36b0e29910ad0c0`.
The proof's required resource entries and source hashes validate; no new proof was
made. No Compound greedy executor is invented.

Recorded collection source commits are taken from existing setup metadata
(`2c9f697439d1d1c2ed7c0a92645848c0f07f7e3f`), independently of the later
flexible-heldout freeze's recorded base commit. The additional recorded application
source digest is retained: a commit alone is not the entire original working
source snapshot. The unpublished custody archive remains absent. Current native
models/services were neither probed nor assumed compatible with old full manifests.

### Historical versus expanded comparisons

Arithmetic/Factual's original three methods are frozen flexible, development-best
coverage-eligible fixed, and captured complete-team greedy. Canonical baseline
row definitions match feasible frozen rows and the stored development ranking.
Their original statistical protocol is **10,000 paired group resamples, seed
20261102**, not the newly retrospective settings.

Reference's original exploratory comparison has full mixture, development-selected
fixed, and captured greedy, with **1,000 resamples, seed 1103**. The fixed-selection
rule is documented, but its authoritative frozen selected ID cannot be recovered
from a redacted freeze or from final-test results. The captured greedy row is
structurally available in the genuine policy context. Whole-freeze validation is blocked.

Compound's original exploratory comparison has the joint policy and declared
fixed joint plan, with **1,000 resamples, seed 1102**. The original 90% infeasibility
and authorized post-development 85% amendment remain separate. Neither this nor
Reference's amended floor is relabelled an unchanged original setting.

Expanded uniform and aggregation-restricted games remain **retrospective**.
No complete real-cohort `FrozenComparison` / `FrozenComponentComparison` carrying
all expanded method definitions and certificates was found. No uniform
probabilities or restricted LP certificates were manufactured here. If no such
freeze exists with the custodian, development-only preparation requires separate
approval; it must not refit the existing full policy or be backdated/preregistered.
New retrospective reporting remains 95%, 5,000 repetitions, seed 20261112.

## Exact missing canonical prerequisites

The machine inventory provides registered original SHA-256 values where available;
unknown original hashes remain null. None were fabricated. All these canonical
paths are absent locally, and local Git history has no commits for them:

- `build/multitask-policy42/arithmetic/training-manifest.json`
- `build/multitask-policy42/arithmetic/development-evaluation.json`
- `build/multitask-policy42/factual/training-manifest.json`
- `build/multitask-policy42/factual/development-evaluation.json`
- `artifacts/flexible-heldout-v1/freeze-manifest.json`
- `artifacts/flexible-heldout-v1/precollection-seal.json`
- `artifacts/flexible-teams-v1/input-hashes.json`
- `artifacts/compound-study-36-v1/preparation/study.json`
- `artifacts/compound-study-36-v1/preparation-seal.json`
- `artifacts/remaining-category-studies-v1/compound-85/candidate/freeze.json`
- `artifacts/remaining-category-studies-v1/reference-50-v1/seal.json`
- `artifacts/remaining-category-studies-v1/reference-50-v1/fit/freeze.json`

Original application-source custody archive
`artifacts/compound-study-36-v1/local-custody/original-execution-source.zip` is
also absent (its recorded SHA-256 is in the inventory). The publication's original
content commit is not an available local Git object. Search scope was this local
repository, ignored build paths, local Git refs and project directory; no network
fetch was performed. Missing locally does not mean missing from the custodian.

Whole-freeze/custody originals must be obtained by exact registered relative path
and SHA-256 through the publication's documented acquisition process. Public views
cannot be promoted into originals. Old prototype ZIP/current-rerun policies are
not substitutes for the genuine current flexible artifacts. No sealed final
outcome file is needed to resolve any of these prerequisites, so none was opened.

## Readiness reproduction — safe to run now

From the repository root in the configured local environment:

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B docs/experiment1/phase-b/assemble_inputs.py
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B docs/experiment1/phase-b/check_readiness.py
```

The wrapper itself exits 0 when all readiness processes return structured reports;
that is **not** a ready experiment. Each candidate's actual CLI exit/result is
retained in `readiness-results.json`. To run an individual readiness check:

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m app.game.research.experiment1 readiness docs/experiment1/phase-b/arithmetic-candidate.json
```

Replace the filename with `factual-candidate.json`, `reference-candidate.json`,
`compound-candidate.json`, `original_semantic-candidate.json` or
`experiment1-candidate.json`. All currently return 2. Do not use the old Phase A
illustrative template as a newly assembled canonical input freeze.

## Eventual approved scoring — NOT EXECUTED and currently blocked

There is deliberately no CLI `score` subcommand. After canonical restoration,
reviewed development-only comparison preparation, successful readiness and explicit
approval of the exact new manifest ID, use the existing explicit Python API.
The following is the exact planned invocation, **not a currently runnable approved
experiment**. `build/experiment1-approved/manifest.json` does not exist yet and the
approved ID must come from that future approval; neither is manufactured here.

```sh
EXPERIMENT1_APPROVED_MANIFEST_ID='<actual separately approved manifest ID>' \
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps \
python3 -B - <<'PY'
import json, os, subprocess
from pathlib import Path
from app.game.research.experiment1.manifest import ExperimentManifest, readiness, source_fingerprint
from app.game.research.experiment1.runner import report_cohort
root = Path.cwd()
manifest = ExperimentManifest.model_validate_json(
    Path('build/experiment1-approved/manifest.json').read_text())
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
fingerprint = source_fingerprint(root)
status = readiness(manifest, actual_commit=commit,
    actual_source_fingerprint=fingerprint, source_root=root)
if not status['ready']:
    raise SystemExit(json.dumps(status))
if os.environ.get('EXPERIMENT1_APPROVED_MANIFEST_ID') != manifest.manifest_id:
    raise SystemExit('Exact manifest has no supplied approval identity')
# Final payloads are read ONLY below this point, after separate approval.
releases = {
    'arithmetic': 'artifacts/flexible-heldout-v1/arithmetic/final-partition.json',
    'factual': 'artifacts/flexible-heldout-v1/factual/final-partition.json',
    'reference': 'artifacts/remaining-category-studies-v1/reference-50-v1/evaluation/final-partition.json',
    'compound': 'artifacts/remaining-category-studies-v1/scoped-er-v1/test/joint.json',
}
output = Path('build/experiment1-approved/new-results')
output.mkdir(parents=True, exist_ok=False)
for cohort, filename in releases.items():
    released = json.loads(Path(filename).read_text())
    result = report_cohort(manifest, cohort, actual_commit=commit,
        actual_source_fingerprint=fingerprint, source_root=root,
        role='final_test', released_final=released)
    with (output / (cohort + '.json')).open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
PY
```

This reports expanded retrospective results only. Reproducing historical results
under their original statistics additionally requires their original execution
seals/source and must stay labelled separately. The future output folder is fresh;
no original final result is overwritten and no database is involved.

## Tests and remaining state

Seven readiness/assembly tests passed, with 15 unrelated tests deselected. They
use actual allowed metadata/training records only, forbid optimizer/replay/final
access, and reject non-allowlisted sealed/redacted inputs. No synthetic or empirical
fitting test was run in Phase B. The previous Phase A broad synthetic results are
not presented as a newly rerun fitting suite.

```sh
PYTHONPATH=/private/tmp/experiment1-test-guard:/private/tmp/experiment1-test-deps python3 -B -m pytest tests/test_experiment1_phase_b_inputs.py tests/test_experiment1_reporting.py -k 'phase_b or schema_and_readiness_cli or reporting_environment' -q -p no:cacheprovider -p no_external_connections
```

Phase B outputs and `tests/test_experiment1_phase_b_inputs.py` remain uncommitted
for review. Scientific source, original artifacts, policies/probabilities, settings,
resource fingerprints, reputation, production code and dependency files were not
modified. The final state is **assembly complete to the limits of available
canonical inputs; actual scoring blocked**. Stop here pending canonical custody
restoration and separate approval, not permission to bypass missing records.
