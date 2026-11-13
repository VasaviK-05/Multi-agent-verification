"""Reproduce source-derived roster payloads into a NEW directory, never run a study.

Does not regenerate proposed scientific configuration, prose, calibration or live
compatibility attestations. Original Package B generator is retained in archive.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

MEMBERS=('manifest.json','audit.json','development_candidates.jsonl',
         'development_verifier_inputs.jsonl','history_candidates.jsonl',
         'unresolved_candidates.jsonl','skipped_groups.jsonl')


def generate(artifacts, output):
    if output.exists():raise FileExistsError('Refusing to overwrite '+str(output))
    archive=artifacts/'research_v1_exploratory_v1_source_package.zip'
    data={};hashes={}
    with zipfile.ZipFile(archive) as z:
        for name in MEMBERS:
            member=next(n for n in z.namelist() if n.replace('\\','/').split('/')[-1]==name)
            raw=z.read(member);hashes[name]=hashlib.sha256(raw).hexdigest()
            data[name]=[json.loads(l) for l in raw.decode().splitlines() if l] if name.endswith('.jsonl') else json.loads(raw)
    for name,expected in data['manifest.json']['output_sha256'].items():
        if name in hashes and hashes[name]!=expected:raise ValueError('Source member digest mismatch: '+name)
    rows=data['development_candidates.jsonl'];history=data['history_candidates.jsonl']
    fields=('candidate_id','source_candidate_id','question_id','related_group_id','split_identity','benchmark',
            'question','candidate_answer','content_identity','label_class','label_protocol','label_method',
            'label_source','label_provenance','answer_is_correct','human_verified','human_review_record')
    roster=[{**{k:r.get(k) for k in fields},'example_id':r['candidate_id'],'approval':'PENDING',
             'reference_available_in_source':bool(r['evidence_context']),'reference_serialization':None,
             'independent_label_accepted':False} for r in rows]
    summary={split:{'examples':len(rs),'groups':len({r['related_group_id'] for r in rs}),
        'by_benchmark':{b:{'examples':sum(r['benchmark']==b for r in rs),
                          'groups':len({r['related_group_id'] for r in rs if r['benchmark']==b})}
                        for b in sorted({r['benchmark'] for r in rs})}} for split,rs in [('history',history),('development',rows)]}
    payloads={'development-scope.json':{'status':'PROPOSED_NOT_APPROVED','dataset_version':data['manifest.json']['dataset_version'],
       'summary':summary,'approved_examples':[],'eligible_source_candidates_pending_approval':roster,
       'excluded_unresolved_candidates':data['unresolved_candidates.jsonl'],'excluded_skipped_groups':data['skipped_groups.jsonl'],
       'source_manifest':data['manifest.json'],'source_audit':data['audit.json'],'final_test_payload_opened':False},
       'development-verifier-inputs.source.json':data['development_verifier_inputs.jsonl'],
       'history-source-roster.json':{'status':'SOURCE_ONLY_NOT_APPROVED_HISTORY_RECORDINGS','examples':history},
       'source-derivation.json':{'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'opened_members':hashes,
                               'source_tuples_transformed':False}}
    output.mkdir(parents=True)
    for name,value in payloads.items():(output/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    print(generate(args.artifacts_dir,args.output_dir))
