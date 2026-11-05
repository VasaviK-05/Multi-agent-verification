"""Opt-in configuration over TaskPolicyRouter, with no API/default activation."""
from dataclasses import dataclass
import re
from app.analysis.capability_probe_analyzer import CapabilityProbeAnalyzer
from app.game.component_binding import question_plan, BindingError, VERSION
from app.game.models import content_id
from app.game.task_conditioning import TaskPolicyRouter, analysis_signature


def classify_question(question, reference=None, *, component_catalog=None, reference_question_version=None):
    """Only pre-dispatch question features; reference contributes presence, not truth."""
    analyzer = CapabilityProbeAnalyzer()
    if reference_question_version is not None and question.startswith('Paraphrase this reference: '):
        from app.analysis.reference_study_analyzer import VERSION as reference_version,analyze_reference
        if reference_question_version!=reference_version:raise ValueError('unsupported reference category version')
        analysis=analyze_reference(question)
        return 'atomic',analysis_signature(analysis,reference),analysis
    if component_catalog is not None:
        from app.game.component_sources import Catalog,question_plan as v2_plan,VERSION as V2
        catalog=Catalog.model_validate(component_catalog)
        try:plan=v2_plan(question,catalog)
        except BindingError:pass
        else:
            analysis=analyzer.base.analyze(question)
            # Exactly two declared checks; no empirical easy/hard adaptation claim.
            signature=(content_id(dict(version=V2,catalog=catalog.model_dump(mode='json'),
                domain=analysis.domain,requirements=['arithmetic','direct_fact'])),
                'two_required_checks',2.0,bool(reference and reference.strip()))
            return 'component',signature,analysis
    try:
        plan = question_plan(question)
    except BindingError:
        # Do not let a factual prefix silently swallow unsupported compound work.
        if re.search(r'\band\b|\b(?:plus|minus|times|divided)\b|give both values', question, re.I):
            # Known standalone arithmetic wording must still delegate normally.
            from app.selection.requirements import requirement_inputs
            standalone=analyzer.analyze(question)
            req=requirement_inputs(standalone)
            if req.requirements in {('arithmetic',),('semantic_comparison',)} and not req.unsupported:
                return 'atomic',analysis_signature(standalone,reference),standalone
            raise ValueError('unsupported_category: no declared component template')
        analysis = analyzer.analyze(question)
        try:
            signature = analysis_signature(analysis, reference)
        except ValueError as exc:
            raise ValueError('unsupported_category: ' + str(exc)) from exc
        return 'atomic', signature, analysis
    analysis = analyzer.base.analyze(question)
    signature = (content_id(dict(version=VERSION, category=plan.category,
        domain=analysis.domain, domain_status=analysis.domain_status,
        requirements=['arithmetic', 'direct_fact'])), analysis.difficulty,
        analysis.difficulty_score, bool(reference and reference.strip()))
    return 'component', signature, analysis


@dataclass(frozen=True)
class QuestionPolicyConfiguration:
    """Explicit registrations only. Atomic entries retain their original episodes.

    component_entries: (signature, budget, primary, ComponentPolicy). An absent
    compound policy is represented by an ordinary unavailable route and reason.
    allowlist is optional and separate from the untouched PrototypeRouter guard.
    """
    atomic_routes: tuple = ()
    component_entries: tuple = ()
    unavailable_routes: tuple = ()
    allowlist: frozenset[str] | None = None
    component_catalog_json: str | None = None
    reference_question_version: str | None = None

    def __post_init__(self):
        for field in ('atomic_routes','component_entries','unavailable_routes'):
            object.__setattr__(self,field,tuple(tuple(row) for row in getattr(self,field)))
        if self.allowlist is not None:
            object.__setattr__(self,'allowlist',frozenset(self.allowlist))
        if self.reference_question_version is not None and self.allowlist is None:
            raise ValueError('bounded reference routing requires an explicit question allowlist')

    def router(self):
        return QuestionPolicyRouter(self)


class QuestionPolicyRouter:
    def __init__(self, configuration):
        from app.game.component_execution import ComponentPolicy
        self.configuration = configuration
        components = tuple((sig, budget, primary, ComponentPolicy.model_validate(policy))
            for sig, budget, primary, policy in configuration.component_entries)
        for sig, budget, _, policy in components:
            if sig != policy.contract.question_signature or budget != policy.contract.budget:
                raise ValueError('component registration differs from bound question signature/budget')
        self.components = components
        catalogs={p.contract.descriptor_catalog_json for _,_,_,p in components if p.contract.descriptor_catalog_json is not None}
        if configuration.component_catalog_json is not None:catalogs.add(configuration.component_catalog_json)
        from app.game.component_sources import Catalog
        normalized={Catalog.model_validate_json(c).model_dump_json() for c in catalogs}
        if len(normalized)>1:raise ValueError('one explicit V2 source catalog per router configuration')
        self.catalog=Catalog.model_validate_json(next(iter(normalized))) if normalized else None
        # All categories share the existing router's uniqueness/lookup semantics.
        self.tasks = TaskPolicyRouter(configuration.atomic_routes + configuration.unavailable_routes +
            tuple((sig, budget, primary, None, 'component_dispatch') for sig, budget, primary, _ in components))

    def resolve(self, question, reference=None, budget=None):
        if self.configuration.allowlist is not None and question not in self.configuration.allowlist:
            return 'unsupported_category', 'question outside explicit allowlist', None
        try:
            kind, signature, analysis = classify_question(question, reference,component_catalog=self.catalog,
                reference_question_version=self.configuration.reference_question_version)
        except ValueError as exc:
            return 'unsupported_category', str(exc), None
        route = self.tasks.resolve(signature, budget)
        if route is None:
            return 'missing_policy', 'no unique registered question category/budget policy', None
        if route[3] is None and route[4] != 'component_dispatch':
            return 'missing_policy', route[4], None
        return kind, signature, (route, analysis)

    def run(self, selector, request, validation_id, *, provider, rng, resource_observer,
            budget=None, allow_synthetic_for_tests=False):
        from app.game.component_execution import run_component_policy, unavailable
        kind, key, resolved = self.resolve(request.question, request.context, budget)
        if resolved is None:
            return unavailable(kind + ': ' + key)
        route, analysis = resolved
        if kind == 'atomic':
            return self.tasks.run(selector, analysis, request, validation_id, provider=provider,
                rng=rng, resource_observer=resource_observer, budget=budget,
                allow_synthetic_for_tests=allow_synthetic_for_tests)
        matches = [p for sig, b, _, p in self.components if sig == key and b == route[1]]
        if len(matches) != 1:
            return unavailable('incompatible_policy: category registration type mismatch')
        return run_component_policy(matches[0], selector, request.question, request.answer,
            request.context, validation_id, rng=rng, resource_observer=resource_observer,
            allow_synthetic_for_tests=allow_synthetic_for_tests)


def configuration_from_atomic_artifacts(artifacts, *, allowlist=None):
    """Validate explicitly supplied artifacts; return config and frozen provider.

    There is no filesystem discovery, global registry change, or implicit default.
    More than one primary policy for a signature/budget is rejected by the router.
    """
    from app.game.artifacts import PolicyArtifact, DeploymentEpisode, InMemoryPolicyProvider
    from app.game.task_conditioning import TaskSnapshotBinding
    captured=tuple(PolicyArtifact.model_validate(a) for a in artifacts)
    routes=[]
    for artifact in captured:
        context=artifact.context
        binding=TaskSnapshotBinding.model_validate_json(context.task_conditioning_json or '{}')
        plan=context.plan
        signature=(binding.identity.task_id,plan.difficulty,plan.difficulty_score,plan.reference_available)
        episode=DeploymentEpisode(episode_id='registered-'+artifact.artifact_id, context=context,
            contract=artifact.contract,execution_configuration_id=artifact.execution_configuration_id)
        routes.append((signature,context.budget,True,episode,''))
    configuration=QuestionPolicyConfiguration(atomic_routes=tuple(routes),allowlist=allowlist)
    configuration.router()  # Validate registration uniqueness before returning.
    return configuration,InMemoryPolicyProvider(captured)
