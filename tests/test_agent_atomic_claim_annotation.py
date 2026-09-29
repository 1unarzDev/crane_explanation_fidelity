from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_agent_atomic_claim_annotation_packets import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from run_evidence_calibration_agent_annotation import run  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "packet_fixtures", ROOT / "tests/test_atomic_claim_annotation_packets.py"
)
FIXTURES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FIXTURES)


def test_agent_packet_preserves_blinding_and_declares_qualification_gate() -> None:
    packet, key = build(*FIXTURES.inputs(), "development-blinding-secret-v1")
    assert packet["schema"] == "crane-blinded-agent-atomic-annotation-packet-set/v1"
    assert packet["annotation_origin"] == "automated_agent"
    assert packet["independent_agent_invocations_required"] == 2
    assert "independent_annotator_count_required" not in packet
    assert packet["qualification_status"].endswith("BEFORE_PRIMARY_SCORING")
    assert key["packet_set_sha256"] == canonical_sha256(packet)
    assert key["annotation_origin"] == "automated_agent"


class FakeCaller:
    def __init__(self, disagree: bool = True) -> None:
        self.roles: list[str] = []
        self.disagree = disagree

    def call(self, *, logical_role, payload, schema, prompt):
        self.roles.append(logical_role)
        if logical_role == "atomic-agent-C":
            disagreement = payload["handoff"]["disagreements"][0]
            parsed = {
                "schema": "crane-blinded-atomic-annotation-adjudication/v1",
                "agreement_report_sha256": payload["handoff"]["agreement_report_sha256"],
                "adjudicator_id": "agent-C-luna-v1",
                "decisions": [{
                    "disagreement_id": disagreement["disagreement_id"],
                    "selected_value": disagreement["annotator_a_value"],
                    "rationale": "The supplied robot-visible evidence directly supports this statement.",
                }],
                "attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE",
            }
        else:
            form = payload["form"]
            slot = form["annotator_slot"]
            labels = []
            for index, item in enumerate(form["atomic_statements"]):
                label = "SUPPORTED_BY_VISIBLE_EVIDENCE"
                if self.disagree and slot == "B" and index == 0:
                    label = "INSUFFICIENT_VISIBLE_EVIDENCE"
                labels.append({"item_id": item["item_id"], "label": label, "annotation_notes": None})
            parsed = {
                "schema": "crane-blinded-atomic-annotation-return/v1",
                "packet_set_sha256": payload["packet_set_sha256"],
                "form_id": form["form_id"],
                "packet_id": form["packet_id"],
                "annotator_slot": slot,
                "annotator_id": f"agent-{slot}-luna-v1",
                "atomic_labels": labels,
                "required_unit_coverage": [
                    {"unit_prompt": item["unit_prompt"], "communicated": True, "response_span": "exact span"}
                    for item in form["required_unit_coverage"]
                ],
                "highest_asserted_abstraction_level": "execution_discrepancy",
                "limitation_preservation": [
                    {"limitation_prompt": item["limitation_prompt"], "preserved": False, "response_span": None}
                    for item in form["limitation_preservation"]
                ],
                "false_premise_handling": "NOT_APPLICABLE",
                "annotator_attestation": "INDEPENDENT_BLINDED_COMPLETE",
            }
        return {"cache_key": logical_role, "parsed_final": parsed}


def test_runner_uses_two_agent_calls_and_disagreement_only_third(tmp_path: Path) -> None:
    packet, _ = build(*FIXTURES.inputs(), "development-blinding-secret-v1")
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    caller = FakeCaller()
    summary = run(packet_path, tmp_path / "out", caller=caller)
    assert caller.roles == ["atomic-agent-A", "atomic-agent-B", "atomic-agent-C"]
    assert summary["agent_assessed"] is True
    assert summary["human_annotations_collected"] == 0
    assert summary["adjudication_agent_invoked"] is True
    assert summary["confirmation_independent_n"] == 0


def test_runner_does_not_invoke_agent_c_when_passes_agree(tmp_path: Path) -> None:
    packet, _ = build(*FIXTURES.inputs(), "development-blinding-secret-v1")
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(__import__("json").dumps(packet), encoding="utf-8")
    caller = FakeCaller(disagree=False)
    summary = run(packet_path, tmp_path / "out", caller=caller)
    assert caller.roles == ["atomic-agent-A", "atomic-agent-B"]
    assert summary["adjudication_agent_invoked"] is False
    assert summary["finalized"] is True
    assert (tmp_path / "out/final.json").is_file()
