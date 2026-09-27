import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/contract-complete-diagnostic-communication-v2-pilot-predeclaration.json"


def test_frozen_resources_exist_and_match_hashes():
    freeze = json.loads(FREEZE.read_text())
    for spec in freeze["frozen_resources"].values():
        path = ROOT / spec["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == spec["sha256"]
    schedule = freeze["schedule"]
    assert hashlib.sha256((ROOT / schedule["path"]).read_bytes()).hexdigest() == schedule["sha256"]


def test_pilot_is_zero_alpha_and_excludes_inspected_canary():
    freeze = json.loads(FREEZE.read_text())
    schedule = json.loads((ROOT / freeze["schedule"]["path"]).read_text())
    assert freeze["analysis"]["alpha"] == 0.0
    assert freeze["confirmation"]["activation"] == "PROHIBITED_UNTIL_POST_PILOT_ATOMIC_FREEZE"
    assert schedule["counts"] == {"controls": 4, "primary": 15, "total": 19}
    assert all(row["run_id"] != "cr-pilot-001" for row in schedule["configurations"])
