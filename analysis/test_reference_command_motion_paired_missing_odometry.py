import copy
import json
from pathlib import Path

import pytest

from mask_command_motion_evidence import build_masked_export
from reference_command_motion_paired_missing_odometry import build_reference


ROOT = Path(__file__).parents[1]
SOURCE = (
    ROOT
    / "data/robot_visible/dev/mccv4-dev-004/command-motion-diagnostic-v3-low-speed.json"
)


def masked_export() -> dict:
    source = json.loads(
        SOURCE.read_text(encoding="utf-8")
    )
    return build_masked_export(source, "mccv4-dev-004-mask-no-odometry")


def test_paired_reference_preserves_source_cluster_and_zero_increment() -> None:
    export = masked_export()
    result = build_reference(export, SOURCE, cluster_id="mccv4-land-004")
    assert result["statistical_cluster_id"] == "mccv4-land-004"
    assert result["independent_scenario_increment"] == 0
    assert result["answerability"]["command_motion_discrepancy"] == "insufficient"
    assert result["observations"]["independent_odometry_sample_count"] == 0
    assert result["observations"]["follow_path_attempt_count"] == 3


def test_paired_reference_rejects_increment_or_source_exposure() -> None:
    export = masked_export()
    bad_increment = copy.deepcopy(export)
    bad_increment["evidence_mask"]["independent_scenario_increment"] = 1
    with pytest.raises(ValueError, match="not paired"):
        build_reference(bad_increment, SOURCE, cluster_id="mccv4-land-004")

    exposed = copy.deepcopy(export)
    exposed["evidence_mask"]["paired_source_available_to_methods"] = True
    with pytest.raises(ValueError, match="fail-closed"):
        build_reference(exposed, SOURCE, cluster_id="mccv4-land-004")
