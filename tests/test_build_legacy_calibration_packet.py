import importlib.util
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).parents[1] / "analysis" / "build_legacy_calibration_packet.py"
SPEC = importlib.util.spec_from_file_location("build_legacy_calibration_packet", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def result(question_kind):
    return {
        "episode_id": "land-nav-20260919-e043-worker-0",
        "evaluator_truth_available_to_methods": False,
        "question_kind": question_kind,
        "question": "Why?",
        "model": "model",
        "information_parity": {
            "runtime_presentation_sha256": "not-used-in-unit-test",
            "audit_sha256": "a" * 64,
            "accepted": True,
        },
        "outputs": [{"condition": c, "text": f"answer {c}"} for c in "FGH"],
    }


def test_opaque_ids_do_not_reveal_condition():
    assert MODULE.opaque_id("secret", "failure-cause", "F") != MODULE.opaque_id(
        "secret", "failure-cause", "G"
    )
    assert "F" not in MODULE.opaque_id("secret", "failure-cause", "F")


def test_inventory_matches_frozen_guide_counts():
    assert len(MODULE.UNIT_INVENTORIES["recovery-mechanism"]) == 8
    assert len(MODULE.UNIT_INVENTORIES["failure-cause"]) == 5


def test_cli_refuses_a_sealed_result_root(tmp_path):
    completed = subprocess.run(
        (
            sys.executable,
            str(SCRIPT),
            "--result-root",
            "model_outputs/final",
            "--packet",
            str(tmp_path / "packet.jsonl"),
            "--key",
            str(tmp_path / "key.json"),
        ),
        cwd=SCRIPT.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "development-only e043" in completed.stderr
