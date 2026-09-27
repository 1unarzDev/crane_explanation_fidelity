import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREDECL = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "explicit-causal-restraint-successor-v1-pilot-predeclaration.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pilot_predeclaration_pins_scientific_inputs_without_binding_alpha():
    value = json.loads(PREDECL.read_text(encoding="utf-8"))
    assert value["status"] == "FROZEN_AND_AUTHORIZED_FOR_FRESH_PILOT_ONLY"
    assert value["alpha_consumed"] == 0.0
    assert value["schedule"]["primary_configurations"] == 16
    assert value["schedule"]["controls"] == 4
    for section, path_key, hash_key in (
        ("schedule", "path", "sha256"),
        ("candidate", "renderer", "renderer_sha256"),
        ("baseline", "prompt", "prompt_sha256"),
        ("runner", "path", "sha256"),
        ("runner", "base_path", "base_sha256"),
        ("primary_measure", "detector_path", "detector_sha256"),
        ("primary_measure", "public_contract_path", "public_contract_sha256"),
        ("physical_runtime", "capture_runner", "capture_runner_sha256"),
    ):
        item = value[section]
        assert digest(ROOT / item[path_key]) == item[hash_key]


def test_pilot_and_discovery_replication_layouts_are_disjoint():
    value = json.loads(PREDECL.read_text(encoding="utf-8"))
    schedule = json.loads((ROOT / value["schedule"]["path"]).read_text(encoding="utf-8"))
    layouts = {
        stage: {item["layout_id"] for item in rows}
        for stage, rows in schedule["stages"].items()
    }
    assert layouts["pilot"].isdisjoint(layouts["discovery"])
    assert layouts["pilot"].isdisjoint(layouts["replication"])
    assert layouts["discovery"].isdisjoint(layouts["replication"])
