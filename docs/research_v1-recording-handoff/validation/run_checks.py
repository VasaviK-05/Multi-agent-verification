"""Guarded offline engineering validation; synthetic test adapters only."""
import ast
import json
import os
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTHONDONTWRITEBYTECODE','PYTHON_DOTENV_DISABLED'):
    os.environ[key]='1'
sys.dont_write_bytecode=True
kind=sys.argv[1]
counts={'plain_assert_evaluations':0,'unittest_assertion_method_calls':0}
asserts={}
for p in [ROOT/'tests/test_offline_file_journal.py',ROOT/'tests/test_research_v1_inputs.py',
          ROOT/'tests/test_research_v1_boundaries.py',ROOT/'tests/test_research_v1_ownership.py',
          ROOT/'tests/test_game_foundation.py',ROOT/'tests/test_game_collection.py']:
    asserts[str(p)]={n.lineno for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Assert)}
def trace(frame,event,arg):
    if event=='line' and frame.f_lineno in asserts.get(frame.f_code.co_filename,()):counts['plain_assert_evaluations']+=1
    return trace

def profile(frame,event,arg):
    if event=='c_call' and getattr(arg,'__name__','')=='connect' and str(getattr(arg,'__module__','')).startswith('psycopg2'):
        raise RuntimeError('Database connections forbidden during checks')
    if event!='call':return
    if frame.f_code.co_name=='get_connection' or (frame.f_code.co_name=='connect' and 'psycopg2' in frame.f_code.co_filename):
        raise RuntimeError('Database connections forbidden during checks')
    name=frame.f_code.co_name;file=frame.f_code.co_filename.replace('\\','/')
    if ('/unittest/case.py' in file and name.startswith('assert') and frame.f_back is not None
        and frame.f_back.f_code.co_filename==str(ROOT/'docs/research_v1-recording-handoff/validate_handoff.py')):
        counts['unittest_assertion_method_calls']+=1
    if name in {'fit_policy','construct_payoffs','solve_minimax','solve_reliability_first','calibrate',
                'evaluate_final_test','evaluate_reserved_final','from_pretrained'}:
        raise RuntimeError('Forbidden during engineering checks: '+name)
    if '/app/verifiers/' in file and name in {'verify','__init__'}:
        raise RuntimeError('Real verifier construction/execution forbidden: '+file)

def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:raise RuntimeError('Network forbidden during checks')
    if event=='open' and args and isinstance(args[0],str):
        p=args[0].replace('\\','/').lower()
        if any(s in p for s in ['/datasets/final_test','/datasets/processed/final_test','/datasets/unified/final_test']):
            raise RuntimeError('Final Test payload access forbidden')
sys.addaudithook(audit);sys.settrace(trace);sys.setprofile(profile)
if kind=='handoff':
    sys.path.insert(0,str(ROOT/'docs/research_v1-recording-handoff'))
    sys.argv=['validate_handoff.py','-v']
    try:runpy.run_path(str(ROOT/'docs/research_v1-recording-handoff/validate_handoff.py'),run_name='__main__');code=0
    except SystemExit as exc:code=int(exc.code or 0)
else:
    import pytest
    files={'eligibility':['tests/test_research_v1_eligibility.py'],
           'regression':['tests/test_policy_package.py','tests/test_policy_source_compatibility.py'],
           'filesystem':['tests/test_offline_file_journal.py'],
           'input':['tests/test_research_v1_inputs.py'],
           'boundaries':['tests/test_research_v1_boundaries.py','tests/test_research_v1_ownership.py'],
           'planning':['tests/test_game_foundation.py','-k',' or '.join([
            'equivalent_requirement_sets_have_same_signature_and_versions_are_preserved',
            'requirement_uncertainty_is_not_an_empty_feasible_obligation',
            'dependencies_overlap_unknowns_order_and_bridge_projection',
            'known_and_unknown_dependency_overlap_merges_conservatively',
            'maximum_enumeration_and_constraints_are_independent',
            'existing_execution_floor_is_preserved_for_easy_questions',
            'zero_weight_obligations_still_require_expected_coverage',
            'configuration_order_does_not_change_semantic_compatibility_or_strategies'])],
           'existing-boundaries':['tests/test_game_collection.py','-k',' or '.join([
            'measurement_export_rechecks_stored_resource_observations',
            'fresh_collector_import_and_collection_has_no_db_api_or_reputation_io',
            'valid_collection_never_reads_released_final_payload',
            'stable_links_exclude_incidental_durations','failures_retained_without_dropping_or_stopping',
            'interrupt_and_malformed_report_are_explicit_incomplete_outcomes',
            'unknown_and_changed_resources_are_never_invented',
            'post_observation_candidate_and_actual_timing_status_checked',
            'invalid_inputs_reject_before_factory_execution','cli_journal_recovery_and_export',
            'unapproved_study_and_incompatible_export_are_rejected',
            'smoke_cannot_be_promoted_and_fit_settings_not_required'])]}
    code=pytest.main(['-q','--assert=plain','-p','no:cacheprovider',*files[kind]])
sys.settrace(None);sys.setprofile(None)
print(json.dumps({'suite':kind,'exit_code':code,**counts,
 'assertion_note':'Plain assert evaluations exclude pytest.raises and subprocess assertions. Unittest count includes direct assertion-method calls from handoff checks, not delegated helper calls.'}))
raise SystemExit(code)
