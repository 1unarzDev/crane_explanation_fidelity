import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import audit_evidence_calibration_b2_requests as requests


def test_all_b2_requests_preserve_original_cohort_and_staged_identity():
    result = requests.build()
    assert result == json.loads((ROOT / requests.OUTPUT).read_text())
    assert result["inspected_development_episode_count"] == 16
    assert result["b2_request_count"] == 60
    assert "cm-land-conf-042" in {row["source_run_id"] for row in result["conditions"]}
    assert result["harness_permissions_enforced"] is False
    assert result["full_tool_surface_bound"] is False
    assert result["model_calls_authorized"] is False
    assert result["semantic_method_outputs_generated"] == 0
    assert result["confirmation_independent_n"] == result["replication_independent_n"] == 0
    assert all(row["token_fit"] is None for row in result["conditions"])
