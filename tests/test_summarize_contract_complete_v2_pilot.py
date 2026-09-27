from summarize_contract_complete_v2_pilot import _claim_assignments, _effect


def _report(a_p, a_r, b_p, b_r):
    return {"passes": {
        "pass-1": {"P": {"claim_a_complete_supported_communication": a_p[0], "claim_b_substantive_assertion_error": b_p[0]},
                   "R": {"claim_a_complete_supported_communication": a_r[0], "claim_b_substantive_assertion_error": b_r[0]}},
        "pass-2": {"P": {"claim_a_complete_supported_communication": a_p[1], "claim_b_substantive_assertion_error": b_p[1]},
                   "R": {"claim_a_complete_supported_communication": a_r[1], "claim_b_substantive_assertion_error": b_r[1]}},
    }}


def test_least_favourable_mapping_is_adverse_to_p_for_both_claims():
    report = _report((True, False), (True, False), (True, False), (True, False))
    assert _claim_assignments(report, "A") == {"least_p": 0, "least_r": 1, "most_p": 1, "most_r": 0}
    assert _claim_assignments(report, "B") == {"least_p": 0, "least_r": 1, "most_p": 1, "most_r": 0}


def test_effect_reports_discordance_and_ties():
    rows = [
        {"least_p": 1, "least_r": 0},
        {"least_p": 0, "least_r": 1},
        {"least_p": 1, "least_r": 1},
    ]
    result = _effect(rows, "least")
    assert result["effect_p_minus_r"] == 0
    assert result["p_only_favourable"] == 1
    assert result["r_only_favourable"] == 1
    assert result["ties"] == 1
