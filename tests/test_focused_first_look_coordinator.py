import json
from pathlib import Path

from focused_first_look_coordinator import cluster_rows, decorate_pair


def test_decorate_preserves_outputs_and_adds_packet_contract():
    pair = {"schema": "crane-focused-supported-diagnostic-response-pair/v1", "episode_id": "e",
            "family": "persistent_command_motion_discrepancy", "outputs": [{"condition": "P", "text": "p"}, {"condition": "R", "text": "r"}]}
    ref = {"episode_id": "e", "allowed_evidence_identifiers": ["events-sha256:" + "a" * 64]}
    out = decorate_pair(pair, ref, "q")
    assert out["outputs"] == pair["outputs"]
    assert out["question_id"] == "q"
    assert out["permitted_evidence_identifiers"] == ref["allowed_evidence_identifiers"]


def test_disagreement_is_adverse_in_least_favourable_payload(tmp_path: Path):
    rows = []
    entries = []
    report = {"cache_keys": {"pass-1": {}, "pass-2": {}}}
    for condition in ("P", "R"):
        rid = "id-" + condition
        units = ["mechanism", "measurement", "outcome", "limit"]
        rows.append({"response_id": rid, "primary_endpoint_eligible": True,
                     "mechanism_unit_id": units[0], "complete_endpoint_unit_ids": units})
        entries.append({"response_id": rid, "condition": condition})
        for pass_id, covered in (("pass-1", True), ("pass-2", False)):
            key = f"{pass_id}-{condition}"
            # The frozen Luna runner keys its summary by opaque response ID, not condition.
            report["cache_keys"][pass_id][rid] = key
            path = tmp_path / pass_id / f"{key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"status": "VALID", "judgment": {
                "material_error": False,
                "required_units": [{"unit_id": u, "status": "covered" if covered else "omitted"} for u in units],
            }}))
    result = cluster_rows(packet_rows=rows, key={"entries": entries}, report=report,
                          cache_root=tmp_path, cluster_id="c", configuration_id="x",
                          family="persistent_command_motion_discrepancy", sequence_index=1)
    lower = result["rows"]["least_favourable"]
    upper = result["rows"]["most_favourable"]
    assert lower["complete_supported_diagnostic_communication_p"] == 0
    assert lower["complete_supported_diagnostic_communication_r"] == 1
    assert upper["complete_supported_diagnostic_communication_p"] == 1
    assert upper["complete_supported_diagnostic_communication_r"] == 0
    assert result["unresolved"]
