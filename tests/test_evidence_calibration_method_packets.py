import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_method_packets import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402

SPEC = importlib.util.spec_from_file_location("fixtures", ROOT / "tests/test_evidence_calibration_reference.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)


def entry():
    return next(item for item in FIXTURES.bundle()["conditions"]
                if item["condition"]["condition_id"] == "e3")


def contract(current):
    evidence_ids = current["condition"]["available_evidence_ids"]
    return {
        "contract_id": "method-parity-development-v1",
        "ordinary_runtime_presentation": "Action aborted after recovery; command and odometry streams are retained.",
        "presentation_evidence_ids": evidence_ids,
        "source_assets": [{"asset_id": "nav2-controller-config", "version": "v1", "sha256": "1" * 64}],
        "primitive_tools": [{"asset_id": "window-statistics", "version": "v1", "sha256": "2" * 64}],
        "question_instruction": "Explain only what this robot-visible evidence supports.",
        "contract_assets": [{"asset_id": "claim-contracts", "version": "v1-development", "sha256": "3" * 64}],
    }


def test_b2_b3_b4_share_evidence_source_and_primitive_tool_basis():
    current = entry()
    output = build(current, contract(current))
    packets = {item["method_id"]: item for item in output["method_packets"]}
    assert set(packets) == {"B0", "B1", "B2", "B3", "B4"}
    for identifier in ("B2", "B3", "B4"):
        packet = packets[identifier]
        assert packet["evidence_basis_sha256"] == output["evidence_basis_sha256"]
        assert canonical_sha256(packet["source_assets"]) == output["b2_b4_source_assets_sha256"]
        assert canonical_sha256(packet["primitive_tools"]) == output["b2_b4_primitive_tools_sha256"]
    assert packets["B3"]["contract_assets"] == packets["B4"]["contract_assets"]
    assert not packets["B3"]["final_claim_verification"]
    assert packets["B4"]["final_claim_verification"]
    assert output["independent_episode_increment"] == 1
    assert all(item["physical_sample_increment"] == 0 for item in packets.values())


def test_builder_rejects_incomplete_raw_presentation_inventory():
    current = entry()
    specification = contract(current)
    specification["presentation_evidence_ids"] = specification["presentation_evidence_ids"][:-1]
    with pytest.raises(ValueError, match="same evidence inventory"):
        build(current, specification)


def test_builder_fails_closed_on_nested_evaluator_truth():
    current = entry()
    current["method_packet"]["nested"] = {"physical_truth": "obstruction"}
    current["condition"]["method_packet_sha256"] = canonical_sha256(current["method_packet"])
    with pytest.raises(ValueError, match="evaluator-only"):
        build(current, contract(current))
