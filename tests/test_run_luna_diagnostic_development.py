from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_luna_diagnostic_development.py"
SPEC = importlib.util.spec_from_file_location("run_luna_diagnostic_development", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def judgment(mechanism: str, material_error: bool, disposition: str = "full") -> dict:
    return {
        "mechanism_identification": mechanism,
        "material_error": material_error,
        "disposition": disposition,
    }


def test_endpoint_derivations_keep_false_premise_separate() -> None:
    assert MODULE.success(judgment("correct", False)) is True
    assert MODULE.success(judgment("not_applicable", False)) is False
    assert MODULE.false_premise_success(judgment("not_applicable", False)) is True
    assert MODULE.false_premise_success(judgment("correct", False)) is False


def test_summary_reports_passes_and_disagreements() -> None:
    rows = []
    for pass_id in ("pass-1", "pass-2"):
        for condition in MODULE.CONDITIONS:
            for packet in sorted(MODULE.MECHANISM_PACKETS):
                value = not (condition == "R" and packet == "land-s-turn-unmasked")
                if pass_id == "pass-2" and condition == "P" and packet == "command-motion-supported":
                    value = False
                rows.append(
                    {
                        "pass_id": pass_id,
                        "response_id": f"{condition}-{packet}",
                        "packet_name": packet,
                        "condition": condition,
                        "judgment": judgment("correct" if value else "omitted", False),
                    }
                )
            rows.append(
                {
                    "pass_id": pass_id,
                    "response_id": f"{condition}-nominal",
                    "packet_name": MODULE.FALSE_PREMISE_PACKET,
                    "condition": condition,
                    "judgment": judgment("not_applicable", False),
                }
            )
    report = MODULE.summarize(rows, [])
    assert report["responses"] == 24
    assert report["passes"]["pass-1"]["conditions"]["P"]["mechanism_successes"] == 5
    assert report["passes"]["pass-1"]["conditions"]["R"]["mechanism_successes"] == 4
    assert report["primary_endpoint_disagreement_count"] == 1
