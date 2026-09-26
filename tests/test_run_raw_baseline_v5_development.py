import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from run_measurement_complete_v2_development import sha256_json, sha256_path  # noqa: E402
from run_raw_baseline_v5_development import (  # noqa: E402
    FORBIDDEN_BASELINE_KEYS,
    frozen_artifact_paths,
    run,
)


CONTRACT_PATH = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "raw-baseline-v5-language-screen-v1.json"
)


def _keys(value):
    if isinstance(value, dict):
        result = set(value)
        for item in value.values():
            result |= _keys(item)
        return result
    if isinstance(value, list):
        result = set()
        for item in value:
            result |= _keys(item)
        return result
    return set()


class FakeCaller:
    def __init__(self):
        self.calls = []
        self.evidence = None

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        evidence_path = kwargs["working_directory"] / "_robot_visible/evidence.json"
        self.evidence = json.loads(evidence_path.read_text())
        assert (kwargs["working_directory"] / "_deterministic_tools").is_dir()
        assert (
            kwargs["working_directory"]
            / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml"
        ).is_file()
        assert (
            kwargs["working_directory"]
            / "packages/astro_dock/src/crane_explain/src/crane_explain/diagnostics.py"
        ).is_file()
        return {
            "cache_key": call_id,
            "latency_ms": 2,
            "cost_usd": None,
            "usage": {},
            "parsed_final": {"answer": "Diagnosis: raw-evidence R answer."},
        }


def _args(tmp_path: Path, case_id: str, contract: Path = CONTRACT_PATH) -> argparse.Namespace:
    return argparse.Namespace(
        contract=contract,
        case_id=case_id,
        cache=tmp_path / "cache",
        output=tmp_path / f"{case_id}.json",
    )


def test_contract_hashes_every_transport_artifact_and_both_treatment_inputs():
    contract = json.loads(CONTRACT_PATH.read_text())
    unhashed = copy.deepcopy(contract)
    unhashed.pop("committed_contract_sha256")
    assert contract["committed_contract_sha256"] == sha256_json(unhashed)
    assert contract["frozen_artifact_sha256"] == {
        name: sha256_path(path) for name, path in frozen_artifact_paths(contract).items()
    }
    for case in contract["cases"]:
        diagnostic = ROOT / case["diagnostic_path"]
        baseline = ROOT / case["baseline_evidence_path"]
        assert hashlib.sha256(diagnostic.read_bytes()).hexdigest() == case["diagnostic_sha256"]
        assert hashlib.sha256(baseline.read_bytes()).hexdigest() == case["baseline_evidence_sha256"]


def test_contract_reuses_five_development_clusters_and_consumes_no_alpha():
    contract = json.loads(CONTRACT_PATH.read_text())
    boundary = contract["statistical_boundary"]
    independent = [item for item in contract["cases"] if item["independent_cluster"]]
    masks = [item for item in contract["cases"] if not item["independent_cluster"]]
    assert len(independent) == boundary["independent_clusters"] == 5
    assert boundary["new_independent_clusters"] == 0
    assert len(contract["cases"]) == boundary["response_pairs"] == 7
    assert {item["paired_with"] for item in masks} == {
        "ccv5-geometry-001",
        "ccv5-persistent-004",
    }
    assert boundary["confirmatory_semantic_n"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0


def test_every_baseline_packet_is_raw_robot_visible_and_checked_output_free():
    contract = json.loads(CONTRACT_PATH.read_text())
    for case in contract["cases"]:
        document = json.loads((ROOT / case["baseline_evidence_path"]).read_text())
        assert document["visibility"] == "robot_visible"
        assert not (FORBIDDEN_BASELINE_KEYS & _keys(document))
        assert "evaluator_only" not in json.dumps(document)


@pytest.mark.parametrize(
    ("case_id", "candidate_text"),
    [
        ("ccv5-geometry-001", "non-traversable near x=12.425 m"),
        ("ccv5-geometry-masked-001m", "costmap cell payload is unavailable"),
        ("ccv5-persistent-004", "median measured speed 0 m/s during 11--21 s"),
    ],
)
def test_runner_is_namespaced_and_gives_r_only_raw_evidence(
    tmp_path: Path, case_id: str, candidate_text: str
):
    caller = FakeCaller()
    result = run(_args(tmp_path, case_id), caller=caller)
    assert result["schema"] == "crane-raw-baseline-v5-development-case-result/v1"
    assert result["question_id"] == f"raw-baseline-v5:{case_id}"
    assert caller.calls[0][0] == f"raw-baseline-v5-{case_id}-R"
    assert candidate_text in result["outputs"][0]["text"]
    assert result["outputs"][1]["text"] == "Diagnosis: raw-evidence R answer."
    parity = result["information_parity"]
    assert parity["same_underlying_robot_visible_observations"] is True
    assert parity["same_executable_diagnostic_tools"] is True
    assert parity["precomputed_diagnostic_visible_to_R"] is False
    assert parity["precomputed_reference_computation_visible_to_R"] is False
    assert not (FORBIDDEN_BASELINE_KEYS & _keys(caller.evidence))


def test_runner_rejects_any_postfreeze_contract_mutation(tmp_path: Path):
    contract = json.loads(CONTRACT_PATH.read_text())
    contract["cases"][0]["question"] = "changed after freeze"
    mutated = tmp_path / "mutated-contract.json"
    mutated.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="contract hash mismatch"):
        run(_args(tmp_path, "ccv5-geometry-001", mutated), caller=FakeCaller())
