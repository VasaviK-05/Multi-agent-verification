"""Run the proposal helper with executable no-final-payload/no-fitting guards."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
directory=Path(__file__).resolve().parent
protected=(directory/'custody/final-examples.jsonl').resolve()
def guard(event,args):
    if event=='open' and isinstance(args[0],str) and Path(args[0]).resolve()==protected:
        raise AssertionError('proposal attempted to open reserved final labels')
sys.addaudithook(guard)
with patch('app.game.solver.linprog',side_effect=AssertionError('proposal attempted fitting')):
    from app.game.offline.pilot_proposal import propose
    result=propose(directory)
print(json.dumps(result,indent=2))
(directory/'proposal-isolation-check.json').write_text(json.dumps(dict(
    final_payload_access_guard='passed',optimizer_call_guard='passed',policy_created=False,
    result=result),indent=2),encoding='utf-8')
