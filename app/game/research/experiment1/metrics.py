"""Exact policy expectations and paired cluster statistics on a complete cube."""
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from app.game.dependencies import FrozenModel
from app.game.offline.attacks import Attack


class Statistics(FrozenModel):
    version: Literal['paired_group_pcg64_percentile_v1'] = 'paired_group_pcg64_percentile_v1'
    confidence_level: Literal[.95] = .95
    resamples: int = Field(default=5000, strict=True, ge=2)
    seed: int = Field(default=20261112, strict=True, ge=0)
    undefined_rule: Literal['omit_interval_if_any_resample_undefined'] = 'omit_interval_if_any_resample_undefined'


class Execution(FrozenModel):
    call_id: str
    state: Literal['directional', 'abstention', 'failed', 'unavailable']
    recorded_state: Literal['directional', 'abstention', 'failed', 'unavailable']
    reason: str
    provenance: str


class Outcome(FrozenModel):
    example_id: str
    group_id: str
    strategy_id: str
    attack_id: str
    correct: bool
    status: Literal['passed', 'failed', 'uncertain']
    estimated_cost: float = Field(ge=0)
    unresolved: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    executions: tuple[Execution, ...] = ()
    components_json: str | None = None


class Distribution(FrozenModel):
    method: str
    probabilities: tuple[tuple[str, float], ...]
    development_coverage: dict

    @model_validator(mode='after')
    def check(self):
        if (not self.probabilities or len({s for s, _ in self.probabilities}) != len(self.probabilities)
                or any(p < 0 for _, p in self.probabilities)
                or abs(math.fsum(p for _, p in self.probabilities) - 1.) > 1e-12):
            raise ValueError('invalid exact method distribution')
        return self


class Cube(FrozenModel):
    """Detached outputs only. Producer must enforce original replay provenance."""
    example_groups: tuple[tuple[str, str], ...]
    strategy_ids: tuple[str, ...]
    attacks: tuple[Attack, ...]
    outcomes: tuple[Outcome, ...]
    methods: tuple[Distribution, ...]
    false_accept_penalty: float = Field(ge=0)
    false_reject_penalty: float = Field(ge=0)
    uncertainty_penalty: float = Field(ge=0)
    resource_coefficient: float = Field(ge=0)
    cost_units: str

    @model_validator(mode='after')
    def check(self):
        examples = dict(self.example_groups)
        attacks = {a.attack_id for a in self.attacks}
        if (not examples or len(examples) != len(self.example_groups) or not self.strategy_ids
                or len(set(self.strategy_ids)) != len(self.strategy_ids) or not attacks
                or len(attacks) != len(self.attacks) or not self.methods
                or len({m.method for m in self.methods}) != len(self.methods)
                or sum(m.method == 'full_minimax' for m in self.methods) != 1):
            raise ValueError('nonempty unique cube axes and full game required')
        keys, truths, costs = set(), {}, {}
        for o in self.outcomes:
            key = o.strategy_id, o.attack_id, o.example_id
            if (key in keys or examples.get(o.example_id) != o.group_id
                    or o.strategy_id not in self.strategy_ids or o.attack_id not in attacks):
                raise ValueError('duplicate or incompatible cube outcome')
            keys.add(key)
            if o.example_id in truths and truths[o.example_id] != o.correct:
                raise ValueError('labels differ across strategies or attacks')
            truths[o.example_id] = o.correct
            if o.strategy_id in costs and costs[o.strategy_id] != o.estimated_cost:
                raise ValueError('frozen strategy cost changed across examples/attacks')
            costs[o.strategy_id] = o.estimated_cost
            if len({e.call_id for e in o.executions}) != len(o.executions):
                raise ValueError('duplicate selected attempt identity')
        if len(keys) != len(examples) * len(self.strategy_ids) * len(attacks):
            raise ValueError('incomplete cube, including zero-probability strategies')
        for method in self.methods:
            if not {s for s, _ in method.probabilities} <= set(self.strategy_ids):
                raise ValueError('method uses an unknown strategy')
        return self


# Additive sufficient statistics; each row's weight is a policy probability.
FIELDS = ('examples', 'correct_accept', 'correct_reject', 'false_accept', 'false_reject',
          'uncertain', 'unresolved', 'estimated_cost_sum', 'execution_failure_attempts',
          'cases_with_execution_failure', 'recorded_execution_failure_attempts')


def vector(outcome):
    o = outcome
    state = ('uncertain' if o.status == 'uncertain' else
             ('correct_' if ((o.status == 'passed') == o.correct) else 'false_') +
             ('accept' if o.status == 'passed' else 'reject'))
    failures = sum(e.state in {'failed', 'unavailable'} for e in o.executions)
    return np.asarray([1., *(float(state == k) for k in FIELDS[1:6]), float(bool(o.unresolved)),
        o.estimated_cost, failures, float(bool(failures)),
        sum(e.recorded_state in {'failed', 'unavailable'} for e in o.executions)], dtype=float)


def measures(totals, cube):
    """Works on one vector or a resample-by-statistic matrix; no risk imputation."""
    t = np.asarray(totals, dtype=float)
    d = {name: t[..., i] for i, name in enumerate(FIELDS)}
    n = d['examples']
    decisions = d['correct_accept'] + d['correct_reject'] + d['false_accept'] + d['false_reject']
    errors = d['false_accept'] + d['false_reject']
    risk = np.divide(errors, decisions, out=np.full_like(errors, np.nan), where=decisions > 0)
    result = {k: v for k, v in d.items() if k != 'estimated_cost_sum'}
    result.update({k + '_rate': d[k] / n for k in ('correct_accept', 'correct_reject', 'false_accept', 'false_reject')})
    validation = (d['false_accept'] * cube.false_accept_penalty + d['false_reject'] * cube.false_reject_penalty
                  + d['uncertain'] * cube.uncertainty_penalty) / n
    cost = d['estimated_cost_sum'] / n
    result.update(decision_coverage=decisions / n, uncertainty_rate=d['uncertain'] / n,
        unresolved_coverage_rate=d['unresolved'] / n, selective_risk=risk,
        validation_loss=validation, estimated_attempt_cost=cost,
        total_loss=validation + cube.resource_coefficient * cost)
    return result


def group_tables(cube):
    groups = sorted({g for _, g in cube.example_groups})
    group_index = {g: i for i, g in enumerate(groups)}
    index = {(o.strategy_id, o.attack_id, o.example_id): o for o in cube.outcomes}
    tables = {}
    for method in cube.methods:
        for attack in cube.attacks:
            table = np.zeros((len(groups), len(FIELDS)))
            for sid, p in method.probabilities:
                for eid, group in cube.example_groups:
                    table[group_index[group]] += p * vector(index[sid, attack.attack_id, eid])
            tables[method.method, attack.attack_id] = table
    return groups, tables


def _reason_counts(cube, method, attack):
    weights = dict(method.probabilities)
    failures, unresolved, reasons, unresolved_reasons = {}, {}, {}, {}
    def add(target, key, weight):
        target[key] = target.get(key, 0.) + weight
    for o in cube.outcomes:
        p = weights.get(o.strategy_id, 0.)
        if o.attack_id != attack.attack_id or p == 0:
            continue
        for e in o.executions:
            if e.state in {'failed', 'unavailable'}:
                add(failures, e.call_id + ':' + e.state + ':' + e.reason, p)
        for cap in set(o.unresolved):
            add(unresolved, cap, p)
        for reason in set(o.reasons):
            add(reasons, reason, p)
            if o.unresolved:
                add(unresolved_reasons, reason, p)
    return dict(execution_failure_reasons=dict(sorted(failures.items())),
        unresolved_requirements=dict(sorted(unresolved.items())),
        unresolved_reasons=dict(sorted(unresolved_reasons.items())), decision_reasons=dict(sorted(reasons.items())))


def point_report(cube):
    cube = Cube.model_validate(cube)
    _, tables = group_tables(cube)
    result = []
    for method in cube.methods:
        cells = []
        for attack in cube.attacks:
            values = measures(tables[method.method, attack.attack_id].sum(axis=0), cube)
            scalars = {k: None if np.isnan(v) else float(v) for k, v in values.items()}
            cells.append(dict(attack_kind=attack.kind, attack_id=attack.attack_id,
                dependency_group_id=attack.group_id, metrics=scalars, **_reason_counts(cube, method, attack)))
        # MAX AFTER averaging all examples and integrating exact probabilities.
        worst = max(c['metrics']['validation_loss'] for c in cells)
        worst_total = max(c['metrics']['total_loss'] for c in cells)
        result.append(dict(method=method.method, probabilities=method.probabilities,
            development_coverage=method.development_coverage, attacks=cells,
            worst_case_expected_loss=worst, worst_case_total_loss=worst_total,
            worst_case_attack_ids=[c['attack_id'] for c in cells if c['metrics']['validation_loss'] == worst],
            worst_case_total_attack_ids=[c['attack_id'] for c in cells if c['metrics']['total_loss'] == worst_total]))
    return result


def bootstrap_report(cube, configuration):
    cube = Cube.model_validate(cube)
    config = Statistics.model_validate(configuration)
    groups, tables = group_tables(cube)
    if len(groups) < 2:
        return dict(configuration=config.model_dump(), groups=len(groups), intervals=[],
            reason='at_least_two_related_example_groups_required')
    draws = np.random.default_rng(config.seed).integers(0, len(groups), size=(config.resamples, len(groups)))
    samples = {}
    for method in cube.methods:
        attacks = []
        for attack in cube.attacks:
            values = measures(tables[method.method, attack.attack_id][draws].sum(axis=1), cube)
            for name, vector_values in values.items():
                samples[method.method, attack.attack_id, name] = vector_values
            attacks.append(values)
        samples[method.method, 'complete_attack_set', 'worst_case_expected_loss'] = np.max(
            [v['validation_loss'] for v in attacks], axis=0)
        samples[method.method, 'complete_attack_set', 'worst_case_total_loss'] = np.max(
            [v['total_loss'] for v in attacks], axis=0)
    for (method, attack, field), values in list(samples.items()):
        if method != 'full_minimax':
            samples['full_minimax-minus-' + method, attack, field] = samples['full_minimax', attack, field] - values
    intervals = []
    tail = (1. - config.confidence_level) / 2.
    actions = {a.attack_id: a for a in cube.attacks}
    for (method, aid, field), values in sorted(samples.items()):
        defined = np.isfinite(values)
        bounds = np.quantile(values, [tail, 1. - tail], method='linear').tolist() if defined.all() else None
        action = actions.get(aid)
        intervals.append(dict(method=method, attack_id=aid,
            attack_kind=action.kind if action else None, dependency_group_id=action.group_id if action else None,
            metric=field, interval95=bounds, defined_resamples=int(defined.sum()),
            total_resamples=config.resamples, undefined_fraction=float(1. - defined.mean())))
    return dict(configuration=config.model_dump(), groups=len(groups), intervals=intervals, reason=None)


def paired_point_differences(points):
    full = next(m for m in points if m['method'] == 'full_minimax')
    result = []
    for baseline in points:
        if baseline is full:
            continue
        attacks = []
        for left, right in zip(full['attacks'], baseline['attacks']):
            if left['attack_id'] != right['attack_id']:
                raise ValueError('paired attack axes differ')
            attacks.append(dict(attack_id=left['attack_id'], attack_kind=left['attack_kind'],
                dependency_group_id=left['dependency_group_id'],
                metrics={k: None if v is None or right['metrics'][k] is None else v - right['metrics'][k]
                         for k, v in left['metrics'].items()}))
        result.append(dict(method='full_minimax-minus-' + baseline['method'], attacks=attacks,
            worst_case_expected_loss=full['worst_case_expected_loss'] - baseline['worst_case_expected_loss'],
            worst_case_total_loss=full['worst_case_total_loss'] - baseline['worst_case_total_loss']))
    return result
