import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "analysis" / "plan_diagnostic_pilot_power.py"
SPEC = importlib.util.spec_from_file_location("plan_diagnostic_pilot_power", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def selection_fixture(tmp_path: Path) -> dict:
    sensitivity = tmp_path / "sensitivity.json"
    write_json(sensitivity, {"status": "DESIGN_SENSITIVITY"})
    inventory = tmp_path / "inventory.json"
    write_json(
        inventory,
        {
            "packets": [
                {
                    "name": "first",
                    "statistical_cluster_id": "c1",
                    "evidence_variant": "unmasked",
                },
                {
                    "name": "first-mask",
                    "statistical_cluster_id": "c1",
                    "evidence_variant": "masked",
                },
                {
                    "name": "second",
                    "statistical_cluster_id": "c2",
                    "evidence_variant": "unmasked",
                },
            ]
        },
    )
    return {
        "schema": "crane-diagnostic-pilot-primary-endpoints/v1",
        "labels_inspected_when_declared": False,
        "annotation_inventory": str(inventory),
        "annotation_inventory_sha256": hashlib.sha256(inventory.read_bytes()).hexdigest(),
        "design_sensitivity": str(sensitivity),
        "design_sensitivity_sha256": hashlib.sha256(sensitivity.read_bytes()).hexdigest(),
        "selected": [
            {"packet_name": "first", "statistical_cluster_id": "c1", "evidence_variant": "unmasked"},
            {"packet_name": "second", "statistical_cluster_id": "c2", "evidence_variant": "unmasked"},
        ],
        "excluded": [{"packet_name": "first-mask", "reason": "mask"}],
        "planning_rule": {"fixed_design_minimum_clusters_for_80_percent_power": 92},
    }


def rows() -> list[dict]:
    output = []
    for cluster, p_success, r_success in (("c1", True, False), ("c2", True, True)):
        for condition in ("R", "P", "T", "N"):
            success = p_success if condition == "P" else r_success if condition == "R" else True
            output.append(
                {
                    "response_id": f"{cluster}-{condition}",
                    "statistical_cluster_id": cluster,
                    "evidence_variant": "unmasked",
                    "condition": condition,
                    "diagnosable": True,
                    "supported_diagnostic_success": success,
                }
            )
        # A mask exists in joined data but is not another primary observation.
        if cluster == "c1":
            for condition in ("R", "P", "T", "N"):
                output.append(
                    {
                        "response_id": f"mask-{condition}",
                        "statistical_cluster_id": cluster,
                        "evidence_variant": "masked",
                        "condition": condition,
                        "diagnosable": False,
                        "supported_diagnostic_success": False,
                    }
                )
    return output


def test_uses_one_predeclared_endpoint_per_cluster_and_never_lowers_fixed_target(tmp_path):
    result = MODULE.plan(rows(), selection_fixture(tmp_path))
    assert result["selected_endpoints_analyzed"] == 2
    assert result["paired_counts"] == {
        "both_success": 1,
        "p_only_success": 1,
        "r_only_success": 0,
        "neither_success": 0,
    }
    assert result["raw_discordance"]["direction"] == "FAVORS_P"
    assert result["observed_direction_favors_p"] is True
    assert result["superiority_freeze_authorized"] is False
    assert result["pilot_informed_minimum_not_below_fixed_design"] >= 92
    assert all(item["evidence_variant"] == "unmasked" for item in result["endpoints"])


def test_missing_quarantined_endpoint_is_reported_not_replaced(tmp_path):
    selected_rows = [row for row in rows() if row["statistical_cluster_id"] == "c1"]
    result = MODULE.plan(selected_rows, selection_fixture(tmp_path))
    assert result["selected_endpoints_analyzed"] == 1
    assert result["selected_endpoints_missing_after_quarantine"] == ["second"]


def test_rejects_post_label_or_nonpartitioned_selection(tmp_path):
    selection = selection_fixture(tmp_path)
    selection["labels_inspected_when_declared"] = True
    with pytest.raises(ValueError, match="pre-label"):
        MODULE.plan(rows(), selection)

    selection = selection_fixture(tmp_path)
    selection["excluded"] = []
    with pytest.raises(ValueError, match="partition"):
        MODULE.plan(rows(), selection)
