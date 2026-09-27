from __future__ import annotations

import hashlib
import json
from pathlib import Path

from analysis.build_contract_complete_pilot_schedule import build


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v6.json"
CLOSED_SCHEDULE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "land-command-motion-physical-schedule-v1.json"
)


def inputs() -> tuple[dict, dict, str]:
    raw = CATALOG.read_bytes()
    return json.loads(raw), json.loads(CLOSED_SCHEDULE.read_text()), hashlib.sha256(raw).hexdigest()


def test_fresh_pilot_uses_only_unassigned_nonqualification_layouts() -> None:
    catalog, closed, digest = inputs()
    result = build(catalog, closed, digest)
    runs = result["runs"]
    closed_layouts = {
        run["layout_id"]
        for cohort in closed["cohorts"]
        for run in cohort["runs"]
    }

    assert result["status"] == "FROZEN_DEVELOPMENT_PILOT_BEFORE_CAPTURE"
    assert len(runs) == 19
    assert len({run["layout_id"] for run in runs}) == 19
    assert not ({run["layout_id"] for run in runs} & closed_layouts)
    assert "diagnostic-command-motion-confirmation-reserve-connected-detour-001" not in {
        run["layout_id"] for run in runs
    }
    assert all(run["study_role"] == "fresh-development-pilot" for run in runs)


def test_fresh_pilot_freezes_diagnosable_and_control_quotas() -> None:
    catalog, closed, digest = inputs()
    result = build(catalog, closed, digest)
    runs = result["runs"]

    counts = {
        family: sum(run["family"] == family for run in runs)
        for family in {
            "persistent_command_motion_discrepancy",
            "measured_response_recovery",
            "missing_decisive_or_ambiguous_evidence",
            "nominal_false_premise_or_irrelevant_obstacle",
        }
    }
    assert counts == {
        "persistent_command_motion_discrepancy": 8,
        "measured_response_recovery": 7,
        "missing_decisive_or_ambiguous_evidence": 2,
        "nominal_false_premise_or_irrelevant_obstacle": 2,
    }
    assert result["primary_diagnosable_count"] == 15
    assert result["control_count"] == 4
    assert {run["geometry_mechanism"] for run in runs} == {
        "connected-detour",
        "nominal-clear-route",
    }


def test_fresh_pilot_has_unique_isolated_execution_identities() -> None:
    catalog, closed, digest = inputs()
    runs = build(catalog, closed, digest)["runs"]

    assert [run["order"] for run in runs] == list(range(1, 20))
    assert len({run["run_id"] for run in runs}) == 19
    assert len({run["cluster_id"] for run in runs}) == 19
    assert len({run["ros_domain_id"] for run in runs}) == 19
    assert len({run["ros_tcp_port"] for run in runs}) == 19
    assert all(run["evidence_mask"] == "remove-delivered-odometry-v1"
               for run in runs if run["family"] == "missing_decisive_or_ambiguous_evidence")
    assert all(run["evidence_mask"] == "none"
               for run in runs if run["family"] != "missing_decisive_or_ambiguous_evidence")
