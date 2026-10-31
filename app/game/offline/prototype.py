"""Load/validate a packaged prototype without models, inference or activation."""
import argparse
import json
from app.game.prototype_bundle import load_prototype

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate'])
    parser.add_argument('--bundle',required=True)
    args=parser.parse_args(argv)
    try:
        loaded=load_prototype(args.bundle)
    except (ValueError,OSError) as exc:
        print(json.dumps(dict(valid=False,errors=[str(exc)],activated=False)));return 2
    print(json.dumps(dict(valid=True,bundle_id=loaded.manifest.bundle_id,artifacts=[a.artifact_id for a in loaded.artifacts],
        tasks=[e.task for e in loaded.manifest.entries],resource_check='expectations only; no live observation',activated=False),indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
