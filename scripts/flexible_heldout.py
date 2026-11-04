"""Freeze held-out candidates and predeclare evaluation; no fitting or inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
from app.game.models import PlanningContext, content_id
from app.game.policy import Policy, validate_policy
from app.game.execution_contract import ExecutionContract
from app.game.offline.records import TrainingManifest
from app.game.offline.attacks import enumerate_attacks


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d): Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def prepare(source, candidates, output):
    output.mkdir(parents=True,exist_ok=False)
    records=[];preserved={str(p.resolve()):sha(p) for p in candidates.rglob('*') if p.is_file()}
    for cohort in ('arithmetic','factual'):
        src=candidates/(cohort+'-minimum-1');dest=output/cohort;dest.mkdir()
        context=PlanningContext.model_validate(read(src/'context.json'))
        contract=ExecutionContract.model_validate(read(src/'contract.json'))
        policy=validate_policy(Policy.model_validate(read(src/'policy.json')),context)
        assert ExecutionContract.model_validate_json(context.execution_contract_json)==contract
        training=TrainingManifest.model_validate(read(source/cohort/'training-manifest.json'))
        reservation=training.final_test_reservation
        assert reservation.model_dump(mode='json')==read(source/cohort/'reservation.json')
        # TrainingManifest validates all reservation overlap keys against both splits.
        diagnostics=read(src/'strategy-diagnostics.json')
        clean=lambda row: next(cell['metrics'] for key,cell in row['attacks'].items() if key.startswith('clean:'))
        eligible=[row for row in diagnostics if clean(row)['decision_coverage']>=.90]
        worst=lambda row:max(cell['decision_loss'] for cell in row['attacks'].values())
        best_loss=min(map(worst,eligible))
        best=min((row for row in eligible if worst(row)<=best_loss+1e-8),key=lambda row:(row['strategy']['estimated_cost'],row['strategy']['strategy_id']))['strategy']
        greedy=tuple(sorted(context.plan.initial_selected))
        greedy_strategy=next(s for s in policy.strategies if s.verifiers==greedy and s.aggregation=='reputation_weighted')
        for name in ('policy.json','context.json','contract.json'):
            shutil.copyfile(src/name,dest/name)
        specification=read(source/cohort/'policy-input.json')
        save(dest/'attacks.json',specification['attacks']);save(dest/'reservation.json',reservation.model_dump(mode='json'))
        save(dest/'baselines.json',dict(development_best=best,greedy=greedy_strategy.model_dump(mode='json'),fixed_equals_flexible=all(s.verifiers==tuple(best['verifiers']) and s.aggregation==best['aggregation'] for s in policy.strategies if dict(policy.solution.probabilities)[s.strategy_id]>0),fixed_selection_rule='Eligible fixed strategies meet 0.90 development clean coverage; minimize worst development decision loss; within 1e-8 minimize estimated cost then strategy_id.',greedy_scope='Existing coverage-aware selector initial_selected, reputation_weighted; complete selected team under matching minimum-one finalization. This isolates selection; it is not the separate adaptive non-game stopping pipeline.'))
        records.append(dict(cohort=cohort,policy_id=policy.policy_id,context_id=context.compatibility_id,reputation_id=context.reputation_snapshot_id,resource_id=contract.execution_configuration_id,threshold=contract.threshold,minimum_selected=context.minimum_participant_count,minimum_informative=context.minimum_informative_count,budget=context.budget,cost_units=context.cost_units,loss=context.loss_configuration.model_dump(mode='json'),team_size_probabilities=read(src/'summary.json')['selection_probability_by_team_size'],probabilities=policy.solution.probabilities,reservation_id=reservation.reservation_id,reserved_examples=reservation.model_dump(mode='json')['examples'],examples=len(reservation.examples),groups=len({e.split_identity for e in reservation.examples}),attempts=len(reservation.examples)*len(context.plan.candidates),roster=[c.verifier_name for c in context.plan.candidates],history_development_overlap='TrainingManifest validated all example/group/question/content/run identity exclusions',training_manifest_id=training.manifest_id,training_sha256=sha(source/cohort/'training-manifest.json')))
    versions={'python':platform.python_version()}
    for package in ('pydantic','numpy','scipy','torch','transformers','sentence-transformers','faiss-cpu','requests','safetensors','tokenizers'):
        try:versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:versions[package]='not installed'
    frozen_files={str(p.relative_to(output)):sha(p) for p in output.rglob('*.json')}
    source_hashes={str(p):sha(p) for p in Path('app').rglob('*.py')}
    freeze=dict(version='flexible_heldout_freeze_v1',created_utc=datetime.now(timezone.utc).isoformat(),base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),worktree=str(Path.cwd()),software_versions=versions,candidates=records,frozen_file_hashes=frozen_files,source_hashes=source_hashes,prior_artifact_hashes=preserved,authorization='User follow-up: bounded local inference for reserved arithmetic/factual partitions only',test_outcomes_inspected=False,test_payloads_opened=False)
    freeze['freeze_id']=content_id(freeze);save(output/'freeze-manifest.json',freeze)
    save(output/'evaluation-specification.json',dict(version='paired_heldout_evaluation_v1',freeze_id=freeze['freeze_id'],cohorts=records,primary_methods=['frozen_flexible','development_best_fixed','coverage_aware_greedy_complete_team'],minimum_two='Separate fixed-team contract ablation only; all minimum-two fits infeasible, no minimum-two policy or invented probabilities.',metrics=dict(accept_reject_uncertain='counts / all 40 examples per cohort',coverage='decided / all examples',false_accept='incorrect accepted / all 40, plus incorrect accepted / 20 incorrect examples',false_reject='correct rejected / all 40, plus correct rejected / 20 correct examples',decision_loss='(FA + FR + 0.2 * uncertain) / all examples; no resource penalty',selective_risk='(FA + FR) / decided; null if no decided examples',execution_failures='failed/unavailable selected attempts, and cases affected, with missing recordings distinguished',cost='measured individual attempt durations excluding initialization; historical selected-team estimates; full-roster collection is not singleton end-to-end latency'),uncertainty=dict(method='Paired cluster percentile bootstrap, resample 20 split_identity groups with replacement, retaining both correct/incorrect answers and paired methods',replicates=10000,seed=20261102,interval=.95,zero_decision_samples='risk undefined; disclose undefined fraction and omit risk CI if any bootstrap sample undefined'),schedule='Arithmetic then factual; reservation example_id order; original roster registration order; one attempt per verifier/example; sequential CPU; no warmups beyond factory; at most 320 attempts and 400 local generation requests (5 per confidence attempt). No semantic cohort.',failure_handling='Existing returned failure/abstention states retained. Confidence sampler timeout 60 seconds per sample, up to five samples; no new retry layer. Durable started/completed journals; never retry an ambiguous in-flight attempt. Missing recordings block evaluation. Observer/resource drift blocks empirical replay.',label_separation='Custody labels retained only in evaluation metadata; dispatch accepts question, answer, permitted reference only. No labels in routing, selection or reputation. No refitting or reputation update.',resource_gate='Require exact frozen resource manifest, matching corpus/index/receipt and live local model digest/version before factory/collection. No downloads, index rebuild or corpus edits.',attacks='Frozen report_corruption_v1 attacks evaluated separately; one connected shared-failure group may corrupt all selected verifiers. Not a real upstream compromise.',coverage='90% is development feasibility only; no promised test coverage.',limitations='Source-known procedural reservations; paired narrow arithmetic and pinned factual cohorts, not blinded unseen-source generalization or broad domain/difficulty adaptation.'))
    print('Freeze',freeze['freeze_id'],'80 examples / 320 attempts; policies validated; test outcomes unopened',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--candidates',type=Path,default=Path('artifacts/flexible-teams-v1'));p.add_argument('--output',type=Path,default=Path('artifacts/flexible-heldout-v1'));a=p.parse_args();prepare(a.source,a.candidates,a.output)
