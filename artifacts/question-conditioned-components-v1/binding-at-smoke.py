"""Question-only, opt-in protocol for the two diagnosed fact-plus-sum templates.

This module deliberately has no verifier, policy, dataset or truth dependency.
"""
from dataclasses import dataclass
import hashlib
import json
import re

VERSION = 'fact_plus_sum_binding_v1'
_NUMBER = r'-?(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,6})?'
_QUESTION = re.compile(
    rf'What is the (area|population) of ([A-Za-z]+), and what is that (area|population) '
    rf'plus ({_NUMBER})( square kilometres)?\? Give both values\.', re.I)


class BindingError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class ComponentPlan:
    measure: str
    entity: str
    increment: str
    version: str = VERSION

    @property
    def category(self):
        return f'{self.version}:{self.measure}'

    @property
    def plan_id(self):
        return digest([self.version, self.measure, self.entity, self.increment,
            [('base_fact', 'direct_fact'), ('derived_sum', 'arithmetic', 'base_fact')]])


@dataclass(frozen=True)
class BoundComponent:
    component_id: str
    requirement: str
    question: str
    answer: str
    depends_on: tuple[str, ...]
    binding_id: str


def question_plan(question):
    if not isinstance(question, str) or len(question) > 1000:
        raise BindingError('unsupported_category: question exceeds bounded protocol')
    match = _QUESTION.fullmatch(question.strip())
    if not match or match[1].lower() != match[3].lower():
        raise BindingError('unsupported_category: expected a declared fact-plus-sum template')
    measure = match[1].lower()
    if bool(match[5]) != (measure == 'area'):
        raise BindingError('unsupported_category: units do not match the measure')
    return ComponentPlan(measure, match[2].title(), match[4])


def bind_answer(plan, answer):
    """JSON decimal strings only; values never come from a reference or label."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BindingError('answer_binding: duplicate field')
            result[key] = value
        return result
    if not isinstance(answer, str) or len(answer) > 500:
        raise BindingError('answer_binding: expected a bounded JSON object')
    try:
        fields = json.loads(answer, object_pairs_hook=pairs)
    except (ValueError, TypeError) as exc:
        raise BindingError('answer_binding: invalid or duplicate JSON fields') from exc
    if type(fields) is not dict or set(fields) != {'base', 'derived'}:
        raise BindingError('answer_binding: exactly base and derived are required')
    if any(type(v) is not str or re.fullmatch(_NUMBER, v) is None for v in fields.values()):
        raise BindingError('answer_binding: fields must be bounded plain decimal strings')
    base, derived = fields['base'], fields['derived']
    units = ' square kilometres' if plan.measure == 'area' else ''
    inputs = (
        ('base_fact', 'direct_fact', f'What is the {plan.measure} of {plan.entity}?',
         f'The {plan.measure} of {plan.entity} is {base}{units}.', ()),
        ('derived_sum', 'arithmetic', f'What is {base} + {plan.increment}?', derived, ('base_fact',)))
    return tuple(BoundComponent(cid, req, q, a, dep,
        digest([plan.plan_id, cid, q, a, dep])) for cid, req, q, a, dep in inputs)


def component_validation_id(validation_id, bound):
    if not isinstance(validation_id, str) or not validation_id.strip():
        raise BindingError('identity: nonblank request validation ID required')
    return digest([VERSION, validation_id, bound.component_id, bound.binding_id])
