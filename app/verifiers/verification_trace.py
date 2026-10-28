"""Runtime tracing for the current EvidenceVerifier; does not alter its logic."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


def safe(value: Any):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [safe(v) for v in value]
    if hasattr(value, "model_dump"):
        try: return safe(value.model_dump())
        except Exception: pass
    if hasattr(value, "dict") and callable(value.dict):
        try: return safe(value.dict())
        except Exception: pass
    return repr(value)


class EvidenceVerifierTracer:
    """Wrap existing verifier methods and save each stage's input/output."""
    def __init__(self, verifier, case_id: str, question: str, answer: str,
                 output_dir="data/verification_traces"):
        self.verifier, self.case_id = verifier, case_id
        self.question, self.answer = question, answer
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.originals = []
        self.trace = {
            "case_id": case_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "question": question, "answer": answer,
            "config": {k: getattr(verifier, k, None) for k in (
                "top_k", "min_retrieval_score", "retrieval_margin", "min_nli_score",
                "min_topic_coverage", "topic_margin", "max_premise_windows")},
            "corpus_version": getattr(verifier.retriever, "corpus_version", None),
            "index_version": getattr(verifier.retriever, "index_version", None),
            "nli_model": getattr(verifier, "NLI_MODEL", None),
            "events": [], "final_result": None, "error": None,
        }
        self.seq = 0

    def event(self, stage, **data):
        self.seq += 1
        self.trace["events"].append({"sequence": self.seq, "stage": stage,
            "time_utc": datetime.now(timezone.utc).isoformat(), "data": safe(data)})

    def wrap(self, obj, method, stage, input_fn=None, output_fn=None):
        original = getattr(obj, method)
        self.originals.append((obj, method, original))
        def wrapped(*args, **kwargs):
            call_no = sum(e["stage"] == stage + ".input" for e in self.trace["events"]) + 1
            call_id = f"{stage}-{call_no}"
            if input_fn:
                self.event(stage + ".input", call_id=call_id, **input_fn(args, kwargs))
            started = perf_counter()
            try:
                result = original(*args, **kwargs)
            except Exception as exc:
                self.event(stage + ".error", call_id=call_id, error=repr(exc))
                raise
            payload = output_fn(result) if output_fn else {"result": result}
            self.event(stage + ".output", call_id=call_id,
                       elapsed_ms=round((perf_counter()-started)*1000, 2), **payload)
            return result
        setattr(obj, method, wrapped)

    def install(self):
        r, v = self.verifier.retriever, self.verifier
        self.wrap(r, "retrieve", "retrieval",
            lambda a,k: {"query": a[0] if a else k.get("query"),
                         "k": k.get("k", a[1] if len(a)>1 else None)},
            lambda out: {"count": len(out or []), "rows": out or []})
        methods = [
            (v, "select_relevant", "retrieval_gate"),
            (v, "select_on_topic", "topic_gate"),
            (v, "score_evidence", "nli_evaluation"),
            (v, "aggregate_chunks", "claim_aggregation"),
            (v, "aggregate_claims", "answer_aggregation"),
        ]
        for obj, method, stage in methods:
            if not hasattr(obj, method):
                continue
            self.wrap(obj, method, stage,
                lambda a,k: {"args": a, "kwargs": k},
                lambda out: {"result": out})
        return self

    def save(self):
        path = self.output_dir / f"{self.case_id}.json"
        path.write_text(json.dumps(self.trace, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return path

    def restore(self):
        for obj, method, original in reversed(self.originals):
            setattr(obj, method, original)
        self.originals.clear()

    def run(self, context=None):
        try:
            result = self.verifier.verify(self.question, self.answer, context=context)
            metadata = getattr(result, "metadata", None)
            self.trace["final_result"] = {
                "verifier_name": getattr(result, "verifier_name", None),
                "score": getattr(result, "score", None),
                "passed": getattr(result, "passed", None),
                "reasoning": getattr(result, "reasoning", None),
                "metadata": safe(metadata),
            }
            return result
        except Exception as exc:
            self.trace["error"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        finally:
            self.restore()
            self.save()
