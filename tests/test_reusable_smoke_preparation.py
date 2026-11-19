"""Plan preparation and execution interlock only; no native execution."""
import json
from pathlib import Path
import pytest
from scripts.reusable_native_smoke import prepare,execute


def test_prepare_seals_independent_references_and_native_caps(tmp_path,monkeypatch):
    import app.game.offline.singleton_compatibility as singleton
    import app.game.offline.reference_compatibility as reference
    def forbidden(*args,**kwargs):raise AssertionError('preparation constructed a native pool')
    monkeypatch.setattr(singleton,'create_singleton',forbidden)
    monkeypatch.setattr(reference,'create_reference',forbidden)
    output=tmp_path/'plans';rows=prepare(output)
    plans={row['kind']:json.loads(Path(row['path']).read_text()) for row in rows}
    arithmetic=plans['arithmetic']
    assert arithmetic['reference_receipt']['candidate_independent']
    assert [r['context'] for r in arithmetic['requests']]==['8','8']
    assert [r['answer'] for r in arithmetic['requests']]==['8','9']
    assert arithmetic['maximum_native_attempts']==2 and arithmetic['maximum_generations']==0
    assert arithmetic['execution_authorized'] is False and arithmetic['blockers']==[]
    assert plans['evidence']['blockers'] and plans['reference']['blockers']
    assert plans['reference']['maximum_generations']==5
    assert len([p for p in plans['reference']['probabilities'] if p[1]>0])==2


def test_execute_requires_explicit_separate_approval_before_reading_plan(tmp_path):
    with pytest.raises(ValueError,match='separate explicit owner approval'):
        execute(tmp_path/'does-not-exist.json','not-approved',tmp_path/'no-output')
    assert not (tmp_path/'no-output').exists()


def test_native_journal_rejects_zero_probability_and_duplicate_attempts(tmp_path):
    from scripts.reusable_native_smoke import NativeJournal
    plan=dict(artifact_id='artifact',policy_id='policy',strategies=[
        dict(strategy_id='allowed',verifiers=['rule'],aggregation='reputation_weighted'),
        dict(strategy_id='zero',verifiers=['rule'],aggregation='dependency_group')],
        probabilities=[['allowed',1.],['zero',0.]],maximum_native_attempts=2,
        allowed_native_names=['rule'],requests=[dict(question='Q',answer='A',context='R')])
    journal=NativeJournal(tmp_path,plan);journal.current=0
    with pytest.raises(ValueError,match='unchanged fitted distribution'):
        journal.set_plan(dict(strategy_id='zero',artifact_id='artifact',policy_id='policy',team=['rule'],aggregation='dependency_group'))
    journal.set_plan(dict(strategy_id='allowed',artifact_id='artifact',policy_id='policy',team=['rule'],aggregation='reputation_weighted'))
    journal.start_attempt(verifier_name='rule')
    with pytest.raises(ValueError,match='retry blocked'):journal.start_attempt(verifier_name='rule')
    assert len(journal.starts)==1


def test_smoke_isolation_rejects_external_writes_and_child_processes(tmp_path):
    import os
    from scripts.reusable_native_smoke import enforce_output_only
    output=tmp_path/'receipt'
    def reject(reason):raise RuntimeError(reason)
    for event,args in [
        ('open',(str(tmp_path/'outside.json'),'w',os.O_CREAT|os.O_WRONLY)),
        ('os.mkdir',(str(tmp_path/'cache'),0o777,-1)),
        ('os.rename',(str(output/'a'),str(tmp_path/'outside'),-1,-1)),
        ('subprocess.Popen',('ollama',[],None,None)),
        ('os.system',('ollama serve',)),
    ]:
        with pytest.raises(RuntimeError):enforce_output_only(event,args,output,reject)
    enforce_output_only('open',(str(output/'ledger.json'),'w',os.O_WRONLY),output,reject)
    enforce_output_only('open',(str(tmp_path/'input'),'r',os.O_RDONLY),output,reject)


def test_reference_free_planning_is_representable_but_not_historically_compatible():
    from scripts.reconciliation import load_bundle
    from app.game.question_routing import classify_question
    from app.game.models import capture_context
    from app.game.frozen_planning import frozen_selector
    from app.selection.verifier_selector import VerifierSelector
    from app.selection.capabilities import BUILTIN_CAPABILITIES
    _,provider,_=load_bundle()
    artifact=next(a for a in provider.snapshot() if a.artifact_id=='cf4507400b26f79ab63366ab64b25ef779870fb85f8c33f7aa60a735a4762477')
    kind,_,analysis=classify_question('What is 4 + 4?',None)
    assert kind=='atomic'
    current=capture_context(frozen_selector(VerifierSelector(capabilities=BUILTIN_CAPABILITIES),artifact.context),
        analysis,context=None,**artifact.context.model_dump(exclude={'selection_json','analyzer_provenance'}))
    assert current.requirement_signature==artifact.context.requirement_signature
    assert not current.plan.reference_available
    rows={c.verifier_name:c for c in current.plan.candidates}
    assert rows['rule'].eligible and not rows['rule'].requires_reference
    assert not rows['semantic'].eligible and rows['semantic'].prerequisite_status=='missing_reference'
    assert current.compatibility_id!=artifact.context.compatibility_id
