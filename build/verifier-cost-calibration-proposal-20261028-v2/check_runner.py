"""Synthetic network-limit checks only; no network or verifier calls."""
import io
from pathlib import Path
import runpy
from types import SimpleNamespace

code = runpy.run_path(str(Path(__file__).with_name('execute_authorized.py')),run_name='runner_test')
guard = code['NetworkGuard']('http://localhost:11434/api/generate',io.StringIO())
calls = []
def fake(session,method,url,*a,**kw):
    calls.append((method,url))
    return SimpleNamespace(status_code=200)
for _ in range(430):
    assert guard.call(fake,None,'POST','http://localhost:11434/api/generate').status_code == 200
for _ in range(4):
    guard.call(fake,None,'GET','http://localhost:11434/api/version')
for method,url in [('POST','http://localhost:11434/api/generate'),
                   ('GET','http://localhost:11434/api/tags'),('GET','https://example.com')]:
    try:
        guard.call(fake,None,method,url)
    except RuntimeError:
        pass
    else:
        raise AssertionError('limit/endpoint violation accepted')
assert len(calls) == 434
assert guard.counts == dict(generation=430,metadata=4,blocked=3)
print('Synthetic guard checks passed; zero actual requests')
