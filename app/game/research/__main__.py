"""Read-only readiness CLI. Deliberately has no scoring/fitting subcommands."""

import argparse
import json
from pathlib import Path
import subprocess

from pydantic import ValidationError

from app.game.models import content_id
from app.game.research.readiness import check_readiness
from app.game.research.specification import ExperimentSpecification


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError(f"nonfinite JSON number: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a recorded game study without replay, fitting or test scoring")
    parser.add_argument("command", choices=("readiness",))
    parser.add_argument("specification", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[3]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=root, text=True)
    # Include uncommitted harness bytes, which are not represented by HEAD.
    source_id = content_id([(str(p.relative_to(root)).replace("\\", "/"), p.read_text(encoding="utf-8"))
                           for p in sorted((root / "app" / "game" / "research").glob("*.py"))])
    payload_id = None
    try:
        payload = json.loads(args.specification.read_text(encoding="utf-8"), object_pairs_hook=_object, parse_constant=_nonfinite)
        payload_id = content_id(payload)
        spec = ExperimentSpecification.model_validate(payload)
        result = check_readiness(spec, actual_code_revision=revision).model_dump(mode="json")
    except ValidationError as exc:
        result = {"ready": False, "blockers": [{"location": list(e["loc"]), "message": e["msg"]}
                                               for e in exc.errors(include_url=False)]}
    except (OSError, ValueError) as exc:
        result = {"ready": False, "blockers": [str(exc)]}
    result.update(command="readiness_only", input_digest=payload_id, code_revision=revision,
                  working_tree_clean=not bool(status), research_source_digest=source_id)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
