"""Freeze the eight authorized examples and independent labels before execution."""
import hashlib
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    target=root/'artifacts/question-conditioned-components-v1'
    save=lambda name,value:(target/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if (target/'protocol.json').exists():raise ValueError('prepared smoke already exists; never overwrite or retry')
    examples=[];labels={}
    templates=(('area','Bahrain',765,10,' square kilometres'),('population','Belgium',11941781,1000,''))
    # Existing source facts, fixed before calls. Every variant of a fact remains one group.
    for measure,entity,base,increment,units in templates:
        reference=f'The {measure} of {entity} is {base}{units}.'
        question=f'What is the {measure} of {entity}, and what is that {measure} plus {increment}{units}? Give both values.'
        for variant,b,d in (('correct',base,base+increment),('wrong_math',base,base+increment-1),
                ('wrong_base',base+1,base+1+increment),('both_wrong',base+1,base+increment-1)):
            identity=f'{measure}-{variant}'
            examples.append(dict(example_id=identity,question=question,
                answer=json.dumps(dict(base=str(b),derived=str(d))),reference=reference))
            labels[identity]=dict(group_id=measure,base_correct=b==base,
                arithmetic_correct=d==b+increment,answer_is_correct=b==base and d==b+increment,
                source='Retained history-source corpus fact; independent integer addition',
                source_fact=reference,not_blinded=True)
    save('examples.json',examples);save('labels.json',labels)
    resources=json.loads((root/'artifacts/flexible-teams-v1/factual-minimum-1/contract.json').read_text())['resource_manifest']
    paths=[target/'examples.json',target/'labels.json',root/'app/game/component_binding.py',
        root/'scripts/collect_component_smoke.py',root/'scripts/prepare_component_smoke.py']
    save('protocol.json',dict(version='component_smoke_v1',execution_mode='diagnostic_no_policy',
        authorization='User attachment ac1c58b6: at most8 compound examples, Evidence+Rule only, at most16 attempts',
        max_examples=8,max_attempts=16,max_generations=0,retries=0,labels_used_for_fitting=False,
        expected_resources=resources,sealed_inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}))


if __name__=='__main__':main()
