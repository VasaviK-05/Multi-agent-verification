"""Render complete frozen development tradeoffs; never selects/activates policies."""
from scripts.multitask_policy42 import read
from scripts.multitask_uncertainty_sweep import OUT

def main():
    data=read(OUT/'comparison.json')
    lines=['# Optional coverage / uncertainty development sweep','',data['scope'],
        '', 'No final-test access, new inference, calibration or activation. Independent binary labels remain unchanged.',
        'Costs are summed measured verifier-attempt wall milliseconds under the recorded shared-machine setup, not money or request latency.',
        'FA/FR below are expected counts out of 40 examples (fractional for mixtures); selective risk is errors among decided cases.',
        'Validation loss excludes resource penalty. The separately reported old cost-inclusive diagnostic is not the reliability-first Stage-A objective.',
        'Tiny positive probabilities and floating-point residuals are preserved; target-zero negligible coverage is not useful verification.']
    for r in data['rows']:
        lines+=['',f"## {r['cohort']} / target {r['target']:.0%}",'',
            f"Status: {r['status']}; maximum finalized clean coverage {r['maximum_clean_coverage']:.1%}; fixed budget {r['budget']:.9f} ms."]
        if not r['artifact_created']:
            lines+=['No PolicyArtifact or probability distribution created. Target not relaxed.'];continue
        lines += [f"Artifact: `{r['artifact_path']}`; ID `{r['artifact_id']}`.",
            f"Probability on zero-clean-coverage strategies: {r['zero_coverage_mass']:.17g}.",
            f"Worst-case validation loss: {r['worst_validation_loss']:.12g}.",
            'Positive-probability strategies (all fourteen, including zeros, retained in JSON/artifact):']
        for s in r['probabilities']:
            if s['probability']>0:lines.append(f"- {s['verifiers']} / {s['aggregation']}: p={s['probability']:.17g}; estimated team cost {s['estimated_cost']:.9f} ms.")
        lines+=['','Finalized scenarios:']
        for s in r['scenarios']:
            m=s['metrics'];risk='undefined (no decisions)' if m['selective_risk'] is None else format(m['selective_risk'],'.12g')
            lines.append(f"- {s['attack']}: coverage={m['decision_coverage']:.12g}; uncertainty={s['uncertainty_rate']:.12g}; FA={m['false_accept']:.12g}; FR={m['false_reject']:.12g}; selective risk={risk}; validation loss={s['validation_loss']:.12g}; estimated cost={m['estimated_resource_cost']:.9f} ms; separate old cost-inclusive diagnostic={m['mean_loss']:.12g}.")
            lines.append('  Expected uncertainty reason counts (can overlap): '+str(s['uncertainty_reasons']))
        lines+=['', 'Repeated-fit numerical equivalence: '+str(r['reproducibility'])]
    lines+=['','## Reference audit','',
        'Pairs chosen by first group in each partition, not by verifier success. Full raw metadata, independent labels and frozen task histories are in semantic-reference-audit.json.']
    for e in read(OUT/'semantic-reference-audit.json'):
        report=e['report'];m={} if report is None else report.get('metadata',{})
        lines+=['',f"### {e['cohort']} / {e['role']} / {e['example_id']}",
            f"Question: {e['question']}",f"Reference: {e['reference']}",f"Candidate: {e['answer']}",
            f"Independent correctness label: {e['answer_is_correct']} ({e['label_meaning']}).",
            f"Raw cosine: {m.get('raw_similarity')}; decision: {m.get('decision')}; normalized abstention: {e['abstained']}; uncalibrated vote strength: {e['vote_confidence']}.",
            'Compared text: '+str(m.get('compared_text')), 'Frozen task history: '+str(e['history_snapshot'])]
    with (OUT/'comparison.md').open('x',encoding='utf-8') as f:f.write('\n\n'.join(lines)+'\n')
    print('Complete readable comparison written:',OUT/'comparison.md')

if __name__=='__main__':main()
