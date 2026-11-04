"""Portable stdlib-only target capture; no imports from the target application."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

FIELDS = {'version','embedding_snapshot','nli_snapshot','corpus_path','index_dir','index_receipt',
    'service_observation','resource_relocation_binding','ollama_url','ollama_model','n_samples',
    'temperature','timeout','chunk_size','device'}
SOURCES = ['app/benchmark/project_adapter.py','app/models/schemas.py',
    'app/verifiers/base_verifier.py','app/verifiers/claim_generator.py','app/verifiers/evidence_retriever.py',
    'app/verifiers/evidence_verifier.py','app/verifiers/rule_verifier.py','app/verifiers/semantic_verifier.py',
    'app/verifiers/confidence_verifier.py','app/verifiers/self_consistency.py',
    'app/game/offline/recording_adapters.py','app/game/offline/resource_relocation.py',
    'app/game/execution.py','app/game/component_execution.py','app/game/question_routing.py',
    'app/game/offline/reconciled_resources.py','app/game/offline/reference_compatibility.py',
    'app/game/offline/singleton_compatibility.py',
    'app/selection/verifier_selector.py','app/selection/capabilities.py',
    'app/services/validation_service.py','app/orchestration/validation_orchestrator.py']


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def collect(target,configuration,metadata=False):
    target=Path(target).resolve()
    def git(*args):return subprocess.check_output(['git','-C',str(target),*args],text=True).rstrip('\r\n')
    raw=json.loads(Path(configuration).read_text(encoding='utf-8-sig'))
    config={k:v for k,v in raw.items() if k in FIELDS}
    url=urllib.parse.urlsplit(config.get('ollama_url',''))
    valid_url=(url.scheme=='http' and url.hostname in {'localhost','127.0.0.1','::1'} and
        not url.username and not url.password and not url.query and not url.fragment and url.path=='/api/generate')
    if not valid_url and 'ollama_url' in config:config['ollama_url']='omitted: not credential-free loopback /api/generate'
    remote=urllib.parse.urlsplit(git('remote','get-url','origin'))
    result=dict(version='reconciliation_target_capture_v1',target=str(target),head=git('rev-parse','HEAD'),
        branch=git('branch','--show-current'),remote=urllib.parse.urlunsplit((remote.scheme,remote.netloc.rsplit('@',1)[-1],remote.path,'','')),
        dirty=git('status','--porcelain=v1'),configuration=config,
        boundary='declared configuration and files only; actual running objects/settings not attested',
        native_attempts=0,confidence_generations=0,source_hashes={},resource_hashes={})
    for p in SOURCES:result['source_hashes'][p]=sha(target/p) if (target/p).is_file() else None
    def local(value):
        p=Path(value);return p if p.is_absolute() else target/p
    for name in ('embedding_snapshot','nli_snapshot'):
        directory=local(config[name]) if config.get(name) else None
        result['resource_hashes'][name]=[dict(path=p.relative_to(directory).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
            for p in sorted(directory.rglob('*')) if p.is_file()] if directory and directory.is_dir() else None
    for name in ('corpus_path','index_receipt','service_observation','resource_relocation_binding'):
        p=local(config[name]) if config.get(name) else None
        result['resource_hashes'][name]=sha(p) if p and p.is_file() else None
    directory=local(config['index_dir']) if config.get('index_dir') else None
    for name in ('faiss.index','chunks.json','manifest.json'):
        p=directory/name if directory else None
        result['resource_hashes'][name]=sha(p) if p and p.is_file() else None
    result['service_metadata']={}
    if metadata and valid_url:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base=raw['ollama_url'].rsplit('/api/generate',1)[0]
        for endpoint in ('version','tags'):
            try:
                with opener.open(base+'/api/'+endpoint,timeout=5) as response:value=json.load(response)
                if endpoint=='tags':
                    value={'models':[{'name':v.get('name'),'digest':v.get('digest')}
                        for v in value.get('models',[]) if v.get('name')==config.get('ollama_model')]}
                else:value={'version':value.get('version')}
                result['service_metadata'][endpoint]=value
            except Exception as exc:result['service_metadata'][endpoint]={'error_type':type(exc).__name__}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',type=Path,required=True)
    p.add_argument('--configuration',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--service-metadata',action='store_true')
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('use a fresh output path')
    result=collect(a.target,a.configuration,a.service_metadata)
    with a.output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print('CAPTURED',a.output,'zero verifier/generation calls')


if __name__=='__main__':main()
