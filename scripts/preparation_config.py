"""Explicit structural adapter inputs for offline preparation; no resource access."""
import json
from pathlib import Path
from pydantic import ValidationError
from app.benchmark.project_adapter import AdapterConfiguration
from app.game.offline.calibration import read_json

def preparation_adapter(path,output_root):
    """Validate before any output write; never discover a local draft or resources.

    All existing contract fields must be explicit, including fields with defaults,
    so preparation cannot silently choose new sampling or execution settings.
    Nullable resource locations remain nullable; only later resource preflight can
    attest readiness. The new study's four output locations are intentionally bound
    to output_root, exactly as the preparation workflow has always specified.
    """
    if path is None:
        raise ValueError('prepare requires --adapter-config PATH to an explicit project_collection_adapter_v1 JSON configuration')
    try:
        data=read_json(Path(path))
    except (OSError,ValueError,TypeError) as exc:
        raise ValueError(f'cannot read --adapter-config {path}: {exc}; provide an existing valid JSON configuration') from exc
    if not isinstance(data,dict):raise ValueError('--adapter-config must contain a JSON object')
    missing=sorted(set(AdapterConfiguration.model_fields)-set(data))
    if missing:raise ValueError('--adapter-config must specify all adapter fields explicitly; missing: '+', '.join(missing))
    try:
        config=AdapterConfiguration.model_validate(data)
        root=Path(output_root)
        return AdapterConfiguration.model_validate({**config.model_dump(mode='json'),
            'corpus_path':str(root/'corpus.json'),'index_dir':str(root/'index-v2'),
            'index_receipt':str(root/'index-receipt.json'),'service_observation':str(root/'service-observation.json')})
    except ValidationError as exc:
        issues=exc.errors(include_input=False,include_context=False,include_url=False)
        raise ValueError('invalid --adapter-config (project_collection_adapter_v1): '+json.dumps(issues)+'; correct the listed fields') from exc
