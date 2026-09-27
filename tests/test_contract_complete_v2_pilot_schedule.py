import json
from pathlib import Path

from analysis.build_contract_complete_v2_pilot_schedule import build, digest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/explicit-causal-restraint-successor-v1-schedule.json"


def test_schedule_uses_only_untouched_fixed_suffix():
    source = json.loads(SOURCE.read_text())
    result = build(source, source_sha256=digest(SOURCE))

    assert result["counts"] == {"total": 19, "primary": 15, "controls": 4}
    assert result["alpha"] == 0.0
    assert result["confirmation_activation"] == "PROHIBITED"
    assert result["inspected_excluded_configuration"]["run_id"] == "cr-pilot-001"
    assert [row["order"] for row in result["configurations"]] == list(range(2, 21))
    assert len({row["layout_id"] for row in result["configurations"]}) == 19
    assert all(row["run_id"] != "cr-pilot-001" for row in result["configurations"])
