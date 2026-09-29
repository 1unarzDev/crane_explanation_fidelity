from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_agent_qualification import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from run_evidence_calibration_agent_qualification import aggregate, gates_pass, run, score_case  # noqa: E402


def test_frozen_suite_hash_and_required_threat_coverage() -> None:
    suite = build()
    frozen = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v1-freeze.json").read_text())
    assert suite["split_counts"] == {"development": 4, "heldout": 16}
    assert canonical_sha256(suite) == frozen["qualification_suite_sha256"]
    tags = {tag for case in suite["cases"] if case["split"] == "heldout" for tag in case["threat_tags"]}
    assert {"physically_true_unsupported", "insufficient_vs_contradicted", "supported_partial", "over_abstention", "recovery_vs_outcome_causation", "false_premise", "valid_extra_fact", "prompt_injection"} <= tags


def test_perfect_returns_pass_all_frozen_gates() -> None:
    suite = build()
    rows = []
    for case in suite["cases"]:
        expected = case["expected"]
        returned = {
            "atomic_labels": [{**item, "annotation_notes": None} for item in expected["atomic_labels"]],
            "required_unit_coverage": expected["required_unit_coverage"],
            "highest_asserted_abstraction_level": expected["highest_asserted_abstraction_level"],
            "limitation_preservation": expected["limitation_preservation"],
            "false_premise_handling": expected["false_premise_handling"],
        }
        rows.append(score_case(case, returned))
    metrics = aggregate(rows, "heldout")
    freeze = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v1-freeze.json").read_text())
    passed, checks = gates_pass(metrics, freeze["heldout_gates"])
    assert passed and all(checks.values())
    assert metrics["atomic_n"] > 16


def test_physical_truth_is_not_allowed_to_repair_missing_visible_support() -> None:
    case = next(item for item in build()["cases"] if item["case_id"] == "qa-ho-02")
    expected = case["expected"]
    wrong = {
        "atomic_labels": [{"item_id": expected["atomic_labels"][0]["item_id"], "label": "SUPPORTED_BY_VISIBLE_EVIDENCE", "annotation_notes": None}],
        "required_unit_coverage": expected["required_unit_coverage"],
        "highest_asserted_abstraction_level": expected["highest_asserted_abstraction_level"],
        "limitation_preservation": expected["limitation_preservation"],
        "false_premise_handling": expected["false_premise_handling"],
    }
    row = score_case(case, wrong)
    assert row["atomic"][0]["correct"] is False


def test_full_qualification_uses_two_separate_pass_caches_and_scores_without_gold_leakage(tmp_path: Path) -> None:
    suite = build()
    suite_path = tmp_path / "suite.json"
    suite_path.write_text(json.dumps(suite), encoding="utf-8")
    freeze = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v1-freeze.json").read_text())
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    expected_by_case = {case["case_id"]: case["expected"] for case in suite["cases"]}
    caches = []

    class PerfectCaller:
        def __init__(self, cache: Path):
            caches.append(cache)

        def call(self, *, logical_role, payload, schema, prompt):
            case_id = logical_role.split("qualification-", 1)[1].split("-qa-", 1)[1]
            case_id = "qa-" + case_id
            expected = expected_by_case[case_id]
            form = payload["form"]
            parsed = {
                "schema": "crane-blinded-atomic-annotation-return/v1",
                "packet_set_sha256": payload["packet_set_sha256"],
                "form_id": form["form_id"],
                "packet_id": form["packet_id"],
                "annotator_slot": form["annotator_slot"],
                "annotator_id": payload["agent_identity"],
                "atomic_labels": [{**item, "annotation_notes": None} for item in expected["atomic_labels"]],
                "required_unit_coverage": expected["required_unit_coverage"],
                "highest_asserted_abstraction_level": expected["highest_asserted_abstraction_level"],
                "limitation_preservation": expected["limitation_preservation"],
                "false_premise_handling": expected["false_premise_handling"],
                "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
            }
            assert "expected" not in json.dumps(payload)
            return {"parsed_final": parsed, "cache_key": logical_role}

    result = run(suite_path, freeze_path, tmp_path / "out", caller_factory=PerfectCaller)
    assert result["status"] == "QUALIFIED"
    assert caches == [tmp_path / "out/pass-A/calls", tmp_path / "out/pass-B/calls"]
