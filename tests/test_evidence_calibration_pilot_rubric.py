from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_rubric import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402


def test_rubric_follows_visible_ladder_and_independent_reference() -> None:
    weak, weak_provenance = build("cm-land-conf-043-E0", "development-blinding-secret-v1")
    strong, strong_provenance = build("cm-land-conf-043-E3", "development-blinding-secret-v1")
    assert len(weak["required_unit_prompts"]) < len(strong["required_unit_prompts"])
    assert "state the supported command-to-measured-motion discrepancy and interval" in strong["required_unit_prompts"]
    assert "state the later measured-response recovery when supported" in strong["required_unit_prompts"]
    assert all("intervention" not in str(item).lower() for item in strong["sanitized_physical_facts"])
    assert weak_provenance["rubric_sha256"] == canonical_sha256(weak)
    assert strong_provenance["rubric_sha256"] == canonical_sha256(strong)
    assert weak_provenance["method_output_read"] is False


def test_missing_odometry_rubric_withholds_motion_diagnosis() -> None:
    rubric, _ = build("cm-land-conf-041-E2", "development-blinding-secret-v1")
    assert "state the supported command-to-measured-motion discrepancy and interval" not in rubric["required_unit_prompts"]
    assert "missing odometry prevents an odometry-dependent motion diagnosis" in rubric["limitation_prompts"]


def test_nominal_rubric_follows_actual_retained_packet() -> None:
    rubric, _ = build("cm-land-conf-054-E0", "development-blinding-secret-v1")
    terminal, _ = build("cm-land-conf-054-E2", "development-blinding-secret-v1")
    assert rubric["false_premise_applicable"] is False
    assert terminal["false_premise_applicable"] is True
    # The inspected pilot deviated from the catalog: its nominal E0 retains the BT trace.
    assert "state the retained source-qualified recovery sequence" in rubric["required_unit_prompts"]
