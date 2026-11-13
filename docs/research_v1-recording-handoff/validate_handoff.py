"""Stdlib-only handoff checks. No factory, models, network, database or fitting."""
import ast, collections, hashlib, json, os, pathlib, statistics, unittest, zipfile
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[1]
def load(n): return json.loads((HERE/n).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def archive(i,member):
 r=load('provenance.json')['archives'][i]
 p=pathlib.Path(os.environ['RESEARCH_V1_ARTIFACT_DIR'])/r['name'] if 'RESEARCH_V1_ARTIFACT_DIR' in os.environ else pathlib.Path(r['absolute_path'])
 with zipfile.ZipFile(p) as z:
  name=next(n for n in z.namelist() if n.replace('\\','/').split('/')[-1]==member)
  assert 'final' not in name.lower()
  return json.loads(z.read(name))
def class_fields(path,name):
 tree=ast.parse((REPO/path).read_text())
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
 return {n.target.id:ast.unparse(n.annotation) for n in cls.body if isinstance(n,ast.AnnAssign)}
# Acceptance-gate simulator uses fabricated journal metadata, never a verifier.
def safe_resume(request,setup,starts,completions,new_request,new_setup):
 if request!=new_request or setup!=new_setup: raise ValueError('identity drift')
 if len(completions)!=len(set(completions)):raise ValueError('duplicates')
 if set(starts)-set(completions):raise ValueError('ambiguous in-flight')
 return set(completions)
class HandoffTests(unittest.TestCase):
 def test_archive_transport_hashes(self):
  for r in load('provenance.json')['archives']:
   p=pathlib.Path(os.environ['RESEARCH_V1_ARTIFACT_DIR'])/r['name'] if 'RESEARCH_V1_ARTIFACT_DIR' in os.environ else pathlib.Path(r['absolute_path'])
   b=p.read_bytes();self.assertEqual(len(b),r['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
 def test_no_final_payload_opened(self):
  self.assertTrue(load('provenance.json')['no_final_test_payload_opened'])
  self.assertTrue(all('final' not in r['member'].lower() for r in load('provenance.json')['opened_members']))
 def test_source_member_hashes(self):
  m=load('development-scope.json')['source_manifest']
  for r in load('provenance.json')['opened_members']:
   n=r['member'].replace('\\','/').split('/')[-1]
   if r['archive'].startswith('research_v1_exploratory') and n in m['output_sha256']:self.assertEqual(r['sha256'],m['output_sha256'][n])
  for r in load('archive/original-manifest.json'):
   folder='package-a' if r['package']=='A' else 'package-b'
   self.assertEqual(hashlib.sha256((HERE/'archive'/folder/r['relative_path']).read_bytes()).hexdigest(),r['sha256'])
 def test_exact_scope_ids_inputs_and_groups(self):
  s=load('development-scope.json'); rows=s['eligible_source_candidates_pending_approval'];inputs=load('development-verifier-inputs.source.json')
  self.assertEqual(len(rows),774);self.assertEqual(len({r['example_id'] for r in rows}),774)
  self.assertEqual(len({r['related_group_id'] for r in rows}),387)
  self.assertEqual(set(collections.Counter(r['related_group_id'] for r in rows).values()),{2})
  byid={r['candidate_id']:r for r in inputs}
  for r in rows:
   self.assertEqual(r['split_identity'],r['related_group_id']);self.assertEqual(r['approval'],'PENDING')
   for k in ['question_id','question','candidate_answer','benchmark','related_group_id']:self.assertEqual(r[k],byid[r['example_id']][k])
  self.assertEqual(s['approved_examples'],[])
 def test_history_development_identity_separation(self):
  h=load('history-source-roster.json')['examples'];d=load('development-scope.json')['eligible_source_candidates_pending_approval']
  self.assertEqual(len(h),1153);self.assertEqual(len({r['related_group_id'] for r in h}),577)
  for key in ['candidate_id','question_id','related_group_id','content_identity']:
   self.assertFalse({r[key] for r in h} & {r[key] for r in d},key)
 def test_label_claims_not_promoted(self):
  s=load('development-scope.json'); self.assertEqual(s['source_manifest']['human_verified_labels'],0)
  self.assertTrue(all(not r['independent_label_accepted'] and not r['human_verified'] and r['label_protocol']=='provisional_automated_labeling_v1' for r in s['eligible_source_candidates_pending_approval']))
 def test_resource_identity_and_rehearsal(self):
  r=load('resource-compatibility.json');self.assertEqual(digest(r['expected_setup']['resources']),r['expected_resource_manifest_id'])
  self.assertEqual(r['expected_setup']['resources'],r['rehearsal_manifest']['resource_manifest'])
  self.assertEqual(r['actual_live_values'],None);self.assertTrue(r['unresolved'])
 def test_cost_means_status_and_warmups(self):
  m=archive(1,'measurements.json');c=load('calibration-evidence.json')
  self.assertEqual(len(m['attempts']),488);self.assertEqual(sum(a['purpose']=='warmup' for a in m['attempts']),8)
  for est in c['result']['estimates']:
   rows=[a for a in m['attempts'] if a['verifier_name']==est['verifier_name'] and a['purpose']!='warmup']
   self.assertEqual(len(rows),120);self.assertEqual(sum(a['status']!='returned' for a in rows),est['failures'])
   self.assertEqual(statistics.mean(a['duration_ms'] for a in rows),est['attempt_cost'])
  self.assertEqual(c['measurement_status_counts'],{'returned':488})
 def test_no_authorization_and_full_roster(self):
  c=load('recording-config.proposed.json');self.assertFalse(c['collection_authorized']);self.assertFalse(c['fitting_authorized']);self.assertIsNone(c['freeze_id'])
  self.assertEqual(c['collection']['candidate_roster'],['confidence','evidence','rule','semantic'])
  self.assertFalse(c['collection']['early_termination']);self.assertFalse(c['collection']['candidate_policy_selection_during_recording'])
  self.assertIsNone(c['planning']['budget_ms']['approved_value']);self.assertIsNone(c['planning']['cost_coefficient']['approved_value'])
 def test_actual_record_schema_fields_static(self):
  a=class_fields('app/game/offline/records.py','Attempt');e=class_fields('app/game/offline/records.py','Example');r=class_fields('app/game/offline/collection.py','RecordingRequest')
  self.assertIn("'missing'",a['state']);self.assertNotIn('duration_ms',a)
  self.assertIn('answer_is_correct',e);self.assertIn('planning_category',e)
  self.assertIn('expected_setup',r);self.assertIn('study_approval',r)
  self.assertIn('report_provenance',a);self.assertIn('observed_resources_json',a)
 def test_synthetic_resume_gate(self):
  self.assertEqual(safe_resume('r','s',['a'],['a'],'r','s'),{'a'})
  for args in [('r','s',['a'],[],'r','s'),('r','s',['a'],['a','a'],'r','s'),('r','s',[],[],'changed','s'),('r','s',[],[],'r','changed')]:
   with self.assertRaises(ValueError):safe_resume(*args)
 def test_dependency_and_replay_obligations_static(self):
  text=(REPO/'app/game/offline/replay.py').read_text()
  self.assertIn('set(lookup) != candidate_names',text);self.assertIn('a.state == "missing"',text)
  text=(REPO/'app/game/dependencies.py').read_text();self.assertIn('shared_unknown',text)
 def test_only_handoff_files_changed(self):
  from ownership import check
  self.assertIsInstance(check(), list)
if __name__=='__main__':unittest.main(verbosity=2)
