"""Aggregate-only publication bundle from explicitly authenticated prospective reports.

No replay, inference, solver, raw dataset discovery or Final Test loader lives here.
SHA-256 establishes byte identity, not independent scientific authentication.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from app.game.research.__main__ import _object, _nonfinite


def load_report(path, digest):
    path = Path(path).resolve()
    if set(path.parts) & {'test', 'final_test', 'heldout'} or path.name in {
            'final-partition.json', 'reserved-request.json', 'heldout-results.json', 'replay-outcomes.json'}:
        raise ValueError('report loader refuses reserved payload paths')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('report SHA-256 mismatch')
    return json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite)


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def _csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _tex(value):
    return ''.join({'\\': r'\textbackslash{}', '_': r'\_', '%': r'\%', '&': r'\&',
                    '#': r'\#', '{': r'\{', '}': r'\}', '$': r'\$', '^': r'\^{}', '~': r'\~{}'}.get(c, c)
                   for c in str(value))


def _number(value):
    return '--' if value is None else f'{value:.4f}'


def _table(path, rows, title):
    lines = ['% ' + title, r'\begin{tabular}{lllrrr}', r'\hline',
             r'Cohort & Split & Method & Clean loss & Worst loss & Cost \\', r'\hline']
    for r in rows:
        lines.append(' & '.join([_tex(r['cohort']), _tex(r['role']), _tex(r['method']),
            _number(r['clean_loss']), _number(r['worst_case_expected_loss']) + (' [' + _number(r['worst_lower95']) + ', ' + _number(r['worst_upper95']) + ']' if r.get('worst_lower95') is not None else ' [CI unavailable]'), _number(r['estimated_attempt_cost'])]) + r' \\')
    lines.extend([r'\hline', r'\end{tabular}'])
    path.write_text('\n'.join(lines) + '\n')


def export_reports(reports, destination, *, command, allow_synthetic=False):
    """Write a fresh bundle after all figures succeed; never replace existing paths.

    One study/manifest/split/evidence kind per bundle; cohorts remain separate.
    Records are aggregated outputs only, never original questions/references/labels.
    """
    reports = list(reports)
    json.dumps(reports, allow_nan=False) # reject nonfinite values before creating output paths
    if not reports:
        raise ValueError('at least one prospective report required')
    identity = ('study_id', 'manifest_id', 'protocol_id', 'role', 'evidence_kind')
    seen = set()
    for r in reports:
        if r.get('version') != 'prospective_experiment1_report_v1' or r.get('cohort') not in {'arithmetic', 'factual'}:
            raise ValueError('expected prospective Arithmetic/Factual report')
        if any(r.get(k) != reports[0].get(k) for k in identity) or r['cohort'] in seen:
            raise ValueError('mixed study, manifest, split, evidence kind or duplicate cohort')
        seen.add(r['cohort'])
        if r['role'] not in {'development', 'final_test'} or r['evidence_kind'] not in {'empirical', 'synthetic_test_fixture'}:
            raise ValueError('unknown split or evidence kind')
        if r['evidence_kind'] != 'empirical' and not allow_synthetic:
            raise ValueError('synthetic export requires explicit allow_synthetic')
        if not r.get('provenance') or not r.get('metrics') or not r.get('fairness', {}).get('exact_probabilities'):
            raise ValueError('missing provenance, metrics or exact expectation contract')
        for m in r['metrics']:
            if sum(a['attack_kind'] == 'clean' for a in m['attacks']) != 1:
                raise ValueError('exactly one clean attack per method required')
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('refusing to overwrite result destination')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.experiment1-export-', dir=destination.parent))
    try:
        _write_bundle(reports, temporary, command)
        # mkdir reserves the destination without replacing a competing writer.
        destination.mkdir()
        try:
            for child in temporary.iterdir():
                child.rename(destination / child.name)
        except BaseException:
            # Leave a visibly partial destination rather than erase anyone's work.
            raise
    finally:
        shutil.rmtree(temporary)
    return destination


def _write_bundle(reports, root, command):
    for name in ('manifests', 'recordings', 'policies', 'metrics', 'figures', 'tables', 'reports'):
        (root / name).mkdir()
    synthetic = reports[0]['evidence_kind'] != 'empirical'
    title = 'SYNTHETIC TEST — ' if synthetic else ''
    title += reports[0]['role'].replace('_', ' ').title()
    cells, summaries, intervals, probabilities = [], [], [], []
    receipts = []
    for r in reports:
        tag = dict(cohort=r['cohort'], role=r['role'])
        receipts.append(dict(**tag, report_canonical_sha256=hashlib.sha256(
            json.dumps(r, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            policy_id=r['policy_id'], comparison_id=r['comparison_id'], cube_id=r['cube_id'],
            payload_sha256=r['payload_sha256'], provenance=r['provenance'],
            execution_receipt=r.get('execution_receipt')))
        # Keep complete aggregate reports: includes reasons, unavailable methods and CI null explanations.
        _json(root / 'metrics' / (r['cohort'] + '_report.json'), r)
        for m in r['metrics']:
            clean = next(a for a in m['attacks'] if a['attack_kind'] == 'clean')
            summaries.append(dict(**tag, method=m['method'], clean_loss=clean['metrics']['validation_loss'],
                worst_case_expected_loss=m['worst_case_expected_loss'],
                worst_case_total_loss=m['worst_case_total_loss'],
                estimated_attempt_cost=clean['metrics']['estimated_attempt_cost'],
                development_coverage_compliant=m['development_coverage'].get('satisfies')))
            for a in m['attacks']:
                cells.append(dict(**tag, method=m['method'], attack_id=a['attack_id'],
                    attack_kind=a['attack_kind'], dependency_group_id=a['dependency_group_id'], **a['metrics']))
            for strategy, probability in m['probabilities']:
                probabilities.append(dict(**tag, method=m['method'], strategy_id=strategy, probability=probability))
        point_lookup={}
        for m in [*r['metrics'], *r['paired_differences']]:
            for a in m['attacks']:
                for field,value in a['metrics'].items():
                    point_lookup[m['method'],a['attack_id'],field]=value
            for field in ('worst_case_expected_loss','worst_case_total_loss'):
                point_lookup[m['method'],'complete_attack_set',field]=m[field]
        for i in r['uncertainty']['intervals']:
            bounds = i['interval95']
            intervals.append(dict(**tag, **{k:v for k,v in i.items() if k != 'interval95'},
                point_estimate=point_lookup.get((i['method'],i['attack_id'],i['metric'])),
                lower95=None if bounds is None else bounds[0], upper95=None if bounds is None else bounds[1]))
    for s in summaries:
        interval=next((i for i in intervals if i['cohort']==s['cohort'] and i['method']==s['method']
            and i['metric']=='worst_case_expected_loss' and i['attack_id']=='complete_attack_set'),{})
        s.update(worst_lower95=interval.get('lower95'),worst_upper95=interval.get('upper95'))
    _csv(root / 'metrics/clean_vs_attacked.csv', cells)
    _csv(root / 'metrics/baseline_comparison.csv', summaries)
    _csv(root / 'metrics/coverage_and_risk.csv', [{k:v for k,v in r.items() if k in
        ('cohort','role','method','attack_id','attack_kind','dependency_group_id','decision_coverage','selective_risk','uncertainty_rate','unresolved_coverage_rate')} for r in cells])
    _csv(root / 'metrics/cost_analysis.csv', [{k:v for k,v in r.items() if k in
        ('cohort','role','method','attack_id','attack_kind','dependency_group_id','estimated_attempt_cost','validation_loss','total_loss')} for r in cells])
    _csv(root / 'metrics/paired_confidence_intervals.csv', intervals, fields=['cohort','role','method','attack_id','attack_kind','dependency_group_id','metric','point_estimate','lower95','upper95','defined_resamples','total_resamples','undefined_fraction'])
    _table(root / 'tables/experiment1_main.tex', [r for r in summaries if r['method']=='full_minimax'], title)
    _table(root / 'tables/baseline_comparison.tex', summaries, title)
    _json(root / 'manifests/aggregate_receipts.json', receipts)
    _csv(root / 'policies/strategy_probabilities.csv', probabilities)
    (root / 'recordings/README.md').write_text('Raw recordings are deliberately excluded. Retrieve them from reviewed private custody using the training manifest and released payload hashes in aggregate_receipts.json.\n')
    _figures(root / 'figures', cells, summaries, intervals, probabilities, title, reports)
    missing = sorted({'arithmetic','factual'} - {r['cohort'] for r in reports})
    notes = [title, '', 'Offline report-level corruption; these results do not establish actual evidence poisoning.',
        'Each cohort is separate. Development results are exploratory and are not held-out Final Test results.',
        'Loss is decision validation loss; cost is estimated attempted-verifier cost in each cohort’s approved units, not observed latency.',
        'Intervals are paired related-group percentile bootstrap intervals, pointwise rather than simultaneous; no significance claims are inferred.',
        'Null selective risk and missing intervals are retained; no imputation. Risk/coverage and cost/loss plots show frozen operating points, not retuned curves.',
        'Unavailable methods and noncompliant uniform coverage remain explicit in the aggregate report JSON.',
        'Absent cohorts: ' + (', '.join(missing) or 'none'),
        'Raw questions, references, correctness labels and execution records are excluded. Review receipts before publication.']
    (root / 'reports/experiment1_results.md').write_text('\n\n'.join(notes)+'\n')
    files = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
    _json(root / 'reports/reproducibility.json', dict(version='prospective_experiment1_export_v1',
        evidence_kind=reports[0]['evidence_kind'], command=command, receipts=receipts, absent_cohorts=missing,
        files_sha256=files, export_environment=dict(
            python=__import__('sys').version, platform=__import__('platform').platform(),
            matplotlib=__import__('importlib.metadata',fromlist=['version']).version('matplotlib'),
            numpy=__import__('importlib.metadata',fromlist=['version']).version('numpy'))))


def _figures(root, cells, summaries, intervals, probabilities, title, reports):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    lookup = {(i['cohort'],i['method'],i['attack_id'],i['metric']):i for i in intervals}
    cohorts = sorted({r['cohort'] for r in summaries})
    def save(fig, name, rows):
        fig.suptitle(title)
        fig.tight_layout(rect=(0,0,1,.94), w_pad=3)
        for suffix in ('png','pdf'):
            fig.savefig(root / (name+'.'+suffix), dpi=300, bbox_inches='tight')
        plt.close(fig)
        _csv(root / (name+'.csv'), rows)
    fig, axes = plt.subplots(1,len(cohorts),figsize=(8*len(cohorts),5),squeeze=False)
    for ax, cohort in zip(axes[0], cohorts):
        rows = [r for r in summaries if r['cohort']==cohort]
        for x,r in enumerate(rows):
            clean = next(c for c in cells if c['cohort']==cohort and c['method']==r['method'] and c['attack_kind']=='clean')
            for offset, metric, aid, value, color, label in ((-.12,'validation_loss',clean['attack_id'],r['clean_loss'],'C0','Clean'),
                    (.12,'worst_case_expected_loss','complete_attack_set',r['worst_case_expected_loss'],'C1','Worst attack (including clean)')):
                ax.plot(x+offset,value,'o',color=color,label=label if x==0 else None)
                i=lookup.get((cohort,r['method'],aid,metric))
                if i and i['lower95'] is not None:
                    # Percentile intervals need not contain the point estimate.
                    ax.vlines(x+offset,i['lower95'],i['upper95'],color=color)
        ax.set(xticks=range(len(rows)),xticklabels=[r['method'] for r in rows],ylabel='Decision validation loss',title=cohort.title())
        ax.tick_params(axis='x',rotation=65);ax.legend(fontsize=8)
    save(fig,'clean_vs_attacked',summaries + [dict(row_kind='interval', **i) for i in intervals if i['metric'] in {'validation_loss','worst_case_expected_loss'} and '-minus-' not in i['method']])
    for name,xfield,yfield,xlabel,ylabel in (
        ('risk_coverage','decision_coverage','selective_risk','Decision coverage','Selective risk'),
        ('cost_loss','estimated_attempt_cost','validation_loss',None,'Decision validation loss')):
        fig,axes=plt.subplots(1,len(cohorts),figsize=(8*len(cohorts),5),squeeze=False)
        for ax,cohort in zip(axes[0],cohorts):
            methods=sorted({c['method'] for c in cells if c['cohort']==cohort})
            for index,method in enumerate(methods):
                rows=[c for c in cells if c['cohort']==cohort and c['method']==method and c[yfield] is not None]
                ax.scatter([r[xfield] for r in rows],[r[yfield] for r in rows],label=method,marker=['o','s','^','D','v','P','X'][index%7],alpha=.7)
            units=next(r['provenance']['cost_units'] for r in reports if r['cohort']==cohort)
            ax.set(xlabel=xlabel or 'Estimated attempted cost\n('+units+')',ylabel=ylabel,title=cohort.title())
            ax.legend(fontsize=7)
        save(fig,name,cells)
    fig,axes=plt.subplots(1,len(cohorts),figsize=(9*len(cohorts),6),squeeze=False)
    for ax,cohort in zip(axes[0],cohorts):
        rows=[r for r in probabilities if r['cohort']==cohort]
        methods=sorted({r['method'] for r in rows});strategies=sorted({r['strategy_id'] for r in rows})
        data=[[next((r['probability'] for r in rows if r['method']==m and r['strategy_id']==s),0.) for s in strategies] for m in methods]
        im=ax.imshow(data,aspect='auto',vmin=0,vmax=1,cmap='Blues')
        ax.set(yticks=range(len(methods)),yticklabels=methods,xticks=range(len(strategies)),
            xticklabels=['S'+str(i+1) for i in range(len(strategies))],title=cohort.title(),xlabel='Strategy (IDs in accompanying CSV)')
        fig.colorbar(im,ax=ax,label='Exact probability')
    save(fig,'strategy_distribution',[dict(r,strategy_label='S'+str(sorted({p['strategy_id'] for p in probabilities if p['cohort']==r['cohort']}).index(r['strategy_id'])+1)) for r in probabilities])


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',nargs=2,action='append',required=True,metavar=('PATH','SHA256'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-synthetic',action='store_true')
    args=p.parse_args(argv)
    export_reports([load_report(path,digest) for path,digest in args.report],args.output,
        command=['python','-m',__spec__.name,*(argv if argv is not None else __import__('sys').argv[1:])],
        allow_synthetic=args.allow_synthetic)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
