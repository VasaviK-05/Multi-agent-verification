import json
from pathlib import Path

import scripts.verify_real_evidence_pipeline as diagnostic


class ReconfigurableStream:
    def __init__(self):
        self.settings = None

    def reconfigure(self, **kwargs):
        self.settings = kwargs


def test_diagnostic_streams_are_configured_for_strict_utf8(monkeypatch):
    stdout = ReconfigurableStream()
    stderr = ReconfigurableStream()
    monkeypatch.setattr(diagnostic.sys, "stdout", stdout)
    monkeypatch.setattr(diagnostic.sys, "stderr", stderr)

    diagnostic.configure_utf8()

    assert stdout.settings == {"encoding": "utf-8", "errors": "strict"}
    assert stderr.settings == {"encoding": "utf-8", "errors": "strict"}


def test_diagnostic_json_log_preserves_unicode(tmp_path):
    output = tmp_path / "diagnostic.json"

    diagnostic._write_json_log(output, {"passage": "Łódź"})

    assert json.loads(output.read_text(encoding="utf-8")) == {"passage": "Łódź"}
    assert "Łódź".encode("utf-8") in output.read_bytes()


def test_diagnostic_returns_failure_exit_code_for_real_exception(monkeypatch):
    monkeypatch.setattr(diagnostic, "configure_utf8", lambda: None)
    monkeypatch.setattr(
        diagnostic,
        "run_diagnostic",
        lambda args: (_ for _ in ()).throw(RuntimeError("diagnostic failed")),
    )

    assert diagnostic.main([]) == 1


def test_fresh_index_validation_rejects_non_temporary_index(tmp_path):
    class Retriever:
        index_dir = Path("data/evidence_index/articles_13083")

    temp_root = tmp_path / "temporary"
    temp_root.mkdir()

    try:
        diagnostic._validate_fresh_index(
            Retriever(),
            Retriever.index_dir,
            temp_root,
        )
    except AssertionError as exc:
        assert "temporary directory" in str(exc)
    else:
        raise AssertionError("production-like index path was accepted")
