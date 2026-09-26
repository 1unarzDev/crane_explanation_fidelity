import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_raw_diagnostic_baseline_evidence import FORBIDDEN_KEYS  # noqa: E402
from recompute_command_motion_diagnostic_v2 import build_result as recompute_command  # noqa: E402
from reference_land_geometric import calculate as calculate_geometry  # noqa: E402
from reference_land_plan_geometry import calculate as calculate_plans  # noqa: E402


RAW_ROOT = ROOT / "data/robot_visible/dev/coverage-complete-v5-raw-baseline"
BT_XML = ROOT / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml"


def _load(name: str) -> dict:
    return json.loads((RAW_ROOT / name).read_text())


def _keys(value):
    if isinstance(value, dict):
        result = set(value)
        for item in value.values():
            result |= _keys(item)
        return result
    if isinstance(value, list):
        result = set()
        for item in value:
            result |= _keys(item)
        return result
    return set()


def test_raw_exports_contain_no_checked_diagnostic_or_evaluator_fields():
    paths = sorted(RAW_ROOT.glob("*.json"))
    assert len(paths) == 7
    for path in paths:
        document = json.loads(path.read_text())
        assert document["visibility"] == "robot_visible"
        assert not (FORBIDDEN_KEYS & _keys(document))
        assert "evaluator_only" not in json.dumps(document)


def test_command_tool_reconstructs_disposition_measurements_and_outcome():
    pairs = {
        "ccv5-persistent-004.json": (
            ROOT / "data/robot_visible/dev/mccv4-dev-004/command-motion-diagnostic-v3-low-speed.json"
        ),
        "ccv5-missing-odometry-004m.json": (
            ROOT
            / "data/robot_visible/dev/mccv4-dev-004-mask-no-odometry/command-motion-diagnostic-v3.json"
        ),
        "ccv5-compensation-005.json": (
            ROOT / "data/robot_visible/dev/mccv4-dev-005/command-motion-diagnostic-v3-low-speed.json"
        ),
    }
    for raw_name, checked_path in pairs.items():
        recomputed = recompute_command(_load(raw_name))["diagnostic_result"]
        checked = json.loads(checked_path.read_text())["diagnostic_result"]
        assert recomputed["disposition"] == checked["disposition"]
        assert recomputed["mechanism"] == checked["mechanism"]
        recomputed_measurements = {item["id"]: item for item in recomputed["measurements"]}
        checked_measurements = {item["id"]: item for item in checked["measurements"]}
        assert recomputed_measurements.keys() == checked_measurements.keys()
        for measurement_id, actual in recomputed_measurements.items():
            expected = checked_measurements[measurement_id]
            assert {
                key: value for key, value in actual.items() if key != "evidence_ids"
            } == {
                key: value for key, value in expected.items() if key != "evidence_ids"
            }
            # The retained masked export predates propagation of the already-declared
            # diagnostic-config hash into measurement provenance. Recalculation must
            # preserve every older ID and repair that omission from the raw source.
            assert set(expected["evidence_ids"]).issubset(actual["evidence_ids"])
            config_hash = _load(raw_name)["source"].get("diagnostic_config_sha256")
            if config_hash:
                assert f"diagnostic-config-sha256:{config_hash}" in actual["evidence_ids"]


def test_geometry_tools_reconstruct_independent_measurements_from_raw_evidence():
    cases = {
        "ccv5-geometry-001.json": "mccv4-dev-001",
        "ccv5-geometry-002.json": "mccv4-dev-002",
        "ccv5-geometry-003.json": "mccv4-dev-003",
        "ccv5-geometry-masked-001m.json": "mccv4-dev-001-mask-no-costmap-cells",
    }
    for raw_name, retained_id in cases.items():
        raw = _load(raw_name)
        configuration = raw["declared_diagnostic_configuration"]
        assert configuration["bt_xml_sha256"] == hashlib.sha256(BT_XML.read_bytes()).hexdigest()
        geometry = calculate_geometry(
            raw,
            BT_XML.read_bytes(),
            episode_id=raw["episode_id"],
            explicit_deadline_seconds=float(configuration["deadline_seconds"]),
        )
        retained = json.loads(
            (ROOT / f"data/evaluator_only/dev/{retained_id}/geometric-independent-reference-v1.json").read_text()
        )
        assert geometry["measurements"] == retained["measurements"]
        assert geometry["reference_findings"] == retained["reference_findings"]
        plans = calculate_plans(raw, episode_id=raw["episode_id"])
        retained_plans = json.loads(
            (ROOT / f"data/evaluator_only/dev/{retained_id}/plan-geometry-independent-reference-v1.json").read_text()
        )
        assert plans["measurements"] == retained_plans["measurements"]
        assert plans["reference_findings"] == retained_plans["reference_findings"]


def test_geometry_cell_payload_mask_is_real_and_hashes_are_retained():
    unmasked = _load("ccv5-geometry-001.json")["latestCostmapSnapshot"]
    masked = _load("ccv5-geometry-masked-001m.json")["latestCostmapSnapshot"]
    assert unmasked["data"]
    assert "data" not in masked
    assert masked["dataSha256"] == unmasked["dataSha256"]
    decoded_hash = hashlib.sha256(
        __import__("zlib").decompress(__import__("base64").b64decode(unmasked["data"]))
    ).hexdigest()
    assert decoded_hash == unmasked["dataSha256"]
