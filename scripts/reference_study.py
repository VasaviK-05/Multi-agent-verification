"""Bounded fresh reference frames; preparation has no model calls or outcome input."""
import argparse
from dataclasses import asdict
import hashlib,json
from pathlib import Path
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.analysis.reference_study_analyzer import analyze_reference,VERSION
from app.game.models import content_id
from app.game.offline.collection import RecordingRequest,PreparationExample
from app.game.offline.records import FinalTestReservation,ReservedExample

ROOT=Path('artifacts/remaining-category-studies-v1/reference')
OLD=Path('artifacts/compound-study-36-v1')
AUTH='User attachment 9d033868: fresh30 groups,60 examples,240 attempts,300 local generations; no retries or deployment.'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,v):
    if hasattr(v,'model_dump'):v=v.model_dump(mode='json')
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)

# Independent constructed predicate frames, not sampled model text. Each tuple
# fixes truth conditions, equivalent wording and one changed semantic feature.
# No entity/predicate combination or lexicalized template crosses partitions.
FRAMES=[
('count','Seven lanterns hang above the marina.','Above the marina hang seven lanterns.','Eight lanterns hang above the marina.'),
('count','The archivist catalogued eleven scrolls yesterday.','Yesterday eleven scrolls were catalogued by the archivist.','The archivist catalogued twelve scrolls yesterday.'),
('count','Exactly six otters inhabit the lagoon.','The lagoon is inhabited by exactly six otters.','Exactly nine otters inhabit the lagoon.'),
('count','A baker packed thirteen croissants for delivery.','For delivery, thirteen croissants were packed by a baker.','A baker packed fourteen croissants for delivery.'),
('count','There are three satellites orbiting the fictional planet Vesta.','The fictional planet Vesta has three orbiting satellites.','There are two satellites orbiting the fictional planet Vesta.'),
('count','Five musicians rehearsed inside the pavilion.','Inside the pavilion, five musicians took part in rehearsal.','Four musicians rehearsed inside the pavilion.'),
('count','The inspection recorded sixteen cracks in the dam.','Sixteen cracks in the dam were recorded during the inspection.','The inspection recorded seventeen cracks in the dam.'),
('count','Eight appointments remain on the dentist schedule.','The dentist schedule still contains eight appointments.','Ten appointments remain on the dentist schedule.'),
('negation','Selene never watered the cactus on Tuesday.','On Tuesday the cactus was never watered by Selene.','Selene watered the cactus on Tuesday.'),
('negation','The locksmith did not repair the bronze latch.','The bronze latch was not repaired by the locksmith.','The locksmith repaired the bronze latch.'),
('negation','No ferries departed from the northern pier this morning.','This morning not a single ferry left the northern pier.','A ferry departed from the northern pier this morning.'),
('negation','Ivo has not signed the rental agreement.','The rental agreement remains unsigned by Ivo.','Ivo has signed the rental agreement.'),
('negation','The inspector denied approving the turbine.','The inspector said that they had not approved the turbine.','The inspector said that they had approved the turbine.'),
('negation','None of the violet balloons burst during the parade.','Not one violet balloon burst during the parade.','At least one violet balloon burst during the parade.'),
('negation','Rhea did not photograph the comet last night.','Last night the comet was not photographed by Rhea.','Rhea photographed the comet last night.'),
('negation','The chef excluded sesame from the soup.','The soup prepared by the chef contained no sesame.','The chef included sesame in the soup.'),
('role','Dorian sold a violin to Elara.','Elara bought a violin from Dorian.','Elara sold a violin to Dorian.'),
('role','Farah taught geology to Gideon.','Gideon learned geology from Farah.','Gideon taught geology to Farah.'),
('role','Helena received a parcel from Idris.','Idris sent a parcel to Helena.','Helena sent a parcel to Idris.'),
('role','Jules defeated Kiran in the final match.','Kiran lost the final match to Jules.','Kiran defeated Jules in the final match.'),
('role','Leonie was followed through the tunnel by Malik.','Malik followed Leonie through the tunnel.','Leonie followed Malik through the tunnel.'),
('role','Nadia invited Orson to the symposium.','Orson was invited to the symposium by Nadia.','Orson invited Nadia to the symposium.'),
('role','Petra inherited a cottage from Quentin.','Quentin left a cottage to Petra as an inheritance.','Quentin inherited a cottage from Petra.'),
('spatial','The fountain stands north of the observatory.','The observatory stands south of the fountain.','The fountain stands south of the observatory.'),
('spatial','The silver vase rests above the walnut shelf.','The walnut shelf is below the silver vase.','The silver vase rests below the walnut shelf.'),
('spatial','The tram stop lies east of the greenhouse.','The greenhouse lies west of the tram stop.','The tram stop lies west of the greenhouse.'),
('spatial','The copper disk is inside the transparent cylinder.','The transparent cylinder contains the copper disk.','The copper disk is outside the transparent cylinder.'),
('spatial','The ambulance is parked behind the theatre.','The theatre is in front of the parked ambulance.','The ambulance is parked in front of the theatre.'),
('spatial','The pine bench is to the right of the stone arch.','The stone arch is to the left of the pine bench.','The pine bench is to the left of the stone arch.'),
('spatial','The coral bead is beneath the ivory plate.','The ivory plate is above the coral bead.','The coral bead is above the ivory plate.'),
]

def prepare():
    ROOT.mkdir(parents=True,exist_ok=True)
    if any(ROOT.iterdir()):raise ValueError('refuse to overwrite prepared study')
    analyzer=TaskQuestionAnalyzer();groups=[]
    for i,(family,ref,good,bad) in enumerate(FRAMES):
        gid=f'reference-fresh-{i:02d}'
        groups.append(dict(group_id=gid,family=family,reference=ref,equivalent=good,non_equivalent=bad,
            question='Paraphrase this reference: '+ref,
            label_proof='Equivalent preserves all predicate arguments, polarity, exact count and spatial orientation; negative changes '+family+'.',
            construction='Independent explicit semantic frame; no generation or verifier outputs used.'))
    # Family-stratified deterministic assignment, fixed before any outputs.
    roles=['history','development','final_test'];totals={r:0 for r in roles}
    for family in ('count','negation','role','spatial'):
        local=sorted((g for g in groups if g['family']==family),key=lambda g:content_id(['reference-fresh-v1-seed1103',g['group_id']]))
        for g in local:
            role=min(roles,key=lambda r:(totals[r],roles.index(r)));g['role']=role;totals[role]+=1
    assert set(totals.values())=={10}
    examples=[]
    for g in groups:
        for correct,key in ((True,'equivalent'),(False,'non_equivalent')):
            eid=g['group_id']+('-equivalent' if correct else '-contrast')
            examples.append(dict(example_id=eid,split_identity=g['group_id'],question_id=content_id(g['question']),
                run_id='reference-fresh-v1-'+eid,dataset_id='reference-fresh-v1-'+g['role'],role=g['role'],
                purpose='heldout' if g['role']=='final_test' else 'calibration',question=g['question'],answer=g[key],reference=g['reference'],
                analysis=asdict(analyze_reference(g['question'])),label=dict(answer_is_correct=correct,
                    label_source='independent-constructed-reference-frames-v1',label_method='independent_ground_truth',provenance=g['label_proof'])))
    signatures={(e['analysis']['domain'],e['analysis']['difficulty'],e['analysis']['difficulty_score']) for e in examples}
    if len(signatures)!=1:raise ValueError('Question-only planning categories differ: '+repr(signatures))
    reservation=FinalTestReservation(version='final_test_reservation_v1',role='final_test',dataset_id='reference-fresh-v1-final_test',
        custody_record='Procedurally reserved before collection; author prepared independent labels; not blinded external custody.',examples=tuple(
        ReservedExample(example_id=e['example_id'],split_identity=e['split_identity'],question_id=e['question_id'],
            content_identity=content_id([e['question'],e['answer'],e['reference']]),validation_id=e['run_id']) for e in examples if e['role']=='final_test'))
    setup=read(OLD/'preparation/setup.json');old=read('artifacts/capability-probes-v1/candidates.json')
    request=RecordingRequest(version='offline_recording_request_v1',intended_use='study',study_approval=AUTH,
        preparation_authorization=AUTH,cache_contract='complete_team_independent_v1',randomness_control='Existing n5 temperature.8 seeds0..4; stochastic local service, no deterministic claim.',
        execution_configuration_id=setup['resources'] and content_id(setup['resources']),factory='app.benchmark.project_adapter:create_recording_verifiers',
        expected_setup=setup,final_test_reservation=reservation,permitted_datasets=tuple((r,'reference-fresh-v1-'+r) for r in roles[:2]),
        candidates=old,examples=tuple(PreparationExample(**e) for e in examples if e['role']!='final_test'))
    base=read('artifacts/flexible-teams-v1/arithmetic-minimum-1/context.json')
    save(ROOT/'groups.json',groups);save(ROOT/'reserved-examples.json',[e for e in examples if e['role']=='final_test'])
    save(ROOT/'request.json',request)
    save(ROOT/'protocol.json',dict(version='reference-fresh-v1',routing_version=VERSION,difficulty='One bounded category constant easy/.1, not empirical adaptation; legacy word-count scores span .06–.10.',grammar='Paraphrase this reference: <one exact predeclared reference>',
        scope='30 explicit frames only, no API activation or broad difficulty adaptation',partitions=totals,seed='reference-fresh-v1-seed1103',
        grouping='All lexicalized entity/predicate/template frames and both answer variants grouped; broad contrast families recur across partitions.',
        independent_label_rule='Semantic predicate/argument/count/polarity/spatial equivalence, never cosine or verifier agreement.',
        reference_contract='Fixed legitimate source text provided to semantic comparison; raw cosine measurement is not equivalence certification.',
        minimum_clean_development_coverage=.9,threshold=.55,min_informative_contributors=1,history='Fresh Beta(1,1), directional history only, no cross-task copying.',
        costs='Per-verifier mean measured history+development wall_ms, no warmup; budget=sum four means; resource penalty=.1/budget.',
        losses=dict(false_accept=1.,false_reject=1.,uncertain=.2),dependencies=base['dependencies'],
        attacks=dict(version='report_corruption_v1',suppression='unavailable'),objective='Worst finalized validation loss then attempt cost, epsilon1e-8.',
        fitting='All genuinely eligible teams sizes1–4, both existing aggregations; no team quotas.',
        caps=dict(all_examples=60,all_attempts=240,all_generations=300,training_examples=40,training_attempts=160,training_generations=200,reserved_examples=20,reserved_attempts=80,reserved_generations=100),
        fixed_baseline='Development-best coverage-eligible fixed team; valid existing greedy under identical contract if feasible.',
        uncertainty=dict(method='group bootstrap',seed=1103,resamples=1000),authorization=AUTH))
    files=[ROOT/'groups.json',ROOT/'reserved-examples.json',ROOT/'request.json',ROOT/'protocol.json',Path(__file__),Path('scripts/collect_reference_study.py'),Path('app/analysis/reference_study_analyzer.py'),Path('app/game/question_routing.py')]
    save(ROOT/'seal.json',{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    print('PREPARED',request.request_id,signatures,flush=True)
if __name__=='__main__':prepare()
