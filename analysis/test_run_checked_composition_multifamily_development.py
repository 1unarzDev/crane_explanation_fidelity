import argparse
import copy
import hashlib
import json
from pathlib import Path

import pytest

from build_checked_composition_annotation_reference import build_reference, load_inventory
from build_diagnostic_annotation_packet import build_rows
from run_checked_composition_multifamily_development import (
    frozen_artifact_paths,
    run,
    sha256_json,
    sha256_path,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONTRACT = ROOT / "research/explanation_fidelity/experiment_configs/development/diagnostic-checked-composition-multifamily-screen-v1.json"


class FakeCaller:
    def __init__(self):
        self.calls = []
        self.blind = None

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        self.blind = json.loads(
            (kwargs["working_directory"] / "_robot_visible/primitive-diagnostic.json").read_text()
        )
        return {
            "cache_key": "r-call",
            "latency_ms": 2,
            "cost_usd": None,
            "usage": {},
            "parsed_final": {"answer": "Diagnosis: R answer."},
        }


def frozen_contract(tmp_path: Path) -> Path:
    contract = json.loads(SOURCE_CONTRACT.read_text())
    contract["status"] = "FROZEN_BEFORE_ANY_CALL"
    contract["frozen_artifact_sha256"] = {
        name: sha256_path(path) for name, path in frozen_artifact_paths(contract).items()
    }
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256", None)
    contract["committed_contract_sha256"] = sha256_json(unhashed)
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    return path


def args(tmp_path: Path, contract: Path) -> argparse.Namespace:
    return argparse.Namespace(
        contract=contract,
        case_id="ccdev-persistent-001",
        cache=tmp_path / "cache",
        output=tmp_path / "result.json",
    )


def test_runner_refuses_uncommitted_draft(tmp_path: Path):
    with pytest.raises(ValueError, match="not committed/frozen"):
        run(args(tmp_path, SOURCE_CONTRACT), caller=FakeCaller())


def test_runner_gives_r_same_primitive_result_but_not_episode_certificate(tmp_path: Path):
    caller = FakeCaller()
    result = run(args(tmp_path, frozen_contract(tmp_path)), caller=caller)

    assert len(caller.calls) == 1
    assert result["information_parity"]["same_blind_primitive_diagnostic"]
    assert not result["information_parity"]["episode_certificate_visible_to_R"]
    assert [item["condition"] for item in result["outputs"]] == ["P", "R"]
    assert result["episode_id"] == "cmv3-land-001"
    assert result["question_id"] == "checked-composition:ccdev-persistent-001"
    assert result["question_kind"] == "supported_execution_mechanism"
    assert result["evaluator_truth_available_to_methods"] is False
    assert result["permitted_evidence_identifiers"]
    assert result["inputs"]["annotation_reference_sha256"]
    assert "command-to-motion discrepancy" in result["outputs"][0]["text"]
    assert caller.blind["visibility"] == "robot_visible"
    assert "diagnostic_result" in caller.blind
    serialized = json.dumps(caller.blind)
    assert "final_answer" not in serialized
    assert "answer_plan" not in serialized
    assert "final_text_verification" not in serialized
    assert "condition" not in serialized


def test_runner_result_builds_v12_endpoint_aligned_blinded_rows(tmp_path: Path):
    result = run(args(tmp_path, frozen_contract(tmp_path)), caller=FakeCaller())
    contract = json.loads(SOURCE_CONTRACT.read_text())
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    screen_case = next(item for item in contract["cases"] if item["case_id"] == result["case_id"])
    reference_case = next(
        item for item in inventory["cases"] if item["case_id"] == result["case_id"]
    )
    reference = build_reference(screen_case, reference_case)

    rows, key = build_rows(result, reference, "fixed-test-secret")

    assert len(rows) == len(key) == 2
    assert {item["condition"] for item in key} == {"P", "R"}
    by_condition = {item["condition"]: item for item in key}
    assert by_condition["P"]["provider"] == "deterministic"
    assert by_condition["P"]["model"] is None
    assert by_condition["R"]["provider"] == "codex"
    assert by_condition["R"]["model"] == "gpt-6-sol"
    assert all(item["primary_endpoint_eligible"] is True for item in rows)
    assert all(
        item["mechanism_unit_id"] == "mechanism-command-motion-discrepancy"
        for item in rows
    )
    assert all("condition" not in item for item in rows)


def test_runner_refuses_contract_hash_mismatch(tmp_path: Path):
    path = frozen_contract(tmp_path)
    contract = json.loads(path.read_text())
    contract["cases"][0]["question"] = "Changed after freeze"
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="contract hash mismatch"):
        run(args(tmp_path, path), caller=FakeCaller())


def test_runner_refuses_frozen_artifact_hash_mismatch(tmp_path: Path):
    path = frozen_contract(tmp_path)
    contract = json.loads(path.read_text())
    contract["frozen_artifact_sha256"]["reference_inventory"] = "0" * 64
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256", None)
    contract["committed_contract_sha256"] = sha256_json(unhashed)
    path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="frozen artifact hash mismatch"):
        run(args(tmp_path, path), caller=FakeCaller())


def test_draft_contract_counts_only_independent_scenario_configurations():
    contract = json.loads(SOURCE_CONTRACT.read_text())
    independent = [item for item in contract["cases"] if item["independent_cluster"]]
    masks = [item for item in contract["cases"] if not item["independent_cluster"]]

    assert len(independent) == contract["statistical_boundary"]["independent_clusters"] == 6
    assert len({item["cluster_id"] for item in independent}) == 6
    assert len(masks) == 1
    assert masks[0]["paired_with"] == "ccdev-persistent-001"
    assert masks[0]["cluster_id"] == "cmv3-land-001"


def test_draft_contract_hash_pins_every_robot_visible_diagnostic():
    contract = json.loads(SOURCE_CONTRACT.read_text())
    for case in contract["cases"]:
        path = ROOT / case["diagnostic_path"]
        assert path.is_file()
        assert case["diagnostic_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
