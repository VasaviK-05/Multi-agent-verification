"""Temporary synthetic adapter configuration; no resources or credentials read."""
import json

def synthetic_adapter_file(tmp_path):
    data=dict(version='project_collection_adapter_v1',embedding_snapshot=None,nli_snapshot=None,
        corpus_path='SYNTHETIC/corpus.json',index_dir='SYNTHETIC/index',index_receipt=None,service_observation=None,
        ollama_url='http://localhost:11434/api/generate',ollama_model='SYNTHETIC-not-a-real-model',
        n_samples=3,temperature=.6,timeout=12.,chunk_size=128,device='cpu')
    path=tmp_path/'synthetic-adapter.json';path.write_text(json.dumps(data),encoding='utf-8')
    return path,data
