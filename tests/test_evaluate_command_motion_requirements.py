import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_nested_evidence_conditions import build_conditions  # noqa: E402
from evaluate_command_motion_requirements import evaluate  # noqa: E402
from maximal_supported_diagnosis import diagnose  # noqa: E402
from normalize_command_motion_evidence import normalize  # noqa: E402

ONTOLOGY = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
DIAGNOSTIC = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-042/command-motion-diagnostic-v3.json").read_text())


def conditions():
    source = normalize(DIAGNOSTIC, configuration_id="cluster-042", question="What is supported?")
    spec = {
        "schema": "crane-nested-evidence-mask-spec/v1", "ladder_id": "test-ladder",
        "condition_builder_id": "builder", "condition_builder_version": "v1",
        "condition_builder_sha256": "1" * 64, "source_configuration_sha256": "2" * 64,
        "runtime_manifest_sha256": "3" * 64,
        "conditions": [
            {"condition_id": "e2", "level_index": 0,
             "removed_json_pointers": ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
             "mask_id": "no-odom", "mask_version": "v1"},
            {"condition_id": "e3", "level_index": 1, "removed_json_pointers": [],
             "mask_id": None, "mask_version": None},
        ],
    }
    return build_conditions(source, spec)


QUESTION = {"question_id": "command-motion-v1", "failure_premise": True,
            "required_mechanism_families": ["command_motion"]}


def test_masked_odometry_blocks_discrepancy_but_retains_command_observation():
    masked, full = conditions()
    facts = evaluate(ONTOLOGY, masked, QUESTION)
    result = diagnose(ONTOLOGY, masked, facts)
    assert "claim-command-observed" in result["approved_claim_ids"]
    assert "claim-command-motion-discrepancy" not in result["approved_claim_ids"]
    assert "req-odometry-stream-valid" in result["missing_requirement_ids"]

    full_facts = evaluate(ONTOLOGY, full, QUESTION)
    full_result = diagnose(ONTOLOGY, full, full_facts)
    assert "claim-command-motion-discrepancy" in full_result["approved_claim_ids"]
    assert "claim-external-obstruction" not in full_result["approved_claim_ids"]


def test_requirement_support_is_role_bound_not_merely_flat_id_visible():
    _, full = conditions()
    facts = evaluate(ONTOLOGY, full, QUESTION)
    recovery = next(item for item in facts["requirement_evaluations"]
                    if item["requirement_id"] == "req-recovery-trace-valid")
    assert set(recovery["support_references"]) == {"recovery-trace", "source-anchors"}
