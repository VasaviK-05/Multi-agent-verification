"""Readiness/schema only: deliberately no scoring, fitting, or collection command."""
import argparse
import json
from pathlib import Path
import subprocess

from app.game.research.__main__ import _object, _nonfinite
from app.game.research.experiment1.manifest import ExperimentManifest, readiness, source_fingerprint


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('readiness', 'schema'))
    parser.add_argument('manifest', type=Path, nargs='?')
    args = parser.parse_args(argv)
    if args.command == 'schema':
        print(json.dumps(ExperimentManifest.model_json_schema(), indent=2, sort_keys=True))
        return 0
    if args.manifest is None:
        parser.error('readiness requires a manifest')
    root = Path(__file__).resolve().parents[4]
    try:
        payload = json.loads(args.manifest.read_text(encoding='utf-8'), object_pairs_hook=_object, parse_constant=_nonfinite)
        manifest = ExperimentManifest.model_validate(payload)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        result = readiness(manifest, actual_commit=commit, actual_source_fingerprint=source_fingerprint(root), source_root=root)
    except (OSError, ValueError) as exc:
        result = dict(ready=False, blockers=[str(exc)], final_payloads_read=False)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result['ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
