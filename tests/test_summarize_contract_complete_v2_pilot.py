import json

from summarize_contract_complete_v2_pilot import _claim_assignments, _effect, summarize


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


def test_summarize_keeps_primary_and_controls_separate_and_reports_tradeoffs(tmp_path):
    schedule = {"configurations": [
        {"order": 1, "run_id": "primary", "family": "persistent", "primary_eligible_family": True},
        {"order": 2, "run_id": "control", "family": "nominal", "primary_eligible_family": False},
    ]}
    result_root = tmp_path / "results"
    failure_root = tmp_path / "failures"
    pair_root = tmp_path / "pairs"
    for run_id, r_a in (("primary", True), ("control", False)):
        target = result_root / run_id
        target.mkdir(parents=True)
        report = {
            "status": "DEVELOPMENT_ONLY_COMPLETE",
            "passes": {
                "pass-1": {
                    "P": {"claim_a_complete_supported_communication": True,
                          "claim_b_substantive_assertion_error": False,
                          "fields": {"M": True, "Q": True, "O": True, "L": True}},
                    "R": {"claim_a_complete_supported_communication": r_a,
                          "claim_b_substantive_assertion_error": False,
                          "fields": {"M": True, "Q": True, "O": True, "L": r_a}},
                },
                "pass-2": {
                    "P": {"claim_a_complete_supported_communication": True,
                          "claim_b_substantive_assertion_error": False,
                          "fields": {"M": True, "Q": True, "O": True, "L": True}},
                    "R": {"claim_a_complete_supported_communication": True,
                          "claim_b_substantive_assertion_error": False,
                          "fields": {"M": True, "Q": True, "O": True, "L": True}},
                },
            },
        }
        (target / "development-summary.json").write_text(json.dumps(report), encoding="utf-8")
        pair_root.mkdir(exist_ok=True)
        pair = {
            "outputs": [
                {"condition": "P-contract", "text": "short answer"},
                {"condition": "R-contract", "text": "a somewhat longer answer"},
            ],
            "calls": [{"condition": "R-contract", "latency_ms": 1000, "usage": {"input_tokens": 10}}],
        }
        (pair_root / f"{run_id}.json").write_text(json.dumps(pair), encoding="utf-8")

    result = summarize(schedule, result_root, failure_root, pair_root)
    assert result["primary_reconciled_n"] == 1
    assert result["control_reconciled_n"] == 1
    assert result["claims"]["A"]["least_favourable"]["effect_p_minus_r"] == 0
    assert result["controls_descriptive"]["A"]["pass_1"]["effect_p_minus_r"] == 1
    assert result["two_pass_disagreement_counts"] == {"R:A": 1, "R:field:L": 1}
    assert result["communication_tradeoffs"]["P"]["median_words"] == 2
    assert result["communication_tradeoffs"]["R"]["median_latency_ms"] == 1000
