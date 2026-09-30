#!/usr/bin/env python3
"""Present completed frozen results; no new endpoint, scoring or inference."""
import json
from pathlib import Path

from audit_release import ROOT, sha, write
from verify_v3 import V3, study

METHODS = ('HX-ORIGINAL', 'HX-PROMPT', 'HX-CONTRACT')
CONDITIONS = ('intact', 'irrelevant_removal', 'diagnostic_removal')


def percent(value):
    return 'unavailable' if value is None else f'{100 * value:.1f}%'


def bounds(values, points=False):
    if values is None:
        return 'unavailable'
    if points:
        return f'[{100 * values[0]:+.1f}, {100 * values[1]:+.1f}] percentage points'
    return f'{100 * values[0]:.1f}–{100 * values[1]:.1f}%'


def main():
    study()
    base = V3 / 'reserved'
    result = json.loads((base / 'results.json').read_text())
    causal = json.loads((base / 'causal_reporting.json').read_text())
    annotation = json.loads((base / 'annotation/annotation_summary.json').read_text())
    accounting = json.loads((base / 'causal_reporting_accounting_audit.json').read_text())
    assert accounting['passed'] and accounting['report_sha256'] == sha(base / 'causal_reporting.json')
    assert result['independent_recordings'] == causal['independent_recordings'] == 12
    assert result['alpha_consumed'] == causal['alpha_consumed'] == 0
    assert result['p_value'] is None and not result['statistically_supported_improvement_claim']
    values = result['methods']
    assert all(values[m]['n_jobs'] == causal['methods'][m]['n_jobs'] == 108 for m in METHODS)
    out = base / 'paper'
    out.mkdir(exist_ok=True)
    lines = [
        '| Method | Useful supported success¹ | Required-unit coverage² | Unsupported material¹ | Unsupported causal relation¹ | Intact success¹ | Median words |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for method in METHODS:
        value = values[method]
        lines.append(f"| {method} | {bounds(value['fixed_denominator_bounds'])} | {percent(value['coverage'])} | "
                     f"{bounds(value['unsupported_material_fixed_denominator_bounds'])} | "
                     f"{bounds(causal['methods'][method]['fixed_denominator_bounds'])} | "
                     f"{bounds(value['evidence_success_bounds']['intact'])} | {value['median_answer_words']:g} |")
    lines.extend([
        '',
        '¹ Full declared denominator:108 answers/method, grouped by12 physical recordings in six known families. Ranges are unknown-label/role bounds, not confidence intervals. Intact denominator:36 answers/method.',
        '² Mean compact required-unit coverage among finalized agent assessments; not exhaustive information coverage. Unsupported material includes noncausal facts. Causal roles are independently blind-coded developer judgments, not qualified/human-validated; qualified support labels are unchanged.',
        '',
        f"Registered contract-minus-prompt full-cohort effect bounds: **{bounds(result['primary_full_cohort_effect_bounds'], True)}**. "
        f"Complete principal recording pairs:{result['paired_complete_recordings']}/12. No confirmatory alpha or p-value.",
    ])
    (out / 'result_table.md').write_text('\n'.join(lines) + '\n')
    operations = ['| Method | Median realization ms | Model calls | Template | Fallback | Blanket abstention² | Required-unit control consistency³ |',
                  '|---|---:|---:|---:|---:|---:|---:|']
    responses = [json.loads(p.read_text()) for p in (base / 'responses').glob('*.json')]
    for method in METHODS:
        value = values[method]
        model_calls = sum(r['model_calls'] for r in responses if r['method'] == method)
        operations.append(f"| {method} | {value['median_runtime_ms']:.2f} | {model_calls} | "
                          f"{percent(value['template_rate'])} | {percent(value['fallback_rate'])} | "
                          f"{percent(value['unnecessary_blanket_abstention_rate'])} | "
                          f"{percent(value['irrelevant_required_semantic_consistency'])} |")
    operations.extend(['', 'Timings measure realization from prebuilt packets, not whole replay/extraction latency or pure model compute. Hosted cost/immutable weights are unavailable.',
                       '² Finalized assessments; detects limitation-only blanket refusal missing required units, not all unnecessary hedging. ³ Endpoint and required-unit equality among complete intact/control pairs; selected packets are byte-identical. No complete semantic invariance claim.'])
    (out / 'operations.md').write_text('\n'.join(operations) + '\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure, axis = plt.subplots(figsize=(7.0, 3.6))
    width = .24
    for i, (method, color) in enumerate(zip(METHODS, ('#818896', '#dc9b35', '#277d86'))):
        ranges = [values[method]['evidence_success_bounds'][condition] for condition in CONDITIONS]
        axis.bar([j + (i - 1) * width for j in range(3)], [100 * b[0] for b in ranges], width,
                 label=method, color=color,
                 yerr=[[0] * 3, [100 * (b[1] - b[0]) for b in ranges]], capsize=3)
    axis.set(ylim=(0, 108), ylabel='Useful supported answers (%)', xticks=range(3),
             xticklabels=['Intact', 'Irrelevant removal', 'Diagnostic removal'])
    axis.legend(loc='upper center', ncol=3, fontsize=8)
    figure.text(.5, .025, '12 physical recordings · 6 known families · 36 answers/method/evidence level\n'
                'Bars: fixed-denominator lower bounds; whiskers: missing-score upper bounds, not CIs.',
                ha='center', fontsize=8)
    figure.tight_layout(rect=(0, .09, 1, 1))
    for extension in ('svg', 'png'):
        figure.savefig(out / f'evidence_results.{extension}', dpi=200)
    plt.close(figure)
    complete_mean = 'unavailable' if result['primary_effect'] is None else f"{100 * result['primary_effect']:+.1f} percentage points"
    draft = f"""# External validation on released physical robot executions

We added CRANE's pinned evidence-contract core to HEXAR, an independently developed modular explainer evaluated on released TIAGo executions (Love et al., arXiv:2601.03070). Recalculating the released majority-label metric gives 167/180 overall and 49/54 navigation queries for historical HEXAR; those human labels are separate from our new support task. We selected all six navigation families, split 18 recordings before tuning into six development and 12 reserved recordings, and prospectively froze three original questions crossed with intact, irrelevant-removal and diagnostic-removal evidence. Removal precedes state/diagnostic derivation, uses fresh state, preserves execution outcomes and represents missing information as unknown. Independent packet-specific references precede answers; scenario truth and authors' answers never enter methods. Native ROS Humble replay verified 3,422 selected inputs and state/window/prompt equality on one development recording under traced receipt-clock instrumentation; later deterministic component replay uses bag receipt times.

The principal comparison is HX-CONTRACT versus a strengthened HX-PROMPT sharing primitive evidence, availability, source/public requirements and a three-sentence/60-word allowance. Model-backed conditions request the same hosted gpt-6-sol/high configuration; immutable hosted weights and historical phi4 identity are unavailable. HX-CONTRACT deterministically replaces component realization through the existing core, making no model calls; it is not a post-hoc verifier of unrestricted prose. The sole registered endpoint is recording-average useful-supported-answer success over nine conditions: useful outcome plus one available bounded diagnostic, appropriate unavailable-conclusion scope and no material unsupported assertion. Valid extras are allowed and blanket refusal fails.

All 324 reserved answers were generated without failures/retries. Qualified agent support assessment finalized {annotation['qualified_completed']}/324 answers, with {annotation['technical_failures']} retained technical failures; unscored answers remain unknown. The full-cohort contract-minus-prompt effect bounds are {bounds(result['primary_full_cohort_effect_bounds'], True)}. There are {result['paired_complete_recordings']}/12 complete recording pairs; their conditional mean is {complete_mean}, descriptive recording t95 {bounds(result['descriptive_recording_t95'], True)}. Strict complete-cohort six-family sensitivity is {bounds(result['descriptive_family_t95'], True)}. These descriptive intervals do not establish statistically supported superiority; allocated/consumed alpha is zero. Tables and evidence-level figure retain baseline ties, unknowns and optional-detail/resource tradeoffs. Atom extraction and causal-role coding are unqualified developer assessments; support is agent-assessed, not human-validated. Atomic-label agreement is {percent(result['annotation']['claim_agreement'])}; pass-specific missing-label bounds remain in the retained report.

This finite public known-family cohort does not establish unseen-mechanism transfer, human trust or full HEXAR replacement. Logs/AMCL estimates do not supply raw scan/path/costmap geometry or a unique physical cause. One-recording instrumented native component parity does not establish historical clocks or full-system selector/lifecycle equivalence. The strengthened prompt's performance must remain visible; deterministic rendering restricts lexical flexibility and supplemental detail, and the comparison does not isolate contracts from constrained realization. The supported contribution is an audited application of the same evidence-calibration principle to an independent explainer on released physical executions, with a transparent bounded comparison.
"""
    (out / 'PAPER_SECTION_DRAFT.md').write_text(draft)
    write(out / 'presentation_provenance.json', {
        'results_sha256': sha(base / 'results.json'), 'causal_sha256': sha(base / 'causal_reporting.json'),
        'renderer_sha256': sha(Path(__file__)), 'new_endpoint_or_inference': False,
        'final_root_review_required': True,
    })
    print('FROZEN_RESULT_PRESENTATION_READY_FOR_ROOT_REVIEW')


if __name__ == '__main__':
    main()
