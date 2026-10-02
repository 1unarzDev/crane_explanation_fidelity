"""Descriptive v11 support/coverage and deterministic-realization tradeoffs.

No inferential test, confidence interval or independent-answer N is computed.
"""
import json
import hashlib
from pathlib import Path
from statistics import median
from .development_full_battery_scoring import prepare
from .journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'


def summarize():
    score_path=BASE/'development_full_battery_scoring_v1/report.json'
    method_path=BASE/'development_rich_methods_v1/report.json'
    score=json.loads(score_path.read_text());methods=json.loads(method_path.read_text())
    if score['status']!='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED':raise ValueError('closed development workflow required')
    entries,*_=prepare();payloads={(r['identity']['job_id'],r['identity']['method']):r['payload'] for r in entries}
    tables=[]
    for method in ('HX-CONTRACT','HX-PROMPT'):
        labels=[r for r in score['answer_labels'] if r['method']==method]
        answers=[r for r in methods['answers'] if r['method']==method]
        if len(labels)!=54 or len(answers)!=54:raise ValueError('complete old nine-generation battery required')
        count=len(labels);passes=sum(r['status']=='PASS' for r in labels);unresolved=sum(r['status']=='UNRESOLVED' for r in labels)
        covered=required=coverage_complete=known_material=known_specific=ambiguous=0
        for row in labels:
            required_ids={u['unit_id'] for u in payloads[(row['job_id'],method)]['required_units']}
            label=row['label']
            if label is None:raise ValueError('secondary completeness cannot silently drop unknown labels')
            seen=set(label['covered_units']);covered+=len(seen&required_ids);required+=len(required_ids)
            coverage_complete+=required_ids<=seen;known_material+=label['unsupported_material'];known_specific+=label['overlicensed_specificity'];ambiguous+=bool(label['ambiguous_spans'])
        words=[a['word_count'] for a in answers]
        tables.append(dict(method=method,generated_answers=count,independent_development_episodes=6,
            useful_supported_answer_rate_bounds=[passes/count,(passes+unresolved)/count],unresolved_answers=unresolved,
            complete_required_unit_coverage=coverage_complete/count,required_unit_recall=covered/required,
            known_unsupported_material_rate=known_material/count,known_overlicensed_specificity_rate=known_specific/count,
            material_ambiguity_rate=ambiguous/count,unsupported_rate_bounds=[known_material/count,(known_material+ambiguous)/count],
            word_count=dict(minimum=min(words),maximum=max(words),median=median(words),mean=sum(words)/len(words)),
            word_allowance_excesses=sum(not a['output_word_allowance_met'] for a in answers),model_calls=sum(a['model_calls'] for a in answers),
            deterministic_constrained_realization=method=='HX-CONTRACT',
            answer_flexibility='not quantified; deterministic realization constrains wording/optional detail' if method=='HX-CONTRACT' else 'not quantified; stochastic prompted realization',
            generation_runtime_or_cost=None))
    return dict(schema='hexar-development-secondary-descriptive/v1',phase='development_only',confirmatory_N=0,alpha_consumed=0,
        agent_assessed=True,human_validated=False,independent_episodes=6,answers_never_independent_N=True,
        generation_design='original v11 nine independent generation attempts per method/episode; unique-request amendment not applied retrospectively',
        inference_performed=False,annotation_accuracy_qualified=False,methods=tables,
        physical_cause_flags='No separate physical-cause-specific label in this instrument; do not equate all overlicensed specificity with physical cause.',
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),score_path,method_path)})


if __name__=='__main__':
    report=summarize();exclusive_json(BASE/'development_secondary_summary_v11.json',report)
    for row in report['methods']:print(row['method'],row['useful_supported_answer_rate_bounds'],row['complete_required_unit_coverage'],row['word_count'])
