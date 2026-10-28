"""Trace one case. Run from the repository root."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from app.verifiers.evidence_verifier import EvidenceVerifier
from app.verifiers.verification_trace import EvidenceVerifierTracer

parser = argparse.ArgumentParser()
parser.add_argument('--case-id', required=True)
parser.add_argument('--question', required=True)
parser.add_argument('--answer', required=True)
parser.add_argument('--corpus-path', default=None)
parser.add_argument('--output-dir', default='data/verification_traces')
a = parser.parse_args()
kwargs = {'corpus_path': a.corpus_path} if a.corpus_path else {}
verifier = EvidenceVerifier(**kwargs)
tracer = EvidenceVerifierTracer(verifier, a.case_id, a.question, a.answer, a.output_dir).install()
result = tracer.run()
metadata = getattr(result, 'metadata', {}) or {}
print(json.dumps({'case_id': a.case_id, 'decision': metadata.get('decision'),
                  'passed': getattr(result, 'passed', None), 'score': getattr(result, 'score', None),
                  'trace_file': str(Path(a.output_dir) / f'{a.case_id}.json')}, indent=2))
