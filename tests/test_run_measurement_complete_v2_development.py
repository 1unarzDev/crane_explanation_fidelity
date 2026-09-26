import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_checked_composition_annotation_reference import (
    load_inventory,
    validate_inventory,
)
from build_command_motion_reference_v3 import build_reference as build_command_reference_v3
from run_measurement_complete_v2_development import (
    frozen_artifact_paths,
    run,
    sha256_json,
    sha256_path,
)

SOURCE_CONTRACT = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "measurement-complete-v2-language-screen-v1.json"
)


class FakeCaller:
    def __init__(self):
        self.calls = []
        self.blind = None
        self.tools = []

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        workspace = kwargs["working_directory"]
        self.blind = json.loads(
            (workspace / "_robot_visible/primitive-diagnostic.json").read_text()
        )
        self.tools = sorted(path.name for path in (workspace / "_deterministic_tools").iterdir())
        return {
            "cache_key": "r-call",
            "latency_ms": 2,
            "cost_usd": None,
            "usage": {},
            "parsed_final": {"answer": "Diagnosis: R answer."},
        }


def frozen_contract(tmp_path: Path) -> Path:
    contract = json.loads(SOURCE_CONTRACT.read_text())
    contract["status"] = "FROZEN_BEFORE_ANY_RESPONSE_OR_JUDGMENT"
    contract["frozen_artifact_sha256"] = {
        name: sha256_path(path) for name, path in frozen_artifact_paths(contract).items()
    }
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256", None)
    contract["committed_contract_sha256"] = sha256_json(unhashed)
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    return path


def args(tmp_path: Path, contract: Path, case_id="mccv2-geometry-supported-001"):
    return argparse.Namespace(
        contract=contract,
        case_id=case_id,
        cache=tmp_path / "cache",
        output=tmp_path / f"{case_id}.json",
    )


def test_runner_refuses_draft_before_any_response(tmp_path: Path):
    with pytest.raises(ValueError, match="not committed/frozen"):
        run(args(tmp_path, SOURCE_CONTRACT), caller=FakeCaller())


def test_runner_exposes_complete_primitive_and_tools_but_not_candidate_plan(tmp_path: Path):
    caller = FakeCaller()
    result = run(args(tmp_path, frozen_contract(tmp_path)), caller=caller)

    assert len(caller.calls) == 1
    assert result["information_parity"]["same_embedded_reference_computation"]
    assert not result["information_parity"]["episode_certificate_visible_to_R"]
    assert set(result["information_parity"]["baseline_deterministic_tools"]) == {
        "command_motion_config",
        "recompute_command_motion",
        "reference_command_motion",
        "reference_land_geometric",
        "reference_plan_geometry",
    }
    assert "reference_computation" in caller.blind
    assert caller.tools
    serialized = json.dumps(caller.blind)
    assert "final_answer" not in serialized
    assert "answer_plan" not in serialized
    assert "final_text_verification" not in serialized
    assert [item["condition"] for item in result["outputs"]] == ["P", "R"]
    assert "non-traversable near x=11.575 m" in result["outputs"][0]["text"]


def test_contract_counts_configurations_not_masks_questions_or_calls():
    contract = json.loads(SOURCE_CONTRACT.read_text())
    independent = [item for item in contract["cases"] if item["independent_cluster"]]
    dependent = [item for item in contract["cases"] if not item["independent_cluster"]]

    assert len(independent) == contract["statistical_boundary"]["independent_clusters"] == 6
    assert len({item["cluster_id"] for item in independent}) == 6
    assert len(contract["cases"]) == contract["statistical_boundary"]["response_pairs"] == 9
    assert all(item.get("paired_with") for item in dependent)
    assert contract["statistical_boundary"]["paired_masks_add_clusters"] == 0
    assert contract["statistical_boundary"]["question_variants_add_clusters"] == 0


def test_all_diagnostics_and_independent_references_validate():
    contract = json.loads(SOURCE_CONTRACT.read_text())
    inventory_path = ROOT / contract["reference_inventory"]
    references = validate_inventory(contract, load_inventory(inventory_path))

    assert len(references) == 9
    for case in contract["cases"]:
        path = ROOT / case["diagnostic_path"]
        assert path.is_file()
        assert case["diagnostic_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert sum(item["primary_endpoint_eligible"] for item in references) == 4


def test_v3_builder_reproduces_retained_singular_execution_reference():
    contract = json.loads(SOURCE_CONTRACT.read_text())
    case = next(item for item in contract["cases"] if item["case_id"] == "mccv2-compensation-004")
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    reference_case = next(
        item for item in inventory["cases"] if item["case_id"] == case["case_id"]
    )
    retained_path = ROOT / reference_case["reference_sources"][0]["path"]
    retained = json.loads(retained_path.read_text())
    export = json.loads((ROOT / case["diagnostic_path"]).read_text())
    independent = retained["allowed_evidence"]["independent_computation"]

    rebuilt = build_command_reference_v3(
        export,
        independent,
        question_id=retained["question_id"],
    )
    rebuilt["inputs"] = retained["inputs"]

    assert rebuilt == retained
    sequence = next(
        item for item in rebuilt["required_units"] if item["unit_id"] == "execution-sequence"
    )
    assert "1 FollowPath failure" in sequence["text"]
    assert "1 source-qualified Wait invocation" in sequence["text"]


def test_frozen_contract_hash_and_artifact_hashes_are_enforced(tmp_path: Path):
    path = frozen_contract(tmp_path)
    contract = json.loads(path.read_text())
    contract["cases"][0]["question"] = "changed after freeze"
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="contract hash mismatch"):
        run(args(tmp_path, path), caller=FakeCaller())

    path = frozen_contract(tmp_path)
    contract = json.loads(path.read_text())
    contract["frozen_artifact_sha256"]["reference_inventory"] = "0" * 64
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256", None)
    contract["committed_contract_sha256"] = sha256_json(unhashed)
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="frozen artifact hash mismatch"):
        run(args(tmp_path, path), caller=FakeCaller())
