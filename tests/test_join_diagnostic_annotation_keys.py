import hashlib
import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "join_diagnostic_annotation_keys.py"
SPEC = importlib.util.spec_from_file_location("join_diagnostic_annotation_keys", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixtures(tmp_path):
    packet = tmp_path / "packet.jsonl"
    packet.write_text(
        json.dumps(
            {
                "response_id": "r1",
                "question_kind": "diagnosis",
                "diagnosable": True,
                "reference_status": "DEVELOPMENT",
            }
        )
        + "\n"
    )
    key = tmp_path / "key.json"
    key.write_text(
        json.dumps(
            {
                "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
                "entries": [
                    {
                        "response_id": "r1",
                        "condition": "P",
                        "episode_id": "episode-mask",
                        "question_id": "question",
                        "provider": "provider",
                        "model": "model",
                        "used_template_fallback": True,
                        "verification_accepted": False,
                    }
                ],
            }
        )
    )
    inventory = {
        "schema": "crane-diagnostic-development-annotation-inventory/v1",
        "packets": [
            {
                "name": "masked",
                "packet": str(packet),
                "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
                "key": str(key),
                "key_sha256": hashlib.sha256(key.read_bytes()).hexdigest(),
                "statistical_cluster_id": "episode",
                "evidence_variant": "masked",
            }
        ],
    }
    label = {"response_id": "r1", "evidence_problem": False}
    adjudication = {
        "schema": "crane-diagnostic-annotation-adjudication/v1",
        "status": "COMPLETE",
        "condition_key_joined": False,
        "evidence_problem_quarantined_responses": [],
        "labels": {"r1": label},
    }
    return inventory, adjudication


def test_join_preserves_cluster_for_mask_and_fallback_metadata(tmp_path):
    inventory, adjudication = fixtures(tmp_path)
    rows, report = MODULE.join(inventory, {"masked": adjudication})
    assert rows[0]["source_episode_id"] == "episode-mask"
    assert rows[0]["statistical_cluster_id"] == "episode"
    assert rows[0]["evidence_variant"] == "masked"
    assert rows[0]["condition"] == "P"
    assert rows[0]["used_template_fallback"] is True
    assert rows[0]["diagnosable"] is True
    assert report["input_statistical_clusters"] == 1


def test_evidence_problem_quarantines_complete_cluster(tmp_path):
    inventory, adjudication = fixtures(tmp_path)
    adjudication["evidence_problem_quarantined_responses"] = ["r1"]
    rows, report = MODULE.join(inventory, {"masked": adjudication})
    assert rows == []
    assert report["quarantined_statistical_clusters"] == ["episode"]
    assert report["quarantined_responses"] == 1


def test_join_refuses_incomplete_adjudication(tmp_path):
    inventory, adjudication = fixtures(tmp_path)
    adjudication["status"] = "AWAITING_ADJUDICATION"
    try:
        MODULE.join(inventory, {"masked": adjudication})
    except ValueError as error:
        assert "not complete" in str(error)
    else:
        raise AssertionError("incomplete diagnostic adjudication was accepted")
