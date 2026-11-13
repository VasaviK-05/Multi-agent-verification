"""Explicit authorized prospective fit/freeze or replay. Never dispatch verifiers.

The metadata-only readiness CLI remains separate. Fit requires scoped approvals;
Final replay invokes a payload loader only after the exact-manifest release gate.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from app.game.models import content_id
from app.game.research.experiment1.manifest import AtomicEntry, atomic_bindings, source_fingerprint
from .models import Manifest, Cohort, Authorizations, load_authenticated
from .reporting import _gate, report_development, report_final


def fit_cohort(manifest, cohort, *, actual_commit, actual_source_fingerprint, authorizations, freeze_record):
    """Fit NEW full and matched baselines from approved H/D only; no file access."""
    manifest=Manifest.model_validate(manifest)
    auth=Authorizations.model_validate(authorizations)
    _gate(manifest,cohort,'policy_fitting',actual_commit,actual_source_fingerprint,auth)
    c=manifest.cohort(cohort)
    if c.frozen is not None:
        raise ValueError('already frozen; refusing refit')
    if not freeze_record.strip() or freeze_record.strip().upper().startswith(('PENDING','TODO','UNKNOWN')):
        raise ValueError('reviewed freeze record required')
    # All imports/optimization are after the approval gate.
    from app.game.offline.evaluation import construct_payoffs, export_artifact
    from app.game.offline.coverage import prepare_clean_coverage
    from app.game.offline.reliability import prepare_reliability_first
    from app.game.research.comparison import prepare_comparison, validate_frozen
    s=c.specification
    development=construct_payoffs(s.context,s.manifest,s.contract,s.attacks)
    kwargs=dict(minimum=c.choices.development_coverage_floor)
    if c.choices.objective=='validation_then_attempt_cost_v1':
        bound,matrix=prepare_reliability_first(s.context,s.manifest,s.contract,s.attacks,development,
            **kwargs,epsilon=c.choices.validation_epsilon,cost_tolerance=c.choices.cost_tolerance)
    else:
        bound,matrix=prepare_clean_coverage(s.context,s.manifest,s.contract,s.attacks,development,**kwargs)
    from app.game.solver import solve_minimax, validate_solution
    from app.game.policy import Policy, semantics_version
    solution=solve_minimax(matrix,tolerance=c.choices.optimizer_tolerance)
    if solution.status!='optimal':
        # Preserve genuine infeasibility/negative findings; do not make a frozen policy.
        return dict(status=solution.status,cohort=cohort,manifest_id=manifest.manifest_id,
                    matrix=matrix.model_dump(mode='json'),certificate=solution.model_dump(mode='json'))
    validate_solution(matrix,solution)
    policy=Policy(version=semantics_version(bound,matrix),compatibility_id=bound.compatibility_id,
        provenance=bound.provenance,matrix=matrix,solution=solution,strategies=matrix.strategy_definitions)
    artifact=export_artifact(policy,bound,s.manifest,s.contract,s.attacks,applicable_domain=s.context.plan.domain)
    prepared=type(s).model_validate({**s.model_dump(),'context':bound})
    comparison=prepare_comparison(prepared,development,artifact,freeze_record=freeze_record,actual_code_revision=actual_commit)
    validate_frozen(prepared,comparison,actual_code_revision=actual_commit)
    entry=AtomicEntry(cohort=cohort,specification=prepared,comparison=comparison,bindings=atomic_bindings(prepared,comparison))
    updated=Cohort.model_validate({**c.model_dump(),'frozen':entry})
    result=Manifest.model_validate({**manifest.model_dump(),'cohorts':tuple(updated if x.name==cohort else x for x in manifest.cohorts)})
    if result.fitting_id(cohort)!=manifest.fitting_id(cohort):
        raise ValueError('fit changed approved fitting identity')
    return dict(status='frozen',manifest=result.model_dump(mode='json'),manifest_id=result.manifest_id,
                policy_id=policy.policy_id,comparison_id=comparison.comparison_id)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('fit','development','final'))
    p.add_argument('manifest',type=Path)
    p.add_argument('--sha256',required=True)
    p.add_argument('--authorizations',type=Path,required=True)
    p.add_argument('--authorization-sha256',required=True)
    p.add_argument('--cohort',choices=('arithmetic','factual'),required=True)
    p.add_argument('--output',type=Path,required=True,help='Fresh private JSON path; never overwrite')
    p.add_argument('--freeze-record')
    p.add_argument('--payload',type=Path,help='Final bytes; opened lazily only after release gate')
    args=p.parse_args(argv)
    if args.output.exists() or args.output.with_suffix(args.output.suffix+'.receipt.json').exists():
        raise FileExistsError('refusing overwrite')
    if args.command=='fit' and not args.freeze_record:
        p.error('fit requires --freeze-record')
    if (args.payload is not None)!=(args.command=='final'):
        p.error('--payload required only for final')
    m=load_authenticated(args.manifest,args.sha256)
    auth=load_authenticated(args.authorizations,args.authorization_sha256,Authorizations)
    root=Path(__file__).resolve().parents[5]
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    fingerprint=source_fingerprint(root)
    kwargs=dict(actual_commit=commit,actual_source_fingerprint=fingerprint,authorizations=auth)
    if args.command=='fit':
        result=fit_cohort(m,args.cohort,**kwargs,freeze_record=args.freeze_record)
    elif args.command=='development':
        result=report_development(m,args.cohort,**kwargs)
    else:
        result=report_final(m,args.cohort,**kwargs,payload_loader=lambda:args.payload.read_bytes())
    receipt=dict(command=['python','-m','app.game.research.experiment1.prospective.execute',
        *(argv if argv is not None else sys.argv[1:])],source_commit=commit,source_fingerprint=fingerprint,
        input_manifest_id=m.manifest_id,authorization_sha256=args.authorization_sha256,
        result_id_before_receipt=content_id(result))
    result['execution_receipt']=receipt
    # The reviewed local custody path is caller-selected; no public Git staging.
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    with args.output.with_suffix(args.output.suffix+'.receipt.json').open('x') as f:
        json.dump(receipt,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
    return 0 if result.get('status','frozen')=='frozen' else 2


if __name__=='__main__':
    raise SystemExit(main())
