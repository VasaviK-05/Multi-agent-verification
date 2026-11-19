"""Explicit resource binding for reusable policies; no settings/default activation.

Flexible ValidationService deliberately supplies an inert selector. This adapter
binds an artifact's reviewed native selector/observer per compatible request.
Native factories are lazy: construction here performs metadata validation only.
"""
from types import MappingProxyType
from app.game.reusable_policy import ReusablePolicyGameRuntime


class FactoryBoundReusablePolicyRuntime(ReusablePolicyGameRuntime):
    def __init__(self, artifacts, scopes, *, rng, resource_factories):
        super().__init__(artifacts,scopes,rng=rng,resource_observer=None)
        captured=dict(resource_factories)
        if set(captured)!={a.artifact_id for a in self._provider.snapshot()} or not all(callable(v) for v in captured.values()):
            raise ValueError('one explicit resource factory required for every fitted artifact')
        self._resource_factories=MappingProxyType(captured)

    def run(self, selector, analysis, request, validation_id, *, execution_journal=None):
        from app.game.component_execution import unavailable
        resolved,failed=self.resolve(request.question,request.context)
        if resolved is None:return failed
        scope,artifact,_,_=resolved
        try:
            actual_selector,observer=self._resource_factories[artifact.artifact_id](artifact)
            if not callable(getattr(observer,'snapshot_for',None)):
                raise ValueError('resource factory must attest its actual selector')
            observed=observer.snapshot_for(actual_selector)
        except (OSError,TypeError,ValueError) as exc:
            result=unavailable('resource_incompatible: '+str(exc))
            result.summary.update(artifact_id=artifact.artifact_id,policy_id=artifact.policy.policy_id)
            return result
        # Request-local engine/observer: no mutable observer slot is shared across
        # concurrent requests. The same immutable policy and RNG are retained.
        runtime=ReusablePolicyGameRuntime([artifact],[scope],rng=self._rng,resource_observer=observer)
        result=runtime.run(actual_selector,analysis,request,validation_id,execution_journal=execution_journal)
        result.summary.update(runtime_resource_binding='reviewed_factory_bound_reuse_v1',
            pre_dispatch_resource_manifest_id=observed.manifest_id)
        return result


def reviewed_resource_factories(legacy_runtime, artifacts):
    """Reuse original proof-aware factories, not category-to-team heuristics.

    Exact frozen artifact/strategy support determines each authorized resource
    closure. No resource is constructed, inspected remotely, downloaded or changed
    until a compatible request explicitly invokes its factory.
    """
    from app.game.offline.singleton_compatibility import transfer_for
    reference_id='ee32392c870fba30b08b4f7509af645019d9f8b92dc7c39bafeceb8207745c8f'
    factories={}
    for artifact in artifacts:
        if artifact.artifact_id==reference_id:
            def create(actual,expected=artifact):
                if actual!=expected:raise ValueError('factory artifact changed')
                from app.game.offline.reference_compatibility import create_reference
                from scripts.reconciliation import selector_for
                pool,observer=create_reference(legacy_runtime._adapter_for('reference'),actual)
                return selector_for(pool),observer
        else:
            _,binding=transfer_for(artifact)
            route={'rule':'arithmetic','evidence':'factual'}[binding['selected']]
            def create(actual,expected=artifact,route=route):
                if actual!=expected:raise ValueError('factory artifact changed')
                from app.game.offline.singleton_compatibility import create_singleton
                return create_singleton(legacy_runtime._adapter_for(route),actual)
        factories[artifact.artifact_id]=create
    return factories


def compose_factory_bound_reuse(legacy_runtime, artifacts, scopes, *, rng):
    """Owned integration entry point for a future opt-in deployment factory.

    The teammate supplies validated scopes and calls this only on an explicit
    server configuration path. Existing exact registrations always win.
    """
    from app.game.category_deployment import create_category_game_runtime
    artifacts=tuple(artifacts)
    runtime=FactoryBoundReusablePolicyRuntime(artifacts,scopes,rng=rng,
        resource_factories=reviewed_resource_factories(legacy_runtime,artifacts))
    return create_category_game_runtime(legacy_runtime,runtime)
