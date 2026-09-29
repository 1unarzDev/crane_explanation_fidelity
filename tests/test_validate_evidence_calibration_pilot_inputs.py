import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from evidence_calibration_io import canonical_json_bytes  # noqa: E402
from validate_evidence_calibration_pilot_inputs import validate  # noqa: E402

PILOT = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
SCHEDULE = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())


def test_all_fixed_pilot_inputs_dry_build_and_b4_outputs_are_deterministic():
    first = validate(ROOT, PILOT, SCHEDULE)
    second = validate(ROOT, PILOT, SCHEDULE)
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["independent_episode_count"] == 16
    assert first["within_episode_condition_count"] == first["b4_outputs_generated"] == 60
    assert first["b2_model_outputs_generated"] == 0
    assert first["human_annotations_collected"] == 0
    assert all(item["b4_audit_status"] == "ACCEPTED"
               for episode in first["episodes"] for item in episode["diagnostics"])
    serialized = canonical_json_bytes(first).lower()
    assert b"evaluator" not in serialized and b"physical_truth" not in serialized


def test_weaker_conditions_do_not_emit_full_discrepancy():
    output = validate(ROOT, PILOT, SCHEDULE)
    for episode in output["episodes"]:
        for item in episode["diagnostics"][:-1]:
            if item["condition_id"].endswith(("E0", "E1", "E2")) and \
                    len(episode["diagnostics"]) == 4:
                assert "claim-command-motion-discrepancy" not in item["approved_claim_ids"]
