import json
from scripts.capture_reconciliation_target import collect


def test_capture_does_not_import_app_or_emit_configuration_secrets(tmp_path,monkeypatch):
    from scripts import capture_reconciliation_target as capture
    config=tmp_path/'adapter.json'
    config.write_text(json.dumps(dict(ollama_url='http://alice:password@localhost:11434/api/generate',
        api_key='secret-value',embedding_snapshot=None,nli_snapshot=None)))
    def git(args,**kwargs):
        if args[-3:]==['remote','get-url','origin']:return 'https://token-secret@github.com/owner/repo.git'
        return 'metadata'
    monkeypatch.setattr(capture.subprocess,'check_output',git)
    monkeypatch.setattr(capture.urllib.request,'build_opener',lambda *args: (_ for _ in ()).throw(AssertionError('no HTTP')))
    result=collect(tmp_path,config,metadata=True)
    text=json.dumps(result)
    assert 'password' not in text and 'secret-value' not in text and 'token-secret' not in text
    assert result['native_attempts']==result['confidence_generations']==0
    assert result['source_hashes']['app/game/execution.py'] is None
