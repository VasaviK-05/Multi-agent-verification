"""Explicit isolated corpus preparation and offline-only scenario fit/validation."""
import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.game.dependencies import FrozenModel
from app.game.models import content_id
from app.game.offline.calibration import Text, read_json


class Replacement(FrozenModel):
    record_id: Text
    expected_text_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    replacement_text: Text


class CorpusAlterations(FrozenModel):
    version: Literal['isolated_corpus_replacements_v1']
    clean_corpus_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    scope: Text
    provenance: Text
    timing: Literal['committed_before_collection_and_team_sampling']
    knowledge: Literal['public_questions_references_and_clean_resources_no_labels_no_sampled_team']
    replacements: tuple[Replacement, ...] = Field(min_length=1)


def prepare(clean_adapter, alterations, output):
    from app.benchmark.project_adapter import AdapterConfiguration, local_path
    from scripts.preparation_config import preparation_adapter
    # Require the same explicit adapter fields as other owned preparation tools.
    output = Path(output).resolve()
    config = preparation_adapter(clean_adapter, output)
    original = AdapterConfiguration.model_validate(read_json(clean_adapter))
    specification = CorpusAlterations.model_validate(read_json(alterations))
    for protected in (original.index_dir, original.embedding_snapshot, original.nli_snapshot):
        if protected is not None:
            protected = local_path(protected).resolve()
            if output == protected or output.is_relative_to(protected) or protected.is_relative_to(output):
                raise ValueError('experimental output must be separate from existing index/model paths')
    source = local_path(original.corpus_path)
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != specification.clean_corpus_sha256:
        raise ValueError('clean corpus digest mismatch')
    rows = json.loads(raw)
    if (not isinstance(rows, list) or not rows or any(not isinstance(r, dict)
            or not isinstance(r.get('id'), str) or not isinstance(r.get('text'), str) for r in rows)):
        raise ValueError('corpus must be a list of string id/text records')
    lookup = {r['id']: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError('duplicate corpus record ID')
    if len({r.record_id for r in specification.replacements}) != len(specification.replacements):
        raise ValueError('duplicate replacement ID')
    for replacement in specification.replacements:
        row = lookup.get(replacement.record_id)
        if row is None or hashlib.sha256(row['text'].encode()).hexdigest() != replacement.expected_text_sha256:
            raise ValueError('missing record or expected text digest mismatch: ' + replacement.record_id)
        if row['text'] == replacement.replacement_text:
            raise ValueError('replacement must alter text')
        row['text'] = replacement.replacement_text
    encoded = (json.dumps(rows, ensure_ascii=False, indent=2) + '\n').encode()
    receipt = dict(version='isolated_corpus_preparation_v1',
        specification=specification.model_dump(mode='json'), specification_id=content_id(specification.model_dump(mode='json')),
        clean_corpus_sha256=hashlib.sha256(raw).hexdigest(), altered_corpus_sha256=hashlib.sha256(encoded).hexdigest(),
        clean_adapter_id=content_id(original.model_dump(mode='json')),
        note='Preparation only. Index build and observed resource manifests are still required; no trust attestation.')
    # All input checks precede any output. Never open the source for writing.
    output.mkdir(parents=True, exist_ok=False)
    (output/'corpus.json').write_bytes(encoded)
    (output/'adapter.json').write_text(config.model_dump_json(indent=2), encoding='utf-8')
    (output/'intervention-preparation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--clean-adapter', required=True, type=Path)
    prep.add_argument('--alterations', required=True, type=Path)
    prep.add_argument('--output-dir', required=True, type=Path)
    for name in ('validate', 'fit'):
        p = sub.add_parser(name)
        p.add_argument('--experiment', required=True, type=Path)
        if name == 'fit':
            p.add_argument('--output-dir', required=True, type=Path)
            p.add_argument('--code-revision', help='Actual current code SHA; required for empirical fitting')
    assembly = sub.add_parser('assemble')
    for name in ('clean-bundle', 'context', 'contract', 'report-attacks'):
        assembly.add_argument('--'+name, required=True, type=Path)
    assembly.add_argument('--scenario', nargs=2, action='append', required=True,
                          metavar=('DECLARATION_JSON', 'RECORDING_DIRECTORY'))
    assembly.add_argument('--output', required=True, type=Path)
    assembly.add_argument('--clean-build-specification', type=Path,
                          help='Required for empirical inputs: existing ready clean PolicyBuildSpecification')
    assembly.add_argument('--scenario-evidence-validation', nargs=2, action='append', default=[],
                          metavar=('DECLARATION_JSON', 'VALIDATION_JSON'))
    evaluation = sub.add_parser('evaluate', help='Evaluate a frozen policy; never fit or export a policy')
    policy_source = evaluation.add_mutually_exclusive_group(required=True)
    policy_source.add_argument('--policy', type=Path)
    policy_source.add_argument('--prototype-bundle', type=Path, help='Extracted package; validates all original package hashes')
    evaluation.add_argument('--task', choices=('arithmetic', 'factual'), help='Required with --prototype-bundle')
    evaluation.add_argument('--clean-bundle', required=True, type=Path)
    evaluation.add_argument('--report-attacks', required=True, type=Path)
    evaluation.add_argument('--scenario', nargs=2, action='append', required=True,
                            metavar=('DECLARATION_JSON', 'RECORDING_DIRECTORY'))
    evaluation.add_argument('--scenario-evidence-validation', nargs=2, action='append', default=[],
                            metavar=('DECLARATION_JSON', 'VALIDATION_JSON'))
    evaluation.add_argument('--output', required=True, type=Path, help='New evaluation JSON file, never policy.json')
    audit = sub.add_parser('audit-collector', help='Read-only source compatibility rehearsal; no model/resource initialization')
    audit.add_argument('--clean-bundle', required=True, type=Path)
    audit.add_argument('--collector-root', required=True, type=Path)
    audit.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            print(json.dumps(prepare(args.clean_adapter, args.alterations, args.output_dir)))
        elif args.command == 'audit-collector':
            from app.game.offline.collect import load_bundle
            from app.game.offline.upstream_evaluation import audit_collector_source
            bundle = load_bundle(args.clean_bundle)
            report = audit_collector_source(bundle.observed_setup, args.collector_root)
            with args.output.open('x', encoding='utf-8') as handle:
                json.dump(report, handle, indent=2)
            print(json.dumps(dict(source_compatible=report['source_compatible'], gaps=report['gaps'],
                ready_for_real_collection=False, factory_initialized=False)))
            return 0 if report['source_compatible'] else 2
        elif args.command in {'assemble', 'evaluate'}:
            from app.game.offline.collect import load_bundle
            from app.game.offline.upstream import UpstreamExperiment
            validations = {}
            for declaration, validation in args.scenario_evidence_validation:
                key = str(Path(declaration).resolve())
                if key in validations:
                    raise ValueError('duplicate scenario evidence validation')
                validations[key] = read_json(validation)
            declarations = {str(Path(p).resolve()) for p, _ in args.scenario}
            if set(validations) - declarations:
                raise ValueError('evidence validation provided for an undeclared scenario')
            scenarios = tuple(dict(intervention=read_json(declaration), bundle=load_bundle(recordings),
                                  evidence_validation=validations.get(str(Path(declaration).resolve())))
                              for declaration, recordings in args.scenario)
            if args.command == 'evaluate':
                from app.game.artifacts import PolicyArtifact
                from app.game.models import content_id
                from app.game.offline.upstream_evaluation import FrozenUpstreamEvaluationInput, evaluate_frozen_upstream
                bundle_id = None
                if args.prototype_bundle is not None:
                    if args.task is None:
                        raise ValueError('--prototype-bundle requires --task')
                    from app.game.prototype_bundle import load_prototype
                    prototype = load_prototype(args.prototype_bundle)
                    entry = next((e for e in prototype.manifest.entries if e.task == args.task), None)
                    if entry is None:
                        raise ValueError('task is unsupported by the original prototype package')
                    source = args.prototype_bundle / entry.artifact_path
                    bundle_id = prototype.manifest.bundle_id
                else:
                    if args.task is not None:
                        raise ValueError('--task is only valid with --prototype-bundle')
                    source = args.policy
                raw = source.read_bytes()
                artifact = PolicyArtifact.model_validate_json(raw)
                clean = load_bundle(args.clean_bundle)
                if bundle_id is not None:
                    if artifact.artifact_id != entry.artifact_id:
                        raise ValueError('artifact bytes changed since prototype validation')
                    if any(content_id(e.question) not in entry.allowed_question_ids for e in clean.request.examples):
                        raise ValueError('clean recording question is outside original prototype scope')
                inputs = FrozenUpstreamEvaluationInput(artifact=artifact, clean=clean,
                    report_attacks=read_json(args.report_attacks), scenarios=scenarios)
                result = evaluate_frozen_upstream(inputs)
                result = type(result).model_validate({**result.model_dump(),
                    'original_artifact_sha256': hashlib.sha256(raw).hexdigest(), 'prototype_bundle_id': bundle_id})
                if source.read_bytes() != raw:
                    raise ValueError('original artifact changed during evaluation; no report published')
                with args.output.open('x', encoding='utf-8') as handle:
                    handle.write(result.model_dump_json(indent=2))
                print(json.dumps(dict(evaluation_id=inputs.evaluation_input_id,
                    original_artifact_id=artifact.artifact_id, new_policy_created=False,
                    evidence_role=result.evidence_role, output=str(args.output))))
                return 0
            experiment = UpstreamExperiment(version='upstream_evidence_experiment_v1',
                clean=load_bundle(args.clean_bundle), context=read_json(args.context),
                contract=read_json(args.contract), report_attacks=read_json(args.report_attacks),
                scenarios=scenarios,
                clean_build_specification=None if args.clean_build_specification is None else read_json(args.clean_build_specification))
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(experiment.model_dump_json(indent=2))
            print(json.dumps(dict(experiment_id=experiment.experiment_id)))
        else:
            from app.game.offline.upstream import UpstreamExperiment, fit_upstream, construct_upstream_payoffs
            experiment = UpstreamExperiment.model_validate(read_json(args.experiment))
            if args.command == 'validate':
                print(json.dumps(dict(valid=True, experiment_id=experiment.experiment_id)))
                return 0
            fitted = fit_upstream(experiment, actual_code_revision=args.code_revision)
            context, _, metrics, outcomes = construct_upstream_payoffs(experiment)
            from app.game.offline.build import environment_versions
            from app.game.offline.evaluation import summarize
            probabilities = dict(fitted.artifact.policy.solution.probabilities)
            mixed = []
            for scenario_id in fitted.artifact.policy.matrix.attack_ids:
                summary = summarize(tuple((o, probabilities[o.strategy_id]) for o in outcomes
                                          if o.attack_id == scenario_id), context.loss_configuration)
                mixed.append(dict(scenario_id=scenario_id, **summary.model_dump(mode='json'),
                    validation_loss=summary.validation_loss(context.loss_configuration),
                    uncertainty_rate=summary.uncertainty_rate))
            report = dict(experiment_id=experiment.experiment_id, artifact_id=fitted.artifact.artifact_id,
                clean_resource_manifest_id=experiment.contract.resource_manifest.manifest_id,
                experimental_resource_manifest_ids=[s.intervention.altered_resources.manifest_id for s in experiment.scenarios],
                versions=environment_versions(), randomness='no fitting RNG; collection controls in requests',
                probabilities=fitted.artifact.policy.solution.probabilities,
                policy_metrics=mixed, worst_case_scenario=max(mixed, key=lambda m: m['mean_loss'])['scenario_id'],
                metrics=[dict(strategy_id=s, scenario_id=a, **m.model_dump(mode='json'),
                    validation_loss=m.validation_loss(context.loss_configuration), uncertainty_rate=m.uncertainty_rate)
                    for s, a, m in metrics], outcomes=[o.model_dump(mode='json') for o in outcomes])
            args.output_dir.mkdir(parents=True, exist_ok=False)
            for name, value in [('fit.json', fitted.model_dump(mode='json')),
                                ('policy.json', fitted.artifact.model_dump(mode='json')), ('development.json', report)]:
                (args.output_dir/name).write_text(json.dumps(value, indent=2), encoding='utf-8')
            from app.game.offline.upstream import UpstreamFit
            UpstreamFit.model_validate(read_json(args.output_dir/'fit.json'))
            print(json.dumps(dict(artifact_id=fitted.artifact.artifact_id, reload_validated=True)))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps(dict(status='input_error', message=str(exc), new_policy_created=False)))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
