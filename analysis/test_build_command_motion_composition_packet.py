import copy
import hashlib
import json
from pathlib import Path

import pytest

from build_command_motion_composition_packet import build
from compose_diagnostic_hypotheses import compose
from render_diagnostic_composition import render


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads(
    (ROOT / "configs/diagnostic_composition_registry_v1.json").read_text(encoding="utf-8")
)


def load(relative: str):
    raw = (ROOT / relative).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    ("relative", "primary", "required_text"),
    [
        (
            "data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json",
            "command_to_motion_discrepancy",
            "median measured speed 0 m/s during 10--20 s",
        ),
        (
            "data/robot_visible/dev/cmv3-dev-002/command-motion-diagnostic-v3.json",
            "measured_response_recovery",
            "Measured response later recovered to 0.25974 m/s during 24--25 s",
        ),
        (
            "data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json",
            "nominal_command_motion",
            "does not support the question's command-to-motion-failure premise",
        ),
        (
            "data/robot_visible/dev/cmv3-dev-001-mask-no-odometry/command-motion-diagnostic-v3.json",
            "command_motion_evidence_insufficient",
            "missing delivered odometry stream",
        ),
    ],
)
def test_real_development_exports_compile_to_complete_renderable_plans(relative, primary, required_text):
    document, digest = load(relative)
    packet = build(document, source_sha256=digest)
    certificate = compose(packet, REGISTRY)

    assert certificate["status"] == "composed"
    assert certificate["answer_plan"]["primary_mechanism_id"] == primary
    assert certificate["answer_plan"]["language_ready"] is True
    assert certificate["answer_plan"]["missing_required_unit_ids"] == []
    assert required_text in render(certificate)
    assert packet["source"]["sha256"] == digest
    assert "geometry_supported" not in certificate["answer_plan"]["missing_discriminators"]


def test_masked_export_does_not_reuse_unmasked_mechanism():
    document, digest = load(
        "data/robot_visible/dev/cmv3-dev-001-mask-no-odometry/command-motion-diagnostic-v3.json"
    )
    certificate = compose(build(document, source_sha256=digest), REGISTRY)
    indexed = {item["mechanism_id"]: item for item in certificate["mechanisms"]}

    assert indexed["command_to_motion_discrepancy"]["status"] == "unresolved"
    assert certificate["answer_plan"]["primary_mechanism_id"] == "command_motion_evidence_insufficient"
    text = render(certificate)
    assert "prevents a time-aligned command-response chain" in text
    assert "establish a command-to-motion discrepancy" in text


def test_adapter_rejects_evaluator_only_input():
    document, digest = load(
        "data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json"
    )
    document = copy.deepcopy(document)
    document["visibility"] = "evaluator_only"

    with pytest.raises(ValueError, match="robot-visible"):
        build(document, source_sha256=digest)


def test_adapter_fails_closed_when_supported_measurement_is_missing():
    document, digest = load(
        "data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json"
    )
    document = copy.deepcopy(document)
    document["diagnostic_result"]["measurements"] = [
        item
        for item in document["diagnostic_result"]["measurements"]
        if item["id"] != "discrepancy_measured_planar_speed"
    ]

    with pytest.raises(ValueError, match="lacks decisive measurements"):
        build(document, source_sha256=digest)


def test_nominal_adapter_uses_structured_execution_counts_not_inconsistent_prose():
    document, digest = load(
        "data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json"
    )
    text = render(compose(build(document, source_sha256=digest), REGISTRY))

    assert "3 FollowPath attempts" in text
    assert "2 FollowPath failures" in text
    assert "2 source-qualified Wait invocations" in text
    assert "no observed FollowPath failure" not in text


def test_adapter_rejects_execution_count_disagreement():
    document, digest = load(
        "data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json"
    )
    document = copy.deepcopy(document)
    document["method_input"]["execution_sequence"]["follow_path_failure_count"] = 99

    with pytest.raises(ValueError, match="execution sequence and measurements disagree"):
        build(document, source_sha256=digest)
