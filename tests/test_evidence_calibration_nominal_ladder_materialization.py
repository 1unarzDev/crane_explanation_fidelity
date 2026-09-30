from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_nested_evidence_conditions import build_conditions  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from normalize_command_motion_evidence import normalize  # noqa: E402
from validate_evidence_calibration_ladder_materialization import validate_materialization  # noqa: E402


CATALOG = json.loads((ROOT / "configs/evidence_calibration_ladders_v1_development.json").read_text())
LADDER_ID = "nominal-false-premise-v1-development"
QUESTION = "The episode succeeded; was there nevertheless a navigation failure, and what does the evidence support?"


def _inputs():
    status = json.loads((ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json").read_text())
    row = next(item for item in status["episodes"] if item["run_id"] == "cm-land-conf-054")
    schedule = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    run = next(item for item in schedule["cohorts"][0]["runs"] if item["run_id"] == row["run_id"])
    diagnostic = json.loads((ROOT / row["diagnostic_path"]).read_text())
    return row, run, diagnostic


def _spec(diagnostic: dict) -> dict:
    removals = [
        ["/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
        ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
        [],
    ]
    builder = ROOT / "analysis/build_nested_evidence_conditions.py"
    return {
        "schema": "crane-nested-evidence-mask-spec/v1",
        "ladder_id": LADDER_ID,
        "condition_builder_id": "nested-evidence-condition-builder",
        "condition_builder_version": "v1",
        "condition_builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
        "source_configuration_sha256": diagnostic["source"]["nav2_config_sha256"],
        "runtime_manifest_sha256": diagnostic["source"]["runtime_manifest_sha256"],
        "conditions": [
            {"condition_id": f"prospective-nominal-E{index}", "level_index": index,
             "removed_json_pointers": pointers,
             "mask_id": None if not pointers else f"nominal-E{index}",
             "mask_version": None if not pointers else "v2-development-source-projection"}
            for index, pointers in enumerate(removals)
        ],
    }


def test_prospective_nominal_projection_matches_catalog_and_preserves_old_source_hash() -> None:
    row, run, diagnostic = _inputs()
    old = normalize(diagnostic, configuration_id=run["cluster_id"], question=QUESTION)
    assert canonical_sha256(old) == row["normalized_source_sha256"]
    projected = normalize(diagnostic, configuration_id=run["cluster_id"], question=QUESTION,
                          omit_recovery_and_source_anchors=True)
    bundle = build_conditions(projected, _spec(diagnostic))
    result = validate_materialization(CATALOG, LADDER_ID, bundle)
    assert result["status"] == "PASS_CATALOG_BOUND_DEVELOPMENT_ONLY"
    assert result["levels"] == 3
    assert set(result["terminal_roles"]) == {
        "navigate_to_pose_result", "delivered_command_stream",
        "delivered_odometry_stream", "command_motion_computation",
    }


def test_retained_nominal_source_with_extra_trace_roles_fails_prospective_gate() -> None:
    _, run, diagnostic = _inputs()
    old = normalize(diagnostic, configuration_id=run["cluster_id"], question=QUESTION)
    bundle = build_conditions(old, _spec(diagnostic))
    with pytest.raises(ValueError, match="unmasked source roles"):
        validate_materialization(CATALOG, LADDER_ID, bundle)


def test_catalog_gate_rejects_a_rewritten_question_even_with_matching_packet_hash() -> None:
    _, run, diagnostic = _inputs()
    projected = normalize(diagnostic, configuration_id=run["cluster_id"], question=QUESTION,
                          omit_recovery_and_source_anchors=True)
    bundle = build_conditions(projected, _spec(diagnostic))
    bundle[0]["method_packet"]["question"] = "A different question"
    bundle[0]["condition"]["method_packet_sha256"] = canonical_sha256(bundle[0]["method_packet"])
    with pytest.raises(ValueError, match="byte-preserving removal"):
        validate_materialization(CATALOG, LADDER_ID, bundle)
