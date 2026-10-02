import json
from pathlib import Path
import pytest


def test_maximum_discordance_sensitivity_is_balanced_and_matches_exact_enumeration():
    path = Path(__file__).resolve().parents[2] / 'manifests/hexar_external/confirmatory_v1/maximum_variance_power_sensitivity_v1.json'
    report = json.loads(path.read_text())
    assert report['selected_n'] is None and report['selected_effect_floor'] is None
    assert report['no_semantic_data_read'] and report['confirmatory_N'] == 0
    assert all(p <= .01 for p in report['homogeneous_null_sizes'].values())
    for row in report['rows']:
        assert row['n'] % 6 == 0 and row['family_n'] == [row['n']//6]*6
        assert sum(row['family_effects'])/6 == pytest.approx(row['mapped_endpoint_average_effect'])
        assert all(0 <= q <= 1 for q in row['family_favorable_probabilities'])
        if row['exact_homogeneous_power'] is not None:
            assert abs(row['simulated_power'] - row['exact_homogeneous_power']) <= 5*row['simulation_standard_error'] + 1/report['replications']
    point = next(r for r in report['rows'] if r['regime'] == 'homogeneous'
                 and r['n'] == 1296 and r['mapped_endpoint_average_effect'] == .1)
    assert point['exact_homogeneous_power'] == pytest.approx(.4185177041214769)
