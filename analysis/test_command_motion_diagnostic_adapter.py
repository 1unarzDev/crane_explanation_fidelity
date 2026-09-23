import copy
import json
from pathlib import Path

import pytest

from recompute_command_motion_diagnostic import build_result, method_input_from_export


ROOT = Path(__file__).resolve().parents[1]
HELD = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json"
NOMINAL = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-nominal-001/evidence-and-diagnostic.json"
COMPENSATED = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-compensated-001/evidence-and-diagnostic.json"


@pytest.mark.parametrize(
    ("path", "disposition"),
    ((HELD, "supported"), (NOMINAL, "not_triggered")),
)
def test_recomputed_method_input_matches_retained_result(path: Path, disposition: str):
    export = json.loads(path.read_text(encoding="utf-8"))
    method_input = method_input_from_export(export)
    recomputed = build_result(method_input)

    assert not {"diagnostic_result", "final_answer", "final_text_verification"}.intersection(
        method_input
    )
    assert recomputed["diagnostic_result"] == export["diagnostic_result"]
    assert recomputed["final_answer"] == export["final_answer"]
    assert recomputed["diagnostic_result"]["disposition"] == disposition


def test_recompute_rejects_precomputed_diagnostic_leakage():
    export = json.loads(HELD.read_text(encoding="utf-8"))
    method_input = method_input_from_export(export)
    method_input["diagnostic_result"] = export["diagnostic_result"]

    with pytest.raises(ValueError, match="precomputed diagnostic fields"):
        build_result(method_input)


def test_recompute_rejects_recovery_policy_hash_mismatch():
    export = json.loads(HELD.read_text(encoding="utf-8"))
    method_input = method_input_from_export(export)
    changed = copy.deepcopy(method_input)
    changed["method_input"]["execution_sequence"]["recovery_node_classifier"][
        "policy_sha256"
    ] = "0" * 64

    with pytest.raises(ValueError, match="policy hash"):
        build_result(changed)


def test_recomputed_v2_input_preserves_recovered_response_result():
    export = json.loads(COMPENSATED.read_text(encoding="utf-8"))
    method_input = method_input_from_export(export)

    assert (
        method_input["method_input"]["diagnostic_computation_version"]
        == "command-motion-discrepancy-v2"
    )
    recomputed = build_result(method_input)
    assert recomputed["diagnostic_result"] == export["diagnostic_result"]
    assert recomputed["final_answer"] == export["final_answer"]


def test_recompute_rejects_unknown_computation_version():
    export = json.loads(COMPENSATED.read_text(encoding="utf-8"))
    method_input = method_input_from_export(export)
    method_input["method_input"]["diagnostic_computation_version"] = "v999"

    with pytest.raises(ValueError, match="unsupported command-motion computation version"):
        build_result(method_input)
