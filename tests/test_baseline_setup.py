"""Offline-mode API regression checks; no models, verifiers or service access."""
import socket
from unittest.mock import Mock

import pytest

from app.benchmark import baseline_setup, project_adapter
from app.selection import baseline_resources


@pytest.fixture
def observer_boundary(tmp_path, monkeypatch):
    import requests
    from huggingface_hub import constants

    def forbidden(*args, **kwargs):
        raise AssertionError("external access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    for key in ("TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(constants, "HF_HUB_OFFLINE", True)
    monkeypatch.setattr(constants, "HF_HUB_CACHE", str(tmp_path / "cache"))
    refs = tmp_path / "cache/models--sentence-transformers--all-MiniLM-L6-v2/refs"
    refs.mkdir(parents=True)
    (refs / "main").write_text("a" * 40, encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    service = tmp_path / "service.json"
    receipt.touch()
    service.touch()
    monkeypatch.setattr(baseline_resources, "resolve_baseline_evidence_resources",
                        lambda _: (tmp_path / "corpus", tmp_path / "index", None))
    # A sentinel ends the check immediately after offline-mode validation.
    # No model is loaded and the rest of the observer cannot contact services.
    digest = Mock(side_effect=RuntimeError("offline checks passed"))
    live = Mock(side_effect=forbidden)
    monkeypatch.setattr(project_adapter, "directory_digest", digest)
    monkeypatch.setattr(project_adapter, "observe_service", live)
    yield lambda: baseline_setup.observe_baseline_setup(
        index_receipt_path=receipt, service_observation_path=service), digest
    live.assert_not_called()


def test_installed_transformers_uses_public_hub_offline_api():
    from huggingface_hub import is_offline_mode
    from transformers.utils import hub

    assert hub.is_offline_mode is is_offline_mode


def test_offline_observer_accepts_installed_api(observer_boundary):
    observe, digest = observer_boundary
    with pytest.raises(RuntimeError, match="^offline checks passed$"):
        observe()
    digest.assert_called_once()


@pytest.mark.parametrize("flag", ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"])
@pytest.mark.parametrize("value", [None, "0"])
def test_both_explicit_offline_flags_remain_required(observer_boundary, monkeypatch, flag, value):
    if value is None:
        monkeypatch.delenv(flag)
    else:
        monkeypatch.setenv(flag, value)
    observe, digest = observer_boundary
    with pytest.raises(ValueError, match="^baseline_model_resolution_must_be_offline_and_frozen$"):
        observe()
    digest.assert_not_called()


def test_flags_set_after_library_import_do_not_certify_offline_mode(observer_boundary, monkeypatch):
    from huggingface_hub import constants

    monkeypatch.setattr(constants, "HF_HUB_OFFLINE", False)
    observe, digest = observer_boundary
    with pytest.raises(ValueError, match="^baseline_offline_settings_were_not_captured_before_import$"):
        observe()
    digest.assert_not_called()


@pytest.mark.parametrize("override", ["TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"])
def test_unreviewed_cache_override_remains_rejected(observer_boundary, monkeypatch, override):
    monkeypatch.setenv(override, "unreviewed-cache")
    observe, digest = observer_boundary
    with pytest.raises(ValueError, match="^baseline_cache_override_requires_review$"):
        observe()
    digest.assert_not_called()
