"""Offline tests only: real frozen registration/source bytes, no inference or DB."""
from dataclasses import replace
from decimal import Decimal, localcontext
import hashlib
import json
import shutil
from types import SimpleNamespace

import pytest
import requests

from app.game.component_execution import bind_contract
from app.services import compound_generation as generation

QUESTION = "What is the population of Cameroon, and what is that population plus 1000? Give both values."
PROSE = "Cameroon's population (2020): approximately 26,503,000\n\nCameroon's population + 1000: approximately 26,503,001"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Unit tests must not contact services")
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


@pytest.fixture(scope="module")
def spec():
    return generation.resolve_registered_compound(QUESTION)


@pytest.fixture(scope="module")
def sources(spec):
    return generation._load_sources(spec.catalog)


@pytest.fixture
def archive(tmp_path, monkeypatch):
    destination = tmp_path / "archive"
    shutil.copytree(generation._ARCHIVE, destination)
    monkeypatch.setattr(generation, "_ARCHIVE", destination)
    return destination


def test_exact_registration_and_plan(spec):
    assert spec.question == QUESTION
    assert spec.plan.entity == "Cameroon" and spec.plan.measure == "population"
    assert spec.plan.increment == "1000"
    assert spec.policy.policy_id == "0192b98e50ab5dcbd40ca78a0d4a3ec3978dfe8086edcb615802c21024c83532"


@pytest.mark.parametrize("question", [QUESTION + " ", QUESTION.replace("1000", "1001"),
    QUESTION.replace("Give both values.", "Give both numbers."), QUESTION.replace("Cameroon", "Atlantis"),
    QUESTION.replace("plus", "times")])
def test_altered_compound_rejected(question):
    with pytest.raises(generation.UnsupportedRegistrationError):
        generation.generate_compound_answer(question)


@pytest.mark.parametrize("question", ["What is the capital of France?", "Explain quantum gravity."])
def test_ordinary_question_is_not_handled(question):
    assert generation.generate_compound_answer(question) is None


def test_catalog_and_source_identity(spec, sources):
    assert sources.catalog == spec.catalog
    assert sources.manifest_id == spec.catalog.source_manifest_id


def test_changed_catalog_identity_rejected(spec):
    bad = spec.catalog.model_copy(update={"source_manifest_id": "0" * 64})
    with pytest.raises(generation.SourceIntegrityError):
        generation._load_sources(bad)


@pytest.mark.parametrize("name", ["manifest.json", "corpus.json", "geonames-countryInfo.txt", "countries.json"])
def test_missing_source_fails_without_fallback(archive, name):
    (archive / name).unlink()
    with pytest.raises(generation.SourceUnavailableError) as error:
        generation.generate_compound_answer(QUESTION)
    assert str(archive) not in str(error.value)


def test_modified_bytes_rejected(archive):
    file = archive / "corpus.json"
    file.write_bytes(file.read_bytes() + b" ")
    with pytest.raises(generation.SourceIntegrityError):
        generation.generate_compound_answer(QUESTION)


def test_modified_bytes_and_rewritten_local_receipt_still_rejected(archive):
    file = archive / "corpus.json"
    file.write_bytes(file.read_bytes() + b" ")
    receipt = json.loads((archive / "manifest.json").read_bytes())
    receipt["files"]["corpus.json"].update(sha256=hashlib.sha256(file.read_bytes()).hexdigest(), bytes=file.stat().st_size)
    (archive / "manifest.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(generation.SourceIntegrityError):
        generation.generate_compound_answer(QUESTION)


@pytest.mark.parametrize("count", [0, 2])
def test_missing_or_ambiguous_fact(spec, sources, count):
    fact = generation._find_fact(spec, sources)
    with pytest.raises(generation.FactLookupError):
        generation._find_fact(spec, SimpleNamespace(facts=(fact,) * count))


def test_generation_structure_provenance_and_unchanged_binder(spec, sources):
    result = generation.generate_compound_answer(QUESTION)
    assert result.answer == '{"base":"29879337","derived":"29880337"}'
    fields = json.loads(result.answer)
    assert set(fields) == {"base", "derived"} and all(type(v) is str for v in fields.values())
    assert result.source_manifest_id == sources.manifest_id
    assert result.contract_id == spec.policy.contract.compatibility_id
    assert result.descriptor == generation._find_fact(spec, sources).descriptor
    assert result.source_verified and result.arithmetic_validated and result.binder_accepted
    assert result.generation_method == "source_grounded_deterministic_v1"
    assert result.source_scope == "approved_frozen_snapshot"
    assert len(result.source_hashes) == 3
    plan, components, _ = bind_contract(spec.policy.contract, QUESTION, result.answer, None)
    assert plan == spec.plan and components[1].answer == fields["derived"]


def test_other_registered_entities_use_their_own_source_values():
    configuration, _, _ = generation.load_bundle()
    router = configuration.router()
    results = []
    for question in sorted(configuration.allowlist):
        if router.resolve(question, None)[0] != "component":
            continue
        item = generation.resolve_registered_compound(question)
        fact = generation._find_fact(item, generation._load_sources(item.catalog))
        result = generation.generate_compound_answer(question)
        fields = json.loads(result.answer)
        assert Decimal(fields["base"]) == Decimal(fact.value)
        assert Decimal(fields["derived"]) == Decimal(fact.value) + Decimal(item.plan.increment)
        results.append((item.plan.entity, fields["base"]))
    assert len({entity for entity, _ in results}) > 1
    assert len({value for _, value in results}) > 1


@pytest.mark.parametrize("base,increment,expected", [("0.1", "0.2", "0.3"),
    ("1001.5", "0.25", "1001.75"), ("-1.5", "1.5", "0"),
    ("999999999999998.999999", "0.000001", "999999999999999")])
def test_exact_decimal_arithmetic_ignores_ambient_precision(base, increment, expected):
    with localcontext() as context:
        context.prec = 2
        assert generation._derived_value(base, increment) == expected


@pytest.mark.parametrize("base,increment", [("999999999999999", "1"), ("NaN", "1"),
    ("1e3", "1"), ("1.0000001", "1")])
def test_arithmetic_bounds(base, increment):
    with pytest.raises(generation.ArithmeticFailure):
        generation._derived_value(base, increment)


@pytest.mark.parametrize("answer", [PROSE, "{broken", "{}", '{"base":29879337,"derived":"29880337"}',
    '{"base":"29879337","base":"29879337","derived":"29880337"}',
    '{"base":"29879337","derived":"29880337","extra":"x"}'])
def test_malformed_and_original_prose_rejected(spec, sources, answer):
    with pytest.raises(generation.ContractBindingError):
        generation._validate_answer(spec, generation._find_fact(spec, sources), answer)


def test_wrong_base_rejected_even_when_sum_correct(spec, sources):
    with pytest.raises(generation.SourceIntegrityError):
        generation._validate_answer(spec, generation._find_fact(spec, sources), '{"base":"1","derived":"1001"}')


def test_wrong_sum_rejected_even_when_base_correct(spec, sources):
    with pytest.raises(generation.ArithmeticFailure):
        generation._validate_answer(spec, generation._find_fact(spec, sources), '{"base":"29879337","derived":"29880338"}')


def test_generation_checks_output_before_return(monkeypatch):
    monkeypatch.setattr(generation, "_derived_value", lambda *args: "not a decimal")
    with pytest.raises(generation.ContractBindingError):
        generation.generate_compound_answer(QUESTION)


def test_synthetic_policy_cannot_enter_supported_path(spec, monkeypatch):
    configuration, provider, _ = generation.load_bundle()
    policy = spec.policy.model_copy(update={"evidence_kind": "synthetic_test_fixture", "joint_development": None})
    registration = ((policy.contract.question_signature, policy.contract.budget, True, policy),)
    configuration = replace(configuration, component_entries=registration)
    monkeypatch.setattr(generation, "load_bundle", lambda: (configuration, provider, policy))
    with pytest.raises(generation.UnsupportedRegistrationError):
        generation.generate_compound_answer(QUESTION)


def test_configuration_failure_is_not_registration_error(monkeypatch):
    monkeypatch.setattr(generation, "load_bundle", lambda: (_ for _ in ()).throw(OSError("private path")))
    with pytest.raises(generation.ConfigurationLoadingError) as error:
        generation.generate_compound_answer(QUESTION)
    assert not isinstance(error.value, generation.UnsupportedRegistrationError)
    assert "private path" not in str(error.value)


def test_supplied_snapshot_is_used_without_reload(monkeypatch):
    configuration, _, _ = generation.load_bundle()
    monkeypatch.setattr(generation, "load_bundle", lambda: (_ for _ in ()).throw(AssertionError("Reload")))
    assert generation.generate_compound_answer(QUESTION, configuration=configuration).answer == '{"base":"29879337","derived":"29880337"}'
