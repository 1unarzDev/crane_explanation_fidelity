from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "analysis" / "run_luna_judge_qualification_v5.py"
SUITE = ROOT / "research" / "explanation_fidelity" / "qualification" / "luna-model-judge-v7-cases.json"
FREEZE = (
    ROOT
    / "research"
    / "explanation_fidelity"
    / "experiment_configs"
    / "prospective"
    / "luna-model-judge-v7-reference-audited-freeze.json"
)
SPEC = importlib.util.spec_from_file_location("run_luna_judge_qualification_v7", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_v7_suite_and_freeze_are_consistent() -> None:
    suite = MODULE.load_suite(SUITE)
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert hashlib.sha256(SUITE.read_bytes()).hexdigest() == freeze["suite_sha256"]
    assert freeze["qualification_suite"]["model_executions_at_freeze"] == 0
    assert freeze["hard_stop"].startswith("If either pass fails")
    assert len(suite["cases"]) == 24


def test_v7_denominators_and_perfect_reference_score() -> None:
    suite = MODULE.load_suite(SUITE)
    judgments = {
        case["case_id"]: {
            **{field: case["expected"][field] for field in MODULE.CORE_FIELDS},
            "required_units": [
                {"unit_id": unit_id, "status": status}
                for unit_id, status in case["expected"]["required_unit_statuses"].items()
            ],
        }
        for case in suite["cases"]
    }
    report = MODULE.score(suite, judgments)
    assert report["qualified"] is True
    assert report["composite"]["successes"] == 20
    assert report["composite"]["total"] == 20
    assert report["factual_false_rejections"]["total"] == 17
    assert report["unsupported_false_acceptances"]["total"] == 6


def test_v7_truthful_omissions_do_not_add_episode_events() -> None:
    suite = MODULE.load_suite(SUITE)
    by_id = {case["case_id"]: case for case in suite["cases"]}
    assert by_id["Q7H011"]["candidate_answer"] == "The measured-speed median was 0.04 m/s."
    assert by_id["Q7H012"]["candidate_answer"] == "The configured model rejected the transfer passage."
    assert by_id["Q7H017"]["candidate_answer"] == "At least one terminal predicate failed."
    assert by_id["Q7H020"]["candidate_answer"] == "I will not state a mechanism."
