"""Opt-in game-owned completed-consistency output contract.

This validates native report structure, not truth or authenticity. Actual model,
service, prompt, implementation and sampler provenance must ALSO be attested by
an execution resource manifest. It grants no factual/arithmetic/semantic coverage.
Nothing in the historical global output-coverage rules calls this module.
"""
from collections import Counter
import math
from typing import Literal
from pydantic import Field, StrictInt
from app.game.dependencies import FrozenModel
from app.models.schemas import VerificationResult


class ConsistencyAssessmentContract(FrozenModel):
    version: Literal['native_consistency_assessment_v1'] = 'native_consistency_assessment_v1'
    n_samples: StrictInt = Field(gt=0)
    generator_model: str = Field(min_length=1)
    temperature: float = Field(gt=0)


def completed_consistency(report, contract):
    """Directional, stable native assessment; malformed/absent traces fail closed.

    A majority agreement check can support a candidate that is objectively wrong.
    It establishes only completion of the declared consistency-check obligation.
    Abstentions and zero-confidence outcomes cannot establish achieved coverage.
    Contributor eligibility remains the existing finalizer's independent guard.
    """
    contract = ConsistencyAssessmentContract.model_validate(contract)
    if not isinstance(report, VerificationResult) or report.verifier_name != 'confidence':
        return False
    m = report.metadata
    if (not isinstance(m, dict) or type(report.score) not in (int,float)
            or type(report.passed) is not bool or not math.isfinite(report.score) or report.score <= 0):
        return False
    if (m.get('method') != 'self_consistency' or m.get('judgment_source') != 'self_consistency'
            or m.get('generator_model') != contract.generator_model
            or type(m.get('temperature')) not in (int, float)
            or m['temperature'] != contract.temperature
            or type(m.get('n_samples')) is not int or m['n_samples'] != contract.n_samples
            or m.get('stable_answer') is not True
            or not isinstance(m.get('claim'), str) or not m['claim'].strip()):
        return False
    judgments, samples = m.get('judgments'), m.get('samples')
    if (not isinstance(judgments, list) or len(judgments) != contract.n_samples
            or any(type(label) is not str or label not in {'support','reject','unsure'} for label in judgments)
            or not isinstance(samples, list) or len(samples) != contract.n_samples):
        return False
    counts = dict(Counter(judgments))
    if (type(m.get('total_judgments')) is not int or m['total_judgments'] != len(judgments)
            or not isinstance(m.get('judgment_counts'), dict)
            or any(type(value) is not int for value in m['judgment_counts'].values())
            or m['judgment_counts'] != counts):
        return False
    for sample, label in zip(samples, judgments):
        if (not isinstance(sample, dict) or sample.get('label') != label
                or not isinstance(sample.get('sample'), str)
                or type(sample.get('method')) is not str
                or sample['method'] not in {'numeric','string_match','nli','empty_sample'}):
            return False
        if label in {'support','reject'} and not sample['sample'].strip():
            return False
    highest = max(counts.values())
    leaders = [label for label, count in counts.items() if count == highest]
    # Native stable-answer behavior already requires a strict majority. Never
    # reinterpret a low-agreement unique plurality as a stable assessment.
    if len(leaders) != 1 or leaders[0] not in {'support','reject'} or highest * 2 <= len(judgments):
        return False
    leader = leaders[0]
    if (type(m.get('agreement_count')) is not int or m['agreement_count'] != highest
            or m.get('majority_label') != leader
            or m.get('decision') != ('SUPPORT' if leader == 'support' else 'REJECT')
            or report.passed != (leader == 'support')
            or report.score != highest / len(judgments)):
        return False
    return True


def consistency_capabilities(report, contract):
    return {'consistency'} if completed_consistency(report, contract) else set()
