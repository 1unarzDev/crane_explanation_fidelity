import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v3-multiconfiguration-pilot-v1.json"
V2 = ROOT / "research/explanation_fidelity/experiment_configs/development/command-motion-candidate-v2-multiconfiguration-pilot-v1.json"


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_v3_declaration_pins_current_method_and_judge_bytes():
    declaration = json.loads(DECLARATION.read_text())
    pinned = declaration["pinned_software"]
    paths = {
        "candidate_runner_sha256": "analysis/run_command_motion_candidate_v3.py",
        "candidate_renderer_sha256": "analysis/render_command_motion_candidate_v3.py",
        "independent_reference_sha256": "analysis/reference_command_motion.py",
        "complete_reference_builder_sha256": "analysis/build_command_motion_reference_v2.py",
        "masked_complete_reference_builder_sha256": "analysis/build_command_motion_missing_reference_v2.py",
        "masked_independent_reference_sha256": "analysis/evaluate_command_motion_missing_odometry.py",
        "mask_generator_sha256": "analysis/mask_command_motion_evidence.py",
        "shared_diagnostic_adapter_sha256": "analysis/recompute_command_motion_diagnostic.py",
        "repository_agent_prompt_sha256": "research/explanation_fidelity/prompts/diagnostic_repository_agent_command_motion_dev_v2.txt",
        "luna_v7_freeze_sha256": "research/explanation_fidelity/experiment_configs/prospective/luna-model-judge-v7-reference-audited-freeze.json",
        "luna_v7_qualification_result_sha256": "manifests/annotation/luna-model-judge-v1-heldout-v7-reference-audited.json",
    }
    assert {name: digest(path) for name, path in paths.items()} == {
        name: pinned[name] for name in paths
    }


def test_v3_layouts_are_unique_and_fresh_relative_to_v2():
    declaration = json.loads(DECLARATION.read_text())
    prior = json.loads(V2.read_text())
    runs = declaration["physical_runs_in_fixed_order"]
    layouts = [item["layout_id"] for item in runs]
    prior_layouts = {item["layout_id"] for item in prior["physical_runs_in_fixed_order"]}
    assert len(layouts) == len(set(layouts)) == 6
    assert not set(layouts) & prior_layouts
    assert [item["order"] for item in runs] == list(range(1, 7))
    assert len({item["ros_domain_id"] for item in runs}) == 6
    assert len({item["ros_port"] for item in runs}) == 6


def test_v3_question_identity_and_readiness_are_explicit():
    declaration = json.loads(DECLARATION.read_text())
    assert declaration["question"] == {
        "question_id": "command-motion-candidate-v3-mechanism",
        "question_kind": "diagnostic-mechanism-or-false-premise-v3",
        "text": "Did a command-to-motion discrepancy prevent the robot from continuing toward the goal? Identify the deepest supported mechanism or reject the premise, connect it to the recorded navigation behavior, and state what remains unresolved.",
    }
    gate = declaration["development_readiness_gate"]
    assert gate["required_each_luna_pass_net_p_minus_r_successes"] == 2
    assert gate["p_material_errors_allowed"] == 0
    assert declaration["scientific_boundary"]["alpha_consumed"] == 0.0
