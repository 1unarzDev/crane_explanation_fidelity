import hashlib
import json
from pathlib import Path

from build_luna_boat_qualification_suite import build_suite, validate
from run_luna_boat_qualification import validate_freeze


def test_boat_suite_covers_supported_and_overclaimed_marine_cases():
    suite = build_suite()
    validate(suite)
    cases = suite["cases"]

    assert suite["status"] == "FRESH_UNEXECUTED_AT_DECLARATION"
    assert len(cases) == 12
    assert {case["family"] for case in cases} == {
        "terminal_margin",
        "bounded_navigation_geometry",
        "controller_axis_contract",
        "uncompensated_lateral_disturbance",
        "nominal_docking",
        "missing_decisive_motion_evidence",
    }
    assert sum(case["expected"]["material_error"] is False for case in cases) == 6
    assert sum(case["expected"]["material_error"] is True for case in cases) == 6
    assert all(case["accuracy_eligible"] for case in cases)
    assert all(case["primary_endpoint_eligible"] for case in cases)
    assert all("wave" in " ".join(case["prohibited_claims"]).lower() for case in cases)


def test_boat_freeze_pins_every_judge_input(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    sources = {
        "suite_sha256": root / "research/explanation_fidelity/qualification/luna-boat-diagnostic-v1-cases.json",
        "prompt_sha256": root / "research/explanation_fidelity/prompts/luna-model-judge-v5.md",
        "output_schema_sha256": root / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json",
        "caller_source_sha256": root / "analysis/luna_model_judge.py",
        "runner_source_sha256": root / "analysis/run_luna_boat_qualification.py",
        "suite_builder_sha256": root / "analysis/build_luna_boat_qualification_suite.py",
    }
    freeze = {
        "schema": "crane-luna-boat-judge-freeze/v1",
        "status": "FROZEN_BEFORE_ANY_BOAT_QUALIFICATION_CALL",
        "passes": ["pass-1", "pass-2"],
        **{field: hashlib.sha256(path.read_bytes()).hexdigest() for field, path in sources.items()},
    }
    path = tmp_path / "freeze.json"
    path.write_text(json.dumps(freeze) + "\n", encoding="utf-8")

    validate_freeze(path, sources["suite_sha256"])
    freeze["prompt_sha256"] = "0" * 64
    path.write_text(json.dumps(freeze) + "\n", encoding="utf-8")
    try:
        validate_freeze(path, sources["suite_sha256"])
    except ValueError:
        pass
    else:
        raise AssertionError("tampered judge freeze was accepted")
