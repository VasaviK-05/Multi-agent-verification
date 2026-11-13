"""Offline benchmark for the adaptive validation pipeline."""

from importlib import import_module

__all__ = [
    "BenchmarkReport",
    "LabeledExample",
    "examples_from_records",
    "load_labeled_jsonl",
    "run_benchmark",
]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(".offline_benchmark", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
