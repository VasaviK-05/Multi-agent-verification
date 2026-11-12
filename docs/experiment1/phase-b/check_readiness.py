"""Run only the existing readiness CLI for the assembled candidate manifests."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent


def main():
    plan=json.loads((OUT/'readiness-inputs.json').read_text())
    results=[]
    for name in plan['candidates']:
        command=[sys.executable,'-B','-m','app.game.research.experiment1','readiness',str((OUT/name).relative_to(ROOT))]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        if result.returncode not in (0,2):
            raise RuntimeError(result.stderr)
        report=json.loads(result.stdout)
        if not report.get('final_payloads_read') is False:
            raise AssertionError('unexpected final payload access')
        results.append(dict(candidate=name,command=command,exit_code=result.returncode,report=report))
    output=dict(version='experiment1_phase_b_readiness_results_v1',inventory_id=plan['inventory_id'],results=results)
    (OUT/'readiness-results.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({r['candidate']:dict(exit_code=r['exit_code'],ready=r['report']['ready'],
        blockers=r['report']['blockers']) for r in results},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
