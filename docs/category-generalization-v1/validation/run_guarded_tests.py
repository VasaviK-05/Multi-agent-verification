"""Execute offline tests with no network, database, native Rule or model access.

Synthetic analytical/LP unit tests are permitted; empirical fitting is forbidden.
Native Rule cases are explicitly deselected, not replaced with fake passes.
"""
import inspect
import json
import os
from pathlib import Path
import sys
import threading
ROOT=Path(os.environ.get('CATEGORY_TEST_ROOT', str(Path(__file__).resolve().parents[3])))
sys.path.insert(0,str(ROOT))
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')


def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        raise RuntimeError('Forbidden network access in category engineering tests')
sys.addaudithook(audit)
import psycopg2
psycopg2.connect=lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError('Database connection forbidden'))


def profile(frame,event,arg):
    if event!='call':return
    filename=frame.f_code.co_filename.replace('\\','/')
    name=frame.f_code.co_name
    if name=='verify' and filename.endswith('/app/verifiers/rule_verifier.py'):
        raise RuntimeError('Native Rule execution not authorized; use report fixtures')
    if name in {'__call__','__init__','encode','forward','from_pretrained','snapshot_download','hf_hub_download'}:
        if ('sentence_transformers' in filename and ('SentenceTransformer.py' in filename or name=='from_pretrained')
            or ('transformers' in filename and name=='from_pretrained')
            or ('huggingface_hub' in filename and name in {'snapshot_download','hf_hub_download'})
            or (filename.endswith('/app/verifiers/self_consistency.py') and name=='__call__'
                and type(frame.f_locals.get('self')).__name__=='OllamaSampler')):
            raise RuntimeError('Native model/provider access forbidden')
    if name in {'fit_policy','construct_payoffs','fit_clean_coverage','fit_reliability_first'} and '/app/game/' in filename:
        context=frame.f_locals.get('context'); manifest=frame.f_locals.get('manifest')
        provenance=getattr(context,'provenance',None)
        if getattr(provenance,'evidence_kind',None)=='empirical' or getattr(manifest,'evidence_kind',None)=='empirical':
            raise RuntimeError('Empirical fitting/evaluation campaign forbidden')


NATIVE_COMPONENT_CASES = {
    'test_component_correctness_and_complete_execution',
    'test_failure_resource_checks_and_unrelated_support',
    'test_component_journal_callback_preserves_binding_identity_and_typed_failure',
    'test_repeated_verifier_cost_and_distinct_contributors',
    'test_joint_policy_sampling_and_category_registry',
    'test_resource_drift_and_bound_report_identity',
    'test_unavailable_component_coverage_cannot_be_certified_by_arithmetic',
    'test_active_resource_observer_receives_actual_selector',
}

class NativeCases:
    def pytest_collection_modifyitems(self,config,items):
        selected=[];deselected=[]
        for item in items:
            try:source=inspect.getsource(item.function)
            except (AttributeError,TypeError,OSError):source=''
            if ('RuleVerifier(' in source or item.nodeid.startswith('tests/test_validation.py::')
                    or (item.nodeid.startswith('tests/test_component_execution.py::')
                        and item.originalname in NATIVE_COMPONENT_CASES)):
                deselected.append(item)
            else:selected.append(item)
        items[:]=selected
        if deselected:config.hook.pytest_deselected(items=deselected)

# Explicit boundary patches remain active even if Python disables a failing
# profiler callback; all are test-process-only prohibitions, never fake passes.
from app.verifiers.rule_verifier import RuleVerifier
from app.verifiers.self_consistency import OllamaSampler
from sentence_transformers import SentenceTransformer
import app.verifiers.evidence_verifier as evidence_module

def forbidden_native(*args, **kwargs):
    raise RuntimeError('Native inference/provider/Rule execution not authorized')
RuleVerifier.verify = forbidden_native
OllamaSampler.__call__ = forbidden_native
SentenceTransformer.__init__ = forbidden_native
SentenceTransformer.encode = forbidden_native
evidence_module.default_nli_pipeline = forbidden_native
sys.setprofile(profile)
threading.setprofile(profile)
import pytest
raise SystemExit(pytest.main(sys.argv[1:]+['-p','no:cacheprovider'],plugins=[NativeCases()]))
