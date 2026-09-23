import hashlib
import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "join_legacy_annotation_key.py"
SPEC = importlib.util.spec_from_file_location("join_legacy_annotation_key", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def fixtures(tmp_path):
    packet = tmp_path / "packet.jsonl"
    ids = ("0123456789abcdef01234567", "1123456789abcdef01234567")
    packet.write_text(
        "".join(json.dumps({"response_id": value}) + "\n" for value in ids),
        encoding="utf-8",
    )
    labels = {
        value: {
            "response_id": value,
            "episode_id": MODULE.BLINDED_METADATA_SENTINEL,
            "scenario_family": MODULE.BLINDED_METADATA_SENTINEL,
            "condition_blinded_id": value,
            "question_kind": "failure-cause",
            "evidence_problem": False,
        }
        for value in ids
    }
    adjudication = {
        "schema": "crane-explain-annotation-adjudication/v1",
        "status": "COMPLETE",
        "condition_key_joined": False,
        "evidence_problem_quarantined_responses": [],
        "labels": labels,
    }
    key = {
        "schema": "crane-explain-blinded-annotation-key/v1",
        "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
        "entries": [
            {
                "response_id": value,
                "episode_id": "pn-0001-worker-0",
                "question_kind": "failure-cause",
                "condition": condition,
                "arm": "primary",
                "model": "model",
                "result_path": f"result-{condition}.json",
            }
            for value, condition in zip(ids, ("F", "G"))
        ],
    }
    split = {
        "schema": "crane-provenance-final-split/v1",
        "instances": [
            {
                "opaque_episode_id": "pn-0001",
                "scenario_family": "terminal_recovery_abort",
            }
        ],
    }
    return packet, adjudication, key, split, ids


def test_join_restores_metadata_only_after_complete_adjudication(tmp_path):
    packet, adjudication, key, split, _ = fixtures(tmp_path)
    rows, report = MODULE.join(adjudication, key, split, packet)
    assert {row["condition"] for row in rows} == {"F", "G"}
    assert {row["episode_id"] for row in rows} == {"pn-0001-worker-0"}
    assert {row["scenario_family"] for row in rows} == {"terminal_recovery_abort"}
    assert report["condition_key_joined"] is True
    assert report["analysis_responses"] == 2
    assert report["quarantined_episodes"] == []


def test_join_applies_whole_episode_quarantine(tmp_path):
    packet, adjudication, key, split, ids = fixtures(tmp_path)
    adjudication["labels"][ids[0]]["evidence_problem"] = True
    rows, report = MODULE.join(adjudication, key, split, packet)
    assert rows == []
    assert report["quarantined_episodes"] == ["pn-0001-worker-0"]
    assert report["quarantined_responses"] == 2


def test_join_preserves_either_annotators_evidence_problem_flag(tmp_path):
    packet, adjudication, key, split, ids = fixtures(tmp_path)
    adjudication["evidence_problem_quarantined_responses"] = [ids[1]]
    rows, report = MODULE.join(adjudication, key, split, packet)
    assert rows == []
    assert report["quarantined_episodes"] == ["pn-0001-worker-0"]


def test_join_rejects_incomplete_or_unblinded_input(tmp_path):
    packet, adjudication, key, split, ids = fixtures(tmp_path)
    adjudication["status"] = "AWAITING_ADJUDICATION"
    try:
        MODULE.join(adjudication, key, split, packet)
    except ValueError as error:
        assert "not complete" in str(error)
    else:
        raise AssertionError("incomplete adjudication was accepted")

    adjudication["status"] = "COMPLETE"
    adjudication["labels"][ids[0]]["episode_id"] = "pn-0001-worker-0"
    try:
        MODULE.join(adjudication, key, split, packet)
    except ValueError as error:
        assert "pre-join episode" in str(error)
    else:
        raise AssertionError("pre-joined episode metadata was accepted")
