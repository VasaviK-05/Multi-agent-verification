"""Authenticated metadata readiness/schema only. No scoring/fit/collection command."""
import argparse
import json
from pathlib import Path
import subprocess

from app.game.research.experiment1.manifest import source_fingerprint
from .models import Manifest, Authorizations, load_authenticated
from .readiness import readiness


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('schema', 'readiness'))
    parser.add_argument('manifest', nargs='?', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--authorizations', type=Path)
    parser.add_argument('--authorization-sha256')
    args = parser.parse_args(argv)
    if args.command == 'schema':
        print(json.dumps(Manifest.model_json_schema(), indent=2, sort_keys=True))
        return 0
    if args.manifest is None or not args.sha256:
        parser.error('readiness requires a manifest and its caller-trusted --sha256')
    root = Path(__file__).resolve().parents[5]
    try:
        manifest = load_authenticated(args.manifest, args.sha256)
        if args.authorizations and not args.authorization_sha256:
            raise ValueError('authorizations require a separately trusted SHA-256')
        auth = load_authenticated(args.authorizations, args.authorization_sha256, Authorizations) if args.authorizations else Authorizations()
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        result = readiness(manifest, actual_commit=commit,
            actual_source_fingerprint=source_fingerprint(root), authorizations=auth)
    except (OSError, ValueError) as exc:
        result = dict(stages={}, blockers=[str(exc)], final_payloads_read=False,
                      inference_calls=0, optimization_calls=0)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result.get('stages', {}).get('final_test_scoring', {}).get('ready') else 2


if __name__ == '__main__':
    raise SystemExit(main())
