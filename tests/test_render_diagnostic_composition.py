import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "render_diagnostic_composition", ROOT / "analysis/render_diagnostic_composition.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_renderer_leads_with_diagnosis_and_retains_scope_limit():
    certificate = {
        "schema": "crane-diagnostic-composition-certificate/v1",
        "status": "composed",
        "answer_plan": {
            "language_ready": True,
            "missing_required_unit_ids": [],
            "primary_claim": "A command-to-motion discrepancy is established.",
            "missing_discriminators": ["actuator_feedback"],
            "scope_limit": "Unmodeled mechanisms remain possible.",
            "units": [
                {"unit_id": "d", "role": "diagnosis", "text": "Measured response was low."},
                {"unit_id": "e", "role": "evidence", "text": "Median speed was 0.01 m/s."},
                {"unit_id": "l", "role": "limit", "text": "The unique cause is unresolved."},
            ],
        },
    }
    text = MODULE.render(certificate)
    assert text.startswith("Diagnosis:\n- Measured response was low.")
    assert "Decisive evidence:\n- Median speed was 0.01 m/s." in text
    assert "The unique cause is unresolved." in text
    assert "Unmodeled mechanisms remain possible." in text
    assert "Missing discriminators: actuator_feedback." in text


def test_renderer_rejects_evidence_problem():
    try:
        MODULE.render(
            {
                "schema": "crane-diagnostic-composition-certificate/v1",
                "status": "evidence_problem",
            }
        )
    except ValueError as error:
        assert "evidence-problem" in str(error)
    else:
        raise AssertionError("renderer accepted evidence-problem certificate")


def test_renderer_rejects_incomplete_checked_answer_plan():
    try:
        MODULE.render(
            {
                "schema": "crane-diagnostic-composition-certificate/v1",
                "status": "composed",
                "answer_plan": {
                    "language_ready": False,
                    "missing_required_unit_ids": ["decisive-measurement"],
                    "units": [],
                },
            }
        )
    except ValueError as error:
        assert "not language-ready" in str(error)
        assert "decisive-measurement" in str(error)
    else:
        raise AssertionError("renderer accepted an incomplete checked answer plan")
