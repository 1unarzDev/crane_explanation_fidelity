import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "explicit-causal-restraint-successor-v1-pilot-resumption-amendment-1.json"
)


def _sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_resumption_binds_unchanged_methods_and_retained_physical_failures():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    frozen = amendment["frozen_predecessor"]
    assert _sha(frozen["schedule"]) == frozen["schedule_sha256"]
    assert _sha("analysis/compose_contract_complete_answer_v3.py") == frozen["candidate_renderer_sha256"]
    assert _sha("analysis/run_causal_restraint_successor_pair.py") == frozen["pair_runner_sha256"]
    assert _sha("analysis/run_contract_complete_response_pair.py") == frozen["base_runner_sha256"]
    assert _sha("research/explanation_fidelity/prompts/diagnostic_repository_agent_causal_restraint_v1.txt") == frozen["baseline_prompt_sha256"]
    assert _sha("analysis/audit_explicit_causal_links.py") == frozen["detector_sha256"]
    for failure in amendment["physical_disposition"]["technical_failures"]:
        assert _sha(failure["manifest"]) == failure["sha256"]


def test_resumption_reuses_exact_valid_schedule_without_confirmation_or_alpha():
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    schedule = json.loads((ROOT / amendment["frozen_predecessor"]["schedule"]).read_text())
    failures = {item["run_id"] for item in amendment["physical_disposition"]["technical_failures"]}
    valid = [item for item in schedule["stages"]["pilot"] if item["run_id"] not in failures]
    assert len(valid) == amendment["physical_disposition"]["valid_reused_development_captures"] == 18
    assert sum(item["primary_eligible_family"] for item in valid) == 14
    assert sum(not item["primary_eligible_family"] for item in valid) == 4
    for item in valid:
        assert (ROOT / "data/robot_visible/dev" / item["run_id"] / "command-motion-diagnostic-v3.json").is_file()
    assert amendment["confirmation"] == {
        "independent_n": 0,
        "alpha_bound": 0.0,
        "activation": "PROHIBITED_DURING_RESUMED_PILOT",
        "fresh_population": "Only untouched cr-conf configurations may enter a later separately frozen discovery campaign.",
        "replication_population": "cr-repl remains protected and untouched.",
    }
