import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "summarize_diagnostic_development.py"
SPEC = importlib.util.spec_from_file_location("summarize_diagnostic_development", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rows():
    values = []
    for cluster in ("c1", "c2"):
        for condition in MODULE.CONDITIONS:
            success = condition in {"P", "T"}
            values.append(
                {
                    "response_id": f"{cluster}-{condition}",
                    "condition": condition,
                    "statistical_cluster_id": cluster,
                    "evidence_variant": "unmasked",
                    "question_id": "q",
                    "diagnosable": True,
                    "supported_diagnostic_success": success,
                    "material_error": False,
                    "causal_overclaim": False,
                    "unnecessary_abstention": not success,
                    "qualification_correct": True,
                    "required_units_total": 2,
                    "required_units_correct": 2 if success else 1,
                    "used_template_fallback": condition == "P",
                }
            )
    return values


def test_summary_is_clustered_and_explicitly_noninferential():
    result = MODULE.summarize(rows())
    assert result["responses"] == 8
    assert result["statistical_clusters"] == 2
    assert result["diagnosable_responses"] == 8
    assert result["ambiguous_responses"] == 0
    assert result["primary_candidate_p_vs_r"]["difference_method_minus_baseline"] == 1.0
    assert result["primary_candidate_p_vs_r"]["confidence_interval"] is None
    assert result["primary_candidate_p_vs_r"]["diagnosable_filter"] is True
    assert result["ambiguous_qualification_p_vs_r"]["difference_method_minus_baseline"] is None
    assert result["conditions"]["P"]["template_fallback_rate"] == 1.0
    assert result["power_planning_status"] == "NOT_AUTHORIZED_FROM_DEVELOPMENT_LABELS"


def test_summary_rejects_missing_condition_or_duplicate_response():
    incomplete = [row for row in rows() if row["condition"] != "N"]
    try:
        MODULE.summarize(incomplete)
    except ValueError as error:
        assert "R/P/T/N" in str(error)
    else:
        raise AssertionError("incomplete conditions were accepted")

    duplicate = rows()
    duplicate.append(dict(duplicate[0]))
    try:
        MODULE.summarize(duplicate)
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate response was accepted")


def mixed_rows():
    values = []
    for condition in MODULE.CONDITIONS:
        values.append(
            {
                "response_id": f"supported-{condition}",
                "condition": condition,
                "statistical_cluster_id": "shared-cluster",
                "evidence_variant": "supported",
                "question_id": "q1",
                "diagnosable": True,
                "supported_diagnostic_success": condition in {"P", "T"},
                "material_error": False,
                "causal_overclaim": False,
                "unnecessary_abstention": False,
                "qualification_correct": True,
                "required_units_total": 2,
                "required_units_correct": 2,
                "used_template_fallback": condition == "P",
            }
        )
        values.append(
            {
                "response_id": f"ambiguous-{condition}",
                "condition": condition,
                "statistical_cluster_id": "shared-cluster",
                "evidence_variant": "missing-motion",
                "question_id": "q1",
                "diagnosable": False,
                "supported_diagnostic_success": False,
                "material_error": False,
                "causal_overclaim": False,
                "unnecessary_abstention": False,
                "qualification_correct": condition != "N",
                "required_units_total": 2,
                "required_units_correct": 2,
                "used_template_fallback": condition == "P",
            }
        )
    return values


def test_summary_separates_diagnosable_success_from_ambiguous_qualification():
    result = MODULE.summarize(mixed_rows())

    assert result["responses"] == 8
    assert result["statistical_clusters"] == 1
    assert result["diagnosable_responses"] == 4
    assert result["ambiguous_responses"] == 4
    assert result["conditions"]["P"]["supported_diagnostic_success_rate"] == 1.0
    assert result["conditions"]["R"]["supported_diagnostic_success_rate"] == 0.0
    assert result["conditions"]["P"]["ambiguous_qualification_correct_rate"] == 1.0
    assert result["conditions"]["N"]["ambiguous_qualification_correct_rate"] == 0.0
    assert result["primary_candidate_p_vs_r"]["difference_method_minus_baseline"] == 1.0
    assert result["ambiguous_qualification_p_vs_r"]["difference_method_minus_baseline"] == 0.0


def test_summary_rejects_missing_diagnosability_label():
    values = mixed_rows()
    values[0].pop("diagnosable")

    try:
        MODULE.summarize(values)
    except ValueError as error:
        assert "diagnosable" in str(error)
    else:
        raise AssertionError("missing diagnosable label was accepted")
