import hashlib
import json
from pathlib import Path

from build_focused_annotation_reference_v3 import build_command


ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-coordinator-amendment-2.json"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_nominal_control_reference_binds_each_fact_to_its_semantic_registry_unit():
    run_id = "cm-land-conf-054"
    export = load(ROOT / f"data/robot_visible/dev/{run_id}/command-motion-diagnostic-v3.json")
    independent = load(
        ROOT / f"data/evaluator_only/dev/{run_id}/command-motion-independent-reference-v1.json"
    )
    result = build_command(
        export,
        independent,
        family="nominal_false_premise_or_irrelevant_obstacle",
        question_id=f"focused-{run_id}",
    )
    units = {item["unit_id"]: item["text"] for item in result["required_units"]}

    assert "did not trigger" in units["false-premise-rejection"]
    assert "succeeded" in units["action-outcome-and-nominal-or-not-triggered-motion-evidence"]
    assert "0.2597 m/s" in units["action-outcome-and-nominal-or-not-triggered-motion-evidence"]
    assert "obstacle" in units["no-obstacle-cause-from-visibility-alone"]
    assert "Nav2 consumption" in units["no-exact-nav2-consumption-claim"]


def test_amendment_2_freezes_the_corrected_adapter_before_semantic_confirmation():
    amendment = load(AMENDMENT)
    assert amendment["inspection_boundary"]["semantic_primary_N"] == 0
    assert amendment["inspection_boundary"]["P_confirmatory_responses_opened"] == 0
    assert amendment["inspection_boundary"]["R_confirmatory_responses_opened"] == 0
    for artifact in amendment["frozen_artifacts"].values():
        path = ROOT / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
