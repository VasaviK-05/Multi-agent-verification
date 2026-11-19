"""Data-only real-router regression check; requires project imports, never inference.

Run after environment setup. Existing frozen router source/package bytes are
checked before loading. This does not demonstrate verifier execution.
"""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from preservation import snapshot, BASE, preservation_changes


def main():
    before = json.loads(BASE.read_text())
    current = snapshot()
    if preservation_changes(before, current):
        raise RuntimeError('existing source/artifact regression blocks routing test')
    from scripts.policy_package import load
    from app.game.category_runtime import ExactFirstCategoryDispatcher
    config, provider, compound = load(ROOT/'reconciliation/policies.json')
    router = config.router()
    artifacts = provider.snapshot()
    records = []

    class LegacyResolution:
        def run(self, selector, analysis, request, validation_id, **kwargs):
            kind, key, resolved = router.resolve(request.question, request.context)
            result = dict(kind=kind, key=key)
            if resolved is None:
                return result
            route = resolved[0]
            if kind == 'atomic':
                artifact, = [a for a in artifacts if a.context == route[3].context]
                result.update(artifact_id=artifact.artifact_id, policy_id=artifact.policy.policy_id,
                    compatibility_id=artifact.context.compatibility_id,
                    probabilities=artifact.policy.solution.probabilities,
                    resource_requirements=artifact.contract.model_dump(mode='json'),
                    budget=artifact.context.budget,
                    strategies=[s.model_dump(mode='json') for s in artifact.policy.strategies],
                    costs=artifact.context.attempt_costs, cost_units=artifact.context.cost_units,
                    reputation_snapshot_id=artifact.context.reputation_snapshot_id,
                    reference_required=artifact.context.plan.reference_available)
            else:
                result.update(policy_id=compound.policy_id,
                    compatibility_id=compound.contract.compatibility_id,
                    probabilities=compound.solution.probabilities,
                    resource_requirements=compound.contract.model_dump(mode='json'), matrix=compound.matrix.model_dump(mode='json'))
            return result

    class ForbiddenCategory:
        def run(self, *args, **kwargs):
            raise AssertionError('existing exact question entered category runtime')

    legacy = LegacyResolution()
    composed = ExactFirstCategoryDispatcher(legacy, config.allowlist, ForbiddenCategory())
    for question in sorted(config.allowlist):
        reference = question.partition(': ')[2] if question.startswith('Paraphrase this reference: ') else 'External reference fixture'
        for context in (None, reference, 'support,reject'):
            request = SimpleNamespace(question=question, context=context)
            old = legacy.run(None, None, request, 'routing-regression')
            new = composed.run(None, None, request, 'routing-regression')
            if old != new:
                raise AssertionError('exact route changed: '+question)
            records.append(dict(question=question, reference=context, route=old))
    print(json.dumps(dict(questions=len(config.allowlist), checks=len(records), records=records), indent=2))


if __name__ == '__main__':
    main()
