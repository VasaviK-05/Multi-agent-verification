"""Publication/export and execution gates on synthetic records only."""
import hashlib
import json

import pytest

from tests.test_experiment1_prospective import prepared, auth_for, FP
from app.game.research.experiment1.prospective.reporting import report_development
from app.game.research.experiment1.prospective.export import export_reports, load_report, main
from app.game.research.experiment1.prospective.execute import fit_cohort
from app.game.research.experiment1.prospective.models import Manifest, Authorizations, fitting_specification


@pytest.fixture(scope='module')
def report(prepared):
    m,_=prepared
    return report_development(m,'arithmetic',actual_commit=m.source_commit,
        actual_source_fingerprint=FP,authorizations=auth_for(m))


def test_complete_bundle(report,tmp_path):
    root=export_reports([report],tmp_path/'SYNTHETIC',command=['synthetic test'],allow_synthetic=True)
    for name in ('clean_vs_attacked','risk_coverage','cost_loss','strategy_distribution'):
        assert (root/'figures'/f'{name}.png').read_bytes().startswith(b'\x89PNG')
        assert (root/'figures'/f'{name}.pdf').read_bytes().startswith(b'%PDF')
        assert (root/'figures'/f'{name}.csv').stat().st_size>50
    for name in ('clean_vs_attacked','baseline_comparison','coverage_and_risk','cost_analysis','paired_confidence_intervals'):
        assert (root/'metrics'/f'{name}.csv').stat().st_size>50
    receipt=json.loads((root/'reports/reproducibility.json').read_text())
    assert receipt['absent_cohorts']==['factual']
    for path,digest in receipt['files_sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest
    assert 'SYNTHETIC TEST' in (root/'tables/experiment1_main.tex').read_text()
    assert 'not actual evidence poisoning' in report['provenance']['attack_scope']
    assert 'source_fingerprint' in report['provenance']
    assert 'frozen_entry' not in report['provenance'] # never copy raw training records
    with pytest.raises(FileExistsError):
        export_reports([report],root,command=[],allow_synthetic=True)


def test_reject_unreviewed_or_mixed_export(report,tmp_path):
    with pytest.raises(ValueError,match='synthetic'):
        export_reports([report],tmp_path/'out',command=[])
    with pytest.raises(ValueError,match='duplicate'):
        export_reports([report,report],tmp_path/'out',command=[],allow_synthetic=True)
    with pytest.raises(ValueError,match='prospective'):
        export_reports([{**report,'version':'historical'}],tmp_path/'out',command=[])
    with pytest.raises(ValueError,match='mixed'):
        export_reports([report,{**report,'cohort':'factual','role':'final_test'}],tmp_path/'out',command=[],allow_synthetic=True)
    assert not (tmp_path/'out').exists()


def test_authenticated_input(report,tmp_path):
    p=tmp_path/'report.json';p.write_text(json.dumps(report))
    raw=p.read_bytes()
    assert load_report(p,hashlib.sha256(raw).hexdigest())['cube_id']==report['cube_id']
    with pytest.raises(ValueError,match='SHA-256'):
        load_report(p,'a'*64)
    p.write_text('{"version":1,"version":2}')
    with pytest.raises(ValueError):
        load_report(p,hashlib.sha256(p.read_bytes()).hexdigest())


def test_fit_gate_precedes_optimizer(prepared,monkeypatch):
    m,_=prepared
    def forbidden(*args,**kwargs):raise AssertionError('unauthorized optimizer')
    monkeypatch.setattr('app.game.solver.solve_minimax',forbidden)
    with pytest.raises(ValueError,match='blocked'):
        fit_cohort(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,
            authorizations=Authorizations(),freeze_record='SYNTHETIC')
    with pytest.raises(ValueError,match='already frozen'):
        fit_cohort(m,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,
            authorizations=auth_for(m),freeze_record='SYNTHETIC')


def test_authorized_synthetic_fit_freezes_without_changing_contract(prepared):
    m,_=prepared
    c=m.cohort('arithmetic')
    data=m.model_dump()
    data['cohorts'][0]['specification']=fitting_specification(c.frozen.specification).model_dump()
    data['cohorts'][0]['frozen']=None
    prefit=Manifest.model_validate(data)
    result=fit_cohort(prefit,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,
        authorizations=auth_for(prefit),freeze_record='SYNTHETIC freeze only')
    assert result['status']=='frozen'
    fitted=Manifest.model_validate(result['manifest'])
    assert fitted.fitting_id('arithmetic')==prefit.fitting_id('arithmetic')
    assert fitted.protocol_id==prefit.protocol_id
    assert fitted.cohort('arithmetic').frozen.comparison.full_artifact.policy.policy_id==c.frozen.comparison.full_artifact.policy.policy_id


def test_export_multi_group_intervals_and_nulls(report,tmp_path):
    from copy import deepcopy
    from tests.test_experiment1_reporting import cube_fixture
    from app.game.research.experiment1.metrics import point_report,paired_point_differences,bootstrap_report,Statistics
    cube=cube_fixture(groups=3,tiny=True)
    r=deepcopy(report)
    r['metrics']=point_report(cube)
    r['paired_differences']=paired_point_differences(r['metrics'])
    r['uncertainty']=bootstrap_report(cube,Statistics(resamples=20,seed=31))
    factual=deepcopy(r);factual['cohort']='factual'
    root=export_reports([r,factual],tmp_path/'multi',command=['synthetic group test'],allow_synthetic=True)
    import csv
    with (root/'metrics/paired_confidence_intervals.csv').open() as f: rows=list(csv.DictReader(f))
    paired=[i for i in rows if '-minus-' in i['method']]
    assert paired and all(i['point_estimate']!='' for i in paired if i['metric']=='validation_loss')
    assert {i['cohort'] for i in paired}=={'arithmetic','factual'}
    assert any(i['lower95']=='' and i['metric']=='selective_risk' for i in rows)
    assert not json.loads((root/'reports/reproducibility.json').read_text())['absent_cohorts']


def test_reserved_report_path_rejected_before_open(tmp_path,monkeypatch):
    p=tmp_path/'heldout'/'secret.json'
    with pytest.raises(ValueError,match='reserved'):
        load_report(p,'a'*64)


def test_render_failure_leaves_no_destination(report,tmp_path,monkeypatch):
    def broken(*args):raise RuntimeError('plot failure')
    monkeypatch.setattr('app.game.research.experiment1.prospective.export._figures',broken)
    with pytest.raises(RuntimeError,match='plot failure'):
        export_reports([report],tmp_path/'result',command=[],allow_synthetic=True)
    assert not (tmp_path/'result').exists()
    assert not list(tmp_path.glob('.experiment1-export-*'))


def test_execution_cli_final_gate_precedes_payload_io(prepared,tmp_path,monkeypatch):
    import app.game.research.experiment1.prospective.execute as execution
    m,_=prepared
    monkeypatch.setattr(execution,'load_authenticated',lambda p,d,s=None: m if s is None else Authorizations())
    monkeypatch.setattr(execution,'source_fingerprint',lambda root:FP)
    monkeypatch.setattr(execution.subprocess,'check_output',lambda *a,**k:m.source_commit)
    def forbidden(*args):raise AssertionError('unauthorized payload access')
    monkeypatch.setattr('pathlib.Path.read_bytes',forbidden)
    with pytest.raises(ValueError,match='blocked'):
        execution.main(['final','manifest.json','--sha256','a'*64,'--authorizations','auth.json',
            '--authorization-sha256','b'*64,'--cohort','arithmetic','--output',str(tmp_path/'out.json'),
            '--payload',str(tmp_path/'reserved.json')])
    assert not (tmp_path/'out.json').exists()


def test_nonoptimal_fit_preserves_certificate_without_freeze(prepared,monkeypatch):
    m,_=prepared;c=m.cohort('arithmetic');data=m.model_dump()
    data['cohorts'][0]['specification']=fitting_specification(c.frozen.specification).model_dump()
    data['cohorts'][0]['frozen']=None
    prefit=Manifest.model_validate(data)
    failure=c.frozen.comparison.full_artifact.policy.solution.model_copy(update={
        'status':'infeasible','message':'SYNTHETIC infeasible outcome','probabilities':()})
    monkeypatch.setattr('app.game.solver.solve_minimax',lambda *a,**k:failure)
    result=fit_cohort(prefit,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,
        authorizations=auth_for(prefit),freeze_record='SYNTHETIC test')
    assert result['status']=='infeasible'
    assert 'manifest' not in result
    assert result['certificate']['message']=='SYNTHETIC infeasible outcome'
    assert result['matrix']


def test_authorized_cost_inclusive_synthetic_fit(prepared):
    m,_=prepared;c=m.cohort('arithmetic');data=m.model_dump()
    data['cohorts'][0]['specification']=fitting_specification(c.frozen.specification).model_dump()
    data['cohorts'][0]['frozen']=None
    data['cohorts'][0]['choices']['objective']='cost_inclusive_minimax'
    prefit=Manifest.model_validate(data)
    result=fit_cohort(prefit,'arithmetic',actual_commit=m.source_commit,actual_source_fingerprint=FP,
        authorizations=auth_for(prefit),freeze_record='SYNTHETIC cost-inclusive freeze')
    assert result['status']=='frozen'
    matrix=Manifest.model_validate(result['manifest']).cohort('arithmetic').frozen.comparison.full_artifact.policy.matrix
    assert matrix.reliability_first is None
    assert matrix.clean_coverage


def test_execution_cli_records_commands_and_never_overwrites(prepared,tmp_path,monkeypatch):
    import app.game.research.experiment1.prospective.execute as execution
    m,_=prepared
    monkeypatch.setattr(execution,'load_authenticated',lambda p,d,s=None:m if s is None else auth_for(m))
    monkeypatch.setattr(execution,'source_fingerprint',lambda root:FP)
    monkeypatch.setattr(execution.subprocess,'check_output',lambda *a,**k:m.source_commit)
    output=tmp_path/'development.json'
    args=['development','manifest.json','--sha256','a'*64,'--authorizations','auth.json',
        '--authorization-sha256','b'*64,'--cohort','arithmetic','--output',str(output)]
    assert execution.main(args)==0
    report=json.loads(output.read_text())
    receipt=json.loads(output.with_suffix('.json.receipt.json').read_text())
    assert report['execution_receipt']==receipt
    assert receipt['source_commit']==m.source_commit
    assert receipt['command'][-2:]==['--output',str(output)]
    original=output.read_bytes()
    with pytest.raises(FileExistsError):execution.main(args)
    assert output.read_bytes()==original
