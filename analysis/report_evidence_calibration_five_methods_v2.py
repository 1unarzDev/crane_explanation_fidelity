#!/usr/bin/env python3
"""Development reporting layer for bound five-method analysis; no endpoint or alpha selection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_evidence_calibration import analyze
from analyze_evidence_calibration_five_methods import analyze_five_methods, _project_pair, SECONDARY
from evidence_calibration_io import canonical_sha256, canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / 'manifests/study/evidence-calibration-five-method-comparisons-v1-development.json'


def report(data: dict, plan: dict, declaration: dict) -> dict:
    # Exact current declaration, including treatment, multiplicity and scientific boundaries.
    # This is a development binding; selecting final P11 procedures remains a separate action.
    if canonical_sha256(declaration) != canonical_sha256(json.loads(DECLARATION.read_text())):
        raise ValueError('report requires the exact bound development comparison declaration')
    original = analyze_five_methods(data, plan, declaration)
    comparisons = {}
    for comparator in ('B2', *SECONDARY):
        result = original['primary_b2_vs_b4'] if comparator == 'B2' else analyze(_project_pair(data, comparator), plan)
        paired = result['paired_primary']
        metrics = result['method_metrics']
        n = result['independent_episode_count']
        interval = paired['whole_episode_bootstrap_confidence_interval']
        effect = paired['b4_minus_b2_risk_difference']
        discordances = paired['b2_only_failure'] + paired['b4_only_failure']
        controls = {}
        for family, row in result['nonprimary_family_descriptives'].items():
            count = row['independent_episode_count']
            controls[family] = {
                'role': row['role'], 'independent_episode_count': count,
                'method_failures': {comparator: row['B2_episode_failures'], 'B4': row['B4_episode_failures']},
                'method_failure_rates': {
                    comparator: row['B2_episode_failures']/count if count else None,
                    'B4': row['B4_episode_failures']/count if count else None},
                'pooled_into_primary': False, 'inferential_test_performed': False}
        comparisons[comparator] = {
            'comparator': comparator, 'treatment': 'B4',
            'comparison_role': 'primary_candidate' if comparator == 'B2' else 'secondary_exploratory',
            'independent_paired_episode_count': n,
            'method_failures': {comparator: metrics['B2']['primary_failures'], 'B4': metrics['B4']['primary_failures']},
            'method_failure_rates': {comparator: metrics['B2']['primary_failure_rate'], 'B4': metrics['B4']['primary_failure_rate']},
            'paired_episode_counts': {'neither_failure': paired['neither_failure'],
                'comparator_only_failure': paired['b2_only_failure'], 'b4_only_failure': paired['b4_only_failure'],
                'both_failure': paired['both_failure']},
            'b4_minus_comparator_absolute_risk_difference': effect,
            'effect_direction': 'B4_LOWER_FAILURE_RISK' if effect < 0 else 'B4_HIGHER_FAILURE_RISK' if effect > 0 else 'OBSERVED_RISK_TIE',
            'whole_episode_percentile_bootstrap_interval': {
                'bounds': interval, 'nominal_confidence_level': 1-plan['alpha'],
                'replicates': plan['bootstrap_replicates'], 'seed': plan['bootstrap_seed'],
                'resampling_unit': 'episode_configuration',
                'multiplicity_adjusted': False,
                'zero_is_in_interval': interval[0] <= 0 <= interval[1],
                'degenerate': interval[0] == interval[1],
                'sampling_uncertainty_certified_by_bootstrap_when_no_discordances': False,
                'interpretation_note': 'No observed episode discordances; a degenerate empirical bootstrap interval is not evidence of population equivalence.'
                    if discordances == 0 else 'Pointwise development interval; exact procedure and level remain subject to prospective P11 binding.'},
            'exact_mcnemar_two_sided_p': paired['exact_mcnemar_two_sided_p'],
            'holm_adjusted_p_across_three_secondary_method_contrasts': None if comparator == 'B2' else
                original['secondary_method_family'][comparator]['holm_adjusted_p_across_three_method_contrasts'],
            'p_value_correction_scope': 'single_candidate_primary_test' if comparator == 'B2' else 'B4_VS_B0_B1_B3',
            'useful_coverage': {comparator: {
                    key: metrics['B2'][key] for key in ('sdr_numerator','sdr_denominator','supported_diagnostic_recall','coverage_floor','coverage_floor_met')},
                'B4': {key: metrics['B4'][key] for key in ('sdr_numerator','sdr_denominator','supported_diagnostic_recall','coverage_floor','coverage_floor_met')}},
            'primary_family_counts': result['primary_family_counts'],
            'primary_family_weighting': result['primary_family_weighting'],
            'controls_and_secondary_geometry': controls,
            'confirmatory_rejection_decision': None,
            'equivalence_claim_authorized': False,
            'inconclusive_or_unfavorable_result_omitted': False}
    return {'schema': 'crane-five-method-report/v2-development',
        'disposition': 'DEVELOPMENT_ONLY_REPORTING_NOT_P11_FROZEN',
        'input_sha256':canonical_sha256(data), 'analysis_plan_sha256':canonical_sha256(plan),
        'comparison_declaration_sha256':canonical_sha256(declaration),
        'original_v1_analysis_sha256':canonical_sha256(original),
        'comparisons':comparisons,
        'independent_unit':'episode_configuration',
        'secondary_discovery_alpha_allocated':0.0,
        'all_four_declared_contrasts_reported':True,
        'missingness_or_endpoint_mapping_selected':False,
        'model_calls_authorized':False, 'p11_authorized':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--comparison-declaration',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('existing report output cannot be replaced')
    result=report(json.loads(args.results.read_text()),json.loads(args.plan.read_text()),json.loads(args.comparison_declaration.read_text()))
    with args.output.open('xb') as handle:handle.write(canonical_json_bytes(result)+b'\n')


if __name__=='__main__':main()
