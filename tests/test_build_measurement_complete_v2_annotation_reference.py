from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_checked_composition_annotation_reference import (  # noqa: E402
    build_reference as build_base_reference,
    load_inventory,
)
from build_measurement_complete_v2_annotation_reference import (  # noqa: E402
    build_reference,
)
from build_diagnostic_annotation_packet import build_rows  # noqa: E402


CONTRACT = ROOT / (
    "research/explanation_fidelity/experiment_configs/development/"
    "measurement-complete-v2-language-screen-v1.json"
)


def fixtures(case_id: str) -> tuple[dict, dict, dict]:
    contract = json.loads(CONTRACT.read_text())
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    case = next(item for item in contract["cases"] if item["case_id"] == case_id)
    reference_case = next(item for item in inventory["cases"] if item["case_id"] == case_id)
    result = json.loads(
        (
            ROOT
            / "model_outputs/dev/measurement-complete-v2-language-screen-v1/results"
            / f"{case_id}.json"
        ).read_text()
    )
    return case, reference_case, result


def test_wrapper_changes_only_question_namespace() -> None:
    case, reference_case, _ = fixtures("mccv2-persistent-003")
    base = build_base_reference(case, reference_case)
    adjusted = build_reference(case, reference_case)
    expected = copy.deepcopy(base)
    expected["question_id"] = "measurement-complete-v2:mccv2-persistent-003"
    assert adjusted == expected


def test_adjusted_reference_passes_strict_packet_identity_gate() -> None:
    case, reference_case, result = fixtures("mccv2-compensation-004")
    reference = build_reference(case, reference_case)
    rows, key = build_rows(result, reference, "fixed-test-secret")
    assert len(rows) == len(key) == 2
    assert {item["condition"] for item in key} == {"P", "R"}
    assert all("condition" not in row for row in rows)
