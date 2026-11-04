"""Predeclare exploratory capability probes, labels and resource inputs. No inference."""
import argparse
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from app.analysis.task_analyzer import TaskQuestionAnalyzer
from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer,question_profile
from app.game.models import content_id
from app.selection.requirements import requirement_inputs


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def prepare(source,output):
    output.mkdir(parents=True,exist_ok=False)
    corpus={r['id']:r for r in read(source/'corpus.json')}
    old=read(source/'factual/preparation.json')['examples'];facts={}
    for kind in ('area','population','currency'):
        rows=sorted((e for e in old if e['role']=='history' and e['label']['answer_is_correct'] and json.loads(e['label']['provenance'])['kind']==kind),key=lambda e:e['example_id'])
        facts[kind]=next(e for e in rows if json.loads(e['label']['provenance'])['iso'] in corpus)
    # Fixed, first-eligible source-based examples; no verifier outputs or held-out labels.
    assert facts['area']['question']=='What is the area of Bahrain?'
    assert facts['population']['question']=='What is the population of Belgium?'
    assert facts['currency']['question']=='What is the currency of Cuba?'
    countries=read(source/'sources/countries.json');mexico=next(c for c in countries if c['cca2']=='MX')
    assert mexico['currencies']['MXN']['name']=='Mexican peso'
    groups=[]
    def add(gid,family,q,ref,good,bad,checks,why,support,provenance):
        assert good!=bad
        groups.append(dict(group_id=gid,family=family,question=q,reference=ref,answers=[dict(answer=good,answer_is_correct=True),dict(answer=bad,answer_is_correct=False)],required_checks=checks,expected_eligible=['semantic','evidence','rule','confidence'],why_additional_checking_might_help=why,input_support=support,independent_label_provenance=provenance,known_limitations='No independent failure-path guarantee; new wording/contrasts may shift reliability away from prior narrow history. References are legitimate fixed comparison inputs, not correctness labels.'))
    assert Decimal(37)*19==703
    add('a-multiply','arithmetic','What is 37 * 19?','The product of 37 and 19 is 703.','703','693',['arithmetic'],'Compare exact multiplication with generation agreement and reference resemblance.','Supported binary Rule input; other verifiers may abstain or disagree.','Independent Decimal integer multiplication: 37*19=703.')
    assert Decimal(25)-17==8
    add('a-word-difference','arithmetic','What is the difference between 25 and 17?','Subtracting 17 from 25 yields 8.','8','42',['arithmetic'],'Exercise wording accepted by Rule but missed by the existing analyzer; additional results cannot replace missing routing.','Rule input supported; legacy analyzer requirements unknown; opt-in analyzer adds a versioned category.','Independent integer subtraction; wrong answer is the sum, not the difference.')
    assert Decimal(17)/4==Decimal('4.25')
    add('a-division','arithmetic','What is 17 / 4?','Seventeen divided by four equals 4.25.','4.25','4.2',['arithmetic'],'Check exact arithmetic versus a nearby numeric distractor under the existing rounding policy.','Supported binary Rule input; 4.2 is wrong even at its displayed precision (expected 4.3).','Independent Decimal division and explicit half-up rounding check.')
    for kind,bad in [('area','The area of Bahrain is 766 square kilometres.'),('population','The population of Belgium is 11941718.'),('currency','The currency of Cuba is the Mexican peso.')]:
        e=facts[kind]
        add('f-'+kind,'factual',e['question'],e['reference'],e['answer'],bad,['direct_fact'],'Contrast retrieval/NLI with similarity and generation agreement on a near-number or related-currency distractor.','Existing factual interface; numeric facts do not imply arithmetic coverage.',json.loads(e['label']['provenance']))
    frames=[('number','Nora placed four amber tokens in the blue box.','Four amber tokens were placed in the blue box by Nora.','Nora placed five amber tokens in the blue box.','Exact count preservation versus four-to-five change.'),('negation','Owen did not open the red gate.','The red gate was not opened by Owen.','Owen opened the red gate.','Explicit negation preserved versus reversed.'),('roles','Mira lent a book to Theo.','Theo borrowed a book from Mira.','Theo lent a book to Mira.','Lender/borrower roles preserved versus reversed.'),('spatial','The cedar crate is to the left of the oak crate.','The oak crate is to the right of the cedar crate.','The cedar crate is to the right of the oak crate.','Left/right inverse relation preserved versus contradicted.')]
    for kind,ref,good,bad,proof in frames:
        add('s-'+kind,'semantic','Paraphrase this reference: '+ref,ref,good,bad,['semantic_comparison'],'Contrast logical equivalence with cosine resemblance and generation/NLI agreement.','Semantic input/measurement supported; similarity contract is not a logical-equivalence certificate. Synthetic frames are not added to the retrieval corpus.',dict(method='independent predicate/argument/count/negation reasoning',proof=proof))
    add('m-area','mixed','What is the area of Bahrain, and what is that area plus 10 square kilometres? Give both values.',facts['area']['reference'],'The area of Bahrain is 765 square kilometres. Adding 10 gives 775 square kilometres.','The area of Bahrain is 765 square kilometres. Adding 10 gives 774 square kilometres.',['direct_fact','arithmetic'],'Requires retrieving the base fact and checking the derived result; merely selecting two names cannot bind components.','Diagnostic compound only; whole-question Rule matching and component binding are unsupported.',dict(fact=json.loads(facts['area']['label']['provenance']),calculation='765+10=775',negative='Correct base fact, incorrect derived sum.'))
    add('m-population','mixed','What is the population of Belgium, and what is that population plus 1000? Give both values.',facts['population']['reference'],'The population of Belgium is 11941781. Adding 1000 gives 11942781.','The population of Belgium is 11941718. Adding 1000 gives 11942718.',['direct_fact','arithmetic'],'Distinguish a wrong retrieved base fact from an internally consistent calculation on that wrong base.','Diagnostic compound only; a fact-looking prefix must not drop the arithmetic obligation.',dict(fact=json.loads(facts['population']['label']['provenance']),calculation='11941781+1000=11942781',negative='Wrong base fact; addition internally correct for the supplied wrong base, but whole answer incorrect.'))
    assert len(groups)==12
    baseline=TaskQuestionAnalyzer();owned=CapabilityProbeAnalyzer();examples=[];labels={}
    for group in groups:
        group['legacy_analysis']=asdict(baseline.analyze(group['question']))
        group['owned_analysis']=asdict(owned.analyze(group['question']))
        group['profile']=asdict(question_profile(group['question']))
        group['legacy_requirements']=asdict(requirement_inputs(baseline.analyze(group['question'])))
        group['owned_requirements']=asdict(requirement_inputs(owned.analyze(group['question'])))
        for row in group['answers']:
            eid=group['group_id']+('-correct' if row['answer_is_correct'] else '-incorrect')
            labels[eid]=dict(**row,group_id=group['group_id'],family=group['family'],required_checks=group['required_checks'],provenance=group['independent_label_provenance'])
            examples.append(dict(example_id=eid,split_identity=group['group_id'],question_id=content_id(group['question']),run_id='capability-probes-v1-'+eid,dataset_id='capability-probes-v1-diagnostic',role='development',purpose='calibration',question=group['question'],answer=row['answer'],reference=group['reference'],analysis=group['owned_analysis'],label=None))
    exclusions=[]
    for co in ('arithmetic','factual','semantic'):exclusions+=read(source/co/'reservation.json')['examples']
    save(output/'groups.json',groups);save(output/'examples.json',examples);save(output/'labels.json',labels)
    save(output/'exclusions.json',dict(version='diagnostic_exclusion_roster_v1',role='final_test',dataset_id='completed-study-reservations-excluded',examples=exclusions))
    save(output/'candidates.json',read(source/'arithmetic/preparation.json')['candidates'])
    preserved={str(p.resolve()):sha(p) for base in [Path('artifacts/flexible-teams-v1'),Path('artifacts/flexible-heldout-v1'),Path('artifacts/policies')] for p in base.rglob('*') if p.is_file()}
    save(output/'protocol.json',dict(version='capability_probes_v1',exploratory_only=True,groups=12,answer_examples=24,maximum_verifier_attempts=96,maximum_generation_requests=120,n_samples=5,temperature=.8,timeout_per_generation_seconds=60,selection='Examples fixed by parser/input contracts and independent verification needs, before outcomes. Factual sources selected from history-role inputs only; no held-out outcomes used.',labels='Independent arithmetic/structured source/reference-equivalence labels are stored separately. Dispatch receives question, answer, fixed permitted reference only.',aggregation='Enumerate every eligible nonempty team under the explicit existing minimum-one informative contract. No fitting, oracle policy or selected probabilities. Raw comparison labels do not strengthen the cosine measurement contract.',history='Reuse frozen task-family history snapshots as an explicitly uncalibrated diagnostic scenario; no reliability updates. New wording and contrasts may be out of history distribution. Mixed tasks have no compatible history/policy and are blocked by the component-binding requirement.',attacks='No new attack study; primary dependency registry remains unchanged.',scope='No production router/allowlist changes; owned analyzer is opt-in only. No corpus edits, downloads, paid providers, policy fitting or inference beyond this fixed roster.',prior_artifact_hashes=preserved,source_hashes={str(p.resolve()):sha(p) for p in [source/'adapter.json',source/'corpus.json',source/'sources/countries.json']}))
    print('Prepared 12 fixed groups / 24 examples / <=96 attempts / <=120 generations',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('artifacts/capability-probes-v1'));a=p.parse_args();prepare(a.source,a.output)
