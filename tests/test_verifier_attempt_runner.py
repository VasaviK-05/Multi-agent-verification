import json

import pytest

from app.game.offline.calibration import MeasurementSetup
from app.game.offline.records import Attempt
from app.game.resource_provenance import ResourceFingerprint, ResourceManifest, VerifierResources
from app.models.schemas import VerificationResult
from evaluation.data_preparation import run_verifier_attempts as runner


def setup():
    rows = []
    kinds = {
        "semantic": ("implementation", "configuration", "model"),
        "evidence": ("implementation", "configuration", "model", "corpus", "index"),
        "rule": ("implementation", "configuration"),
        "confidence": ("implementation", "configuration", "model", "prompt", "service"),
    }
    for name, required in kinds.items():
        resources = tuple(ResourceFingerprint(resource_id=f"{name}_{kind}", kind=kind, sha256="a" * 64)
                          for kind in required)
        rows.append(VerifierResources(verifier_name=name, resources=resources))
    manifest = ResourceManifest(verifiers=tuple(rows))
    return MeasurementSetup(resources=manifest, environment={"os": "test"}, dependency_versions={"pydantic": "test"},
                            code_revision="b" * 40, application_source_digest="c" * 64, evidence_kind="empirical")


class FakeVerifier:
    def __init__(self, name, seen):
        self.name, self.seen = name, seen

    def verify(self, question, answer, context=None):
        self.seen.append((question, answer, context))
        return VerificationResult(verifier_name=self.name, score=.75, passed=True,
                                 metadata={"decision": "SUPPORT", "score_meaning": "test"})


def make_prepared(directory):
    directory.mkdir()
    row = {"candidate_id": "candidate_1", "dataset_id": "source_1", "question_id": "GSM8K:source_1",
           "related_group_id": "group_1", "partition": "history", "benchmark": "GSM8K",
           "verifier_input": {"benchmark": "GSM8K", "question": "2+2?", "candidate_answer": "4",
                              "evidence_context": []},
           "gold_answer": "secret", "label_provenance": {"trace": "secret"}}
    (directory / "history_prepared.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    (directory / "development_prepared.jsonl").write_text("", encoding="utf-8")
    unresolved = {"candidate_id": "candidate_2", "dataset_id": "source_2", "related_group_id": "group_2",
                  "partition": "development", "benchmark": "GSM8K", "correctness_status": "unresolved"}
    (directory / "excluded_unresolved.jsonl").write_text(json.dumps(unresolved) + "\n", encoding="utf-8")


def test_attempt_schema_and_input_boundary(tmp_path):
    row = {"candidate_id": "candidate_1", "dataset_id": "source_1", "question_id": "GSM8K:source_1",
           "related_group_id": "group_1", "partition": "history", "benchmark": "GSM8K",
           "verifier_input": {"question": "q", "candidate_answer": "a", "context": None},
           "verifier_input_sha256": "d" * 64}
    seen = []
    semantic_resources = next(r for r in setup().resources.verifiers if r.verifier_name == "semantic")
    result = runner.record_one(row, FakeVerifier("semantic", seen),
                               semantic_resources, setup().resources.manifest_id)
    attempt = Attempt.model_validate(result["attempt"])
    assert attempt.state == "directional"
    assert attempt.report.verifier_name == "semantic"
    assert seen == [("q", "a", None)]
    assert "secret" not in attempt.report_provenance
    assert result["duration_ms"] >= 0


def test_roster_ignores_labels_and_preserves_unresolved(tmp_path):
    make_prepared(tmp_path / "prepared")
    rows, unresolved = runner.load_roster(tmp_path / "prepared")
    assert len(rows) == 1 and len(unresolved) == 1
    assert "gold_answer" not in rows[0]
    assert unresolved[0]["correctness_status"] == "unresolved"
    assert unresolved[0]["disposition"] == "not_attempted_no_prepared_verifier_input"


def test_structured_context_passes_text_but_not_provenance():
    row = {"verifier_input": {"benchmark": "HotpotQA", "question": "q", "candidate_answer": "a",
                              "evidence_context": [{"title": "Page", "text": "Evidence sentence",
                                                    "source_path": "private/source.json"}]}}
    assert runner.permitted_input(row) == ("HotpotQA", "q", "Page\nEvidence sentence")


def test_history_development_group_leakage_is_rejected(tmp_path):
    prepared = tmp_path / "prepared"
    make_prepared(prepared)
    row = json.loads((prepared / "history_prepared.jsonl").read_text(encoding="utf-8"))
    row.update(candidate_id="candidate_dev", dataset_id="source_dev", question_id="GSM8K:source_dev",
               partition="development")
    (prepared / "development_prepared.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="group leakage"):
        runner.load_roster(prepared)


def test_unavailable_verifier_is_not_fabricated_as_report():
    from app.selection.models import VerifierUnavailable

    class OfflineVerifier:
        name = "semantic"
        def verify(self, *args):
            raise VerifierUnavailable("dependency unavailable")

    row = {"candidate_id": "candidate_1", "dataset_id": "source_1", "question_id": "GSM8K:source_1",
           "related_group_id": "group_1", "partition": "history", "benchmark": "GSM8K",
           "verifier_input": {"question": "q", "candidate_answer": "a", "context": None},
           "verifier_input_sha256": "d" * 64}
    semantic_resources = next(r for r in setup().resources.verifiers if r.verifier_name == "semantic")
    stored = runner.record_one(row, OfflineVerifier(), semantic_resources, setup().resources.manifest_id)
    checked = Attempt.model_validate(stored["attempt"])
    assert checked.state == "unavailable"
    assert checked.report is None


def test_run_resume_records_once_and_validates_manifest(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    prepared = tmp_path / "prepared"
    make_prepared(prepared)
    config_path = tmp_path / "adapter.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("VERIFIER_COLLECTION_ADAPTER_CONFIG", str(config_path))
    observed = setup()
    seen = []
    adapter = SimpleNamespace(AdapterConfiguration=SimpleNamespace(model_validate=lambda x: x),
                              read_json=lambda p: {}, inspect_setup=lambda c: {"ready": True},
                              create_verifiers=lambda: ([FakeVerifier(n, seen) for n in runner.VERIFIERS], observed))
    monkeypatch.setitem(sys.modules, "app.benchmark.project_adapter", adapter)
    output = tmp_path / "output"
    first = runner.run(prepared, output)
    assert first["recorded_attempts"] == 4
    assert first["unresolved_not_attempted"] == 1
    assert len(seen) == 4
    second = runner.run(prepared, output, resume=True)
    assert second["recorded_attempts"] == 4
    assert len(seen) == 4
    assert runner.validate_output(output, prepared)["pending_attempts"] == 0
    with pytest.raises(ValueError, match="resume refused"):
        source_row = json.loads((prepared / "history_prepared.jsonl").read_text(encoding="utf-8"))
        source_row["verifier_input"]["question"] = "changed question"
        (prepared / "history_prepared.jsonl").write_text(json.dumps(source_row) + "\n", encoding="utf-8")
        runner.run(prepared, output, resume=True)
