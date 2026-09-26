import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_coverage_complete_v4_evidence_complete_reference import (  # noqa: E402
    SOURCE_AND_CONFIG_PATHS,
    build,
    digest,
)
from build_diagnostic_annotation_packet import build_rows  # noqa: E402


CONTRACT = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/development"
        / "coverage-complete-v4-language-screen-v1.json"
    ).read_text()
)
RESULT_ROOT = ROOT / "model_outputs/dev/coverage-complete-v4-language-screen-v1/results"


def _result(case_id: str) -> dict:
    return json.loads((RESULT_ROOT / f"{case_id}.json").read_text())


def test_every_reference_contains_complete_r_primitive_and_hash_bound_sources():
    for case in CONTRACT["cases"]:
        case_id = case["case_id"]
        result = _result(case_id)
        reference = build(CONTRACT, result, case_id)
        allowed = reference["allowed_evidence"]
        primitive = allowed["primitive_diagnostic"]

        assert primitive["method_input"]
        assert primitive["diagnostic_result"]
        assert primitive.get("reference_computation") is not None or case["adapter"] == "command_motion_v2"
        assert len(allowed["source_and_config_excerpts"]) == len(SOURCE_AND_CONFIG_PATHS)
        assert {
            item["path"]: item["sha256"] for item in allowed["source_and_config_excerpts"]
        } == {path.relative_to(ROOT).as_posix(): digest(path) for path in SOURCE_AND_CONFIG_PATHS}
        serialized = json.dumps(primitive)
        assert "answer_plan" not in serialized
        assert "final_answer" not in serialized
        assert "final_text_verification" not in serialized


def test_evidence_complete_references_build_blinded_rows_for_unchanged_responses():
    for case in CONTRACT["cases"]:
        case_id = case["case_id"]
        result = _result(case_id)
        reference = build(CONTRACT, result, case_id)
        rows, key = build_rows(result, reference, "fixed-evidence-parity-test-secret")

        assert len(rows) == len(key) == 2
        assert {item["condition"] for item in key} == {"P", "R"}
        assert all("condition" not in row for row in rows)
        assert all(row["allowed_evidence"]["source_and_config_excerpts"] for row in rows)
        assert all(row["allowed_evidence"]["primitive_diagnostic"]["method_input"] for row in rows)


def test_source_and_config_hashes_match_frozen_treatment_inputs():
    frozen = CONTRACT["frozen_artifact_sha256"]
    expected = {
        "analysis/recompute_command_motion_diagnostic.py": frozen[
            "baseline_tool:recompute_command_motion"
        ],
        "analysis/reference_command_motion.py": frozen["baseline_tool:reference_command_motion"],
        "analysis/reference_land_geometric.py": frozen["baseline_tool:reference_land_geometric"],
        "analysis/reference_land_plan_geometry.py": frozen[
            "baseline_tool:reference_plan_geometry"
        ],
        "configs/diagnostic_command_motion_low_speed_v1.json": frozen[
            "baseline_tool:command_motion_config"
        ],
    }
    actual = {path.relative_to(ROOT).as_posix(): digest(path) for path in SOURCE_AND_CONFIG_PATHS}
    assert all(actual[path] == value for path, value in expected.items())
    assert actual["packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml"] == (
        "e38b8bb2347c59097ba410ea6520a9749f93bd7993eab8a912b3f9b269454b9b"
    )
    assert actual["packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml"] == (
        "14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520"
    )
