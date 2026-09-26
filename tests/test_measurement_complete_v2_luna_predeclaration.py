from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "manifests/annotation/luna-measurement-complete-v2-language-screen-v1-predeclaration.json"
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_predeclaration_binds_exact_treatments_references_and_cluster_boundary() -> None:
    manifest = load(MANIFEST)
    treatment = manifest["treatment_contract"]
    contract_path = ROOT / treatment["path"]
    contract = load(contract_path)
    inventory_spec = manifest["reference_inventory"]
    inventory_path = ROOT / inventory_spec["path"]
    inventory = load(inventory_path)

    assert manifest["status"] == "FROZEN_BEFORE_ANY_RESPONSE_OR_LUNA_STUDY_CALL"
    assert manifest["inferential_status"] == "DEVELOPMENT_ONLY_NOT_CONFIRMATORY"
    assert treatment["file_sha256"] == digest(contract_path)
    assert treatment["committed_contract_sha256"] == contract["committed_contract_sha256"]
    assert treatment["runner_sha256"] == contract["frozen_artifact_sha256"]["runner"]
    assert inventory_spec["sha256"] == digest(inventory_path)
    assert inventory_spec["sha256"] == contract["frozen_artifact_sha256"]["reference_inventory"]

    declared = {item["case_id"]: item for item in manifest["cases"]}
    contract_cases = {item["case_id"]: item for item in contract["cases"]}
    references = {item["case_id"]: item for item in inventory["cases"]}
    assert set(declared) == set(contract_cases) == set(references)
    for case_id, item in declared.items():
        assert item["cluster_id"] == contract_cases[case_id]["cluster_id"]
        assert item["independent_cluster"] == contract_cases[case_id]["independent_cluster"]
        assert item["primary_endpoint_eligible"] == references[case_id][
            "primary_endpoint_eligible"
        ]
        assert item["mechanism_unit_id"] == references[case_id]["mechanism_unit_id"]

    boundary = manifest["statistical_boundary"]
    assert boundary["independent_unit"] == "scenario configuration"
    assert boundary["independent_clusters"] == 6
    assert boundary["response_pairs"] == 9
    assert boundary["paired_masks_add_clusters"] == 0
    assert boundary["question_variants_add_clusters"] == 0
    assert boundary["model_generations_add_clusters"] == 0
    assert boundary["luna_passes_add_clusters"] == 0
    assert boundary["confirmatory_alpha_consumed"] == 0.0


def test_predeclaration_uses_exact_qualified_v12_release_and_blinding_tools() -> None:
    manifest = load(MANIFEST)
    release = manifest["judge_release"]
    paths = {
        "qualification_manifest_sha256": ROOT / release["qualification_manifest"],
        "freeze_sha256": ROOT / release["freeze"],
        "prompt_sha256": ROOT / release["prompt"],
        "output_schema_sha256": ROOT / release["output_schema"],
        "caller_sha256": ROOT / release["caller"],
        "runner_sha256": ROOT / release["runner"],
    }
    for field, path in paths.items():
        assert release[field] == digest(path)

    qualification = load(paths["qualification_manifest_sha256"])
    freeze = load(paths["freeze_sha256"])
    assert qualification["status"] == "HELDOUT_QUALIFIED"
    assert qualification["study_evaluation_allowed"] is True
    assert qualification["freeze"]["sha256"] == release["freeze_sha256"]
    assert freeze["model"] == {
        "requested_id": "gpt-6-luna",
        "substitution_allowed": False,
        "reasoning_effort": "high",
        "provider": "codex-lb",
        "temperature": None,
        "seed": None,
    }
    assert freeze["prompt_sha256"] == release["prompt_sha256"]
    assert freeze["output_schema_sha256"] == release["output_schema_sha256"]
    assert freeze["caller_source_sha256"] == release["caller_sha256"]

    packet = manifest["packet_and_blinding"]
    assert packet["builder_sha256"] == digest(ROOT / packet["builder"])
    assert packet["condition_identity_visible_to_judge"] is False
    assert packet["evaluator_truth_visible_to_judge"] is False
    assert packet["proposed_certificate_plan_and_verifier_visible_to_judge"] is False
    execution = manifest["judge_execution"]
    assert execution["passes"] == ["pass-1", "pass-2"]
    assert execution["planned_judgments"] == 36
    assert execution["judge_calls_at_freeze"] == 0
    assert execution["usable_judgment_retry_allowed"] is False


def test_only_four_atomic_mechanism_cases_enter_primary_endpoint() -> None:
    manifest = load(MANIFEST)
    eligible = [item["case_id"] for item in manifest["cases"] if item["primary_endpoint_eligible"]]
    assert eligible == manifest["scoring"]["primary_endpoint_cases"]
    assert len(eligible) == 4
    assert manifest["prior_exposure"]["candidate_p_responses_generated"] == 0
    assert manifest["prior_exposure"]["baseline_r_responses_generated"] == 0
    assert manifest["prior_exposure"]["luna_study_judgments_generated"] == 0
