import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from build_checked_composition_annotation_reference import (  # noqa: E402
    load_inventory,
    validate_inventory,
)
from run_coverage_complete_v4_development import (  # noqa: E402
    frozen_artifact_paths,
    run,
)
from run_measurement_complete_v2_development import sha256_json, sha256_path  # noqa: E402


CONTRACT_PATH = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "coverage-complete-v4-language-screen-v1.json"
)


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
            "cache_key": call_id,
            "latency_ms": 2,
            "cost_usd": None,
            "usage": {},
            "parsed_final": {"answer": "Diagnosis: R answer."},
        }


def _args(tmp_path: Path, case_id: str, contract: Path = CONTRACT_PATH) -> argparse.Namespace:
    return argparse.Namespace(
        contract=contract,
        case_id=case_id,
        cache=tmp_path / "cache",
        output=tmp_path / f"{case_id}.json",
    )


def test_frozen_contract_hashes_every_transport_artifact_and_input():
    contract = json.loads(CONTRACT_PATH.read_text())
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256")
    assert contract["committed_contract_sha256"] == sha256_json(unhashed)
    assert contract["frozen_artifact_sha256"] == {
        name: sha256_path(path) for name, path in frozen_artifact_paths(contract).items()
    }
    for case in contract["cases"]:
        path = ROOT / case["diagnostic_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["diagnostic_sha256"]


def test_contract_counts_only_five_independent_scenario_configurations():
    contract = json.loads(CONTRACT_PATH.read_text())
    independent = [item for item in contract["cases"] if item["independent_cluster"]]
    masks = [item for item in contract["cases"] if not item["independent_cluster"]]

    assert len(independent) == contract["statistical_boundary"]["independent_clusters"] == 5
    assert len({item["cluster_id"] for item in independent}) == 5
    assert len(contract["cases"]) == contract["statistical_boundary"]["response_pairs"] == 7
    assert {item["paired_with"] for item in masks} == {
        "ccv4-geometry-001",
        "ccv4-persistent-004",
    }
    assert contract["statistical_boundary"]["confirmatory_semantic_n"] == 0
    assert contract["statistical_boundary"]["confirmatory_alpha_consumed"] == 0.0


def test_all_hash_bound_independent_references_validate():
    contract = json.loads(CONTRACT_PATH.read_text())
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    references = validate_inventory(contract, inventory)

    assert len(references) == 7
    assert sum(item["primary_endpoint_eligible"] for item in references) == 5


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("ccv4-geometry-001", "non-traversable near x=12.425 m"),
        ("ccv4-missing-odometry-004m", "414 delivered command samples"),
        ("ccv4-compensation-005", "recorded navigation action succeeded"),
    ],
)
def test_successor_runner_uses_v4_identity_and_blinded_fair_baseline(
    tmp_path: Path, case_id: str, expected: str
):
    caller = FakeCaller()
    result = run(_args(tmp_path, case_id), caller=caller)

    assert result["schema"] == "crane-coverage-complete-v4-development-case-result/v1"
    assert result["question_id"] == f"coverage-complete-v4:{case_id}"
    assert caller.calls[0][0] == f"coverage-complete-v4-{case_id}-R"
    assert expected in result["outputs"][0]["text"]
    assert result["outputs"][0]["generation_method"] == (
        "coverage_complete_checked_composition_v4_deterministic"
    )
    assert result["information_parity"]["same_robot_visible_primitive_diagnostic"] is True
    assert result["information_parity"]["same_embedded_reference_computation"] is True
    assert result["information_parity"]["episode_certificate_visible_to_R"] is False
    assert result["evaluator_truth_available_to_methods"] is False
    serialized = json.dumps(caller.blind)
    assert "answer_plan" not in serialized
    assert "final_answer" not in serialized
    assert "final_text_verification" not in serialized


def test_runner_rejects_any_postfreeze_contract_mutation(tmp_path: Path):
    contract = json.loads(CONTRACT_PATH.read_text())
    contract["cases"][0]["question"] = "changed after freeze"
    mutated = tmp_path / "mutated-contract.json"
    mutated.write_text(json.dumps(contract))

    with pytest.raises(ValueError, match="contract hash mismatch"):
        run(_args(tmp_path, "ccv4-geometry-001", mutated), caller=FakeCaller())
