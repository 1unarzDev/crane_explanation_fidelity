from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from run_evidence_calibration_b2_pilot import _materialize
from realize_evidence_calibrated_explanation_v3 import realize
from evidence_calibration_io import canonical_sha256


def inputs(condition_id):
    pilot = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
    schedule = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
    entry, _, family = _materialize(ROOT, pilot, schedule, condition_id)
    contract = dict(question_id=family + "-question-v1-development", failure_premise=True,
                    required_mechanism_families=["false_premise"] if family == "nominal_false_premise" else ["command_motion"])
    return ontology, entry, contract


def test_evidence_removal_loses_trace_and_motion_but_retains_reported_error():
    low = realize(*inputs("cm-land-conf-045-E0"))
    high = realize(*inputs("cm-land-conf-045-E3"))
    ids = lambda output: {row["contract_id"] for row in output["clauses"]}
    assert "reported-progress-failure" in ids(low) & ids(high)
    assert "software-execution-trace" not in ids(low)
    assert "software-execution-trace" in ids(high)
    assert "claim-command-motion-discrepancy" not in ids(low)
    assert "claim-command-motion-discrepancy" in ids(high)


def test_nominal_motion_diagnostic_does_not_negate_actual_software_failures():
    output = realize(*inputs("cm-land-conf-072-E2"))
    assert "2 FollowPath failures" in output["answer"]
    assert "does not rule out intermediate software action failures" in output["answer"]
    assert "failure premise is rejected" not in output["answer"]


def test_recovery_measurement_is_retained_even_when_task_aborts():
    output = realize(*inputs("cm-land-conf-047-E3"))
    assert "recorded navigation action aborted" in output["answer"]
    assert "later 30–31 s interval" in output["answer"]
    assert "does not establish or cause the eventual task outcome" in output["answer"]


def test_unbound_trace_cannot_supply_new_software_diagnosis():
    ontology, entry, contract = inputs("cm-land-conf-045-E1")
    entry = deepcopy(entry)
    entry["method_packet"]["evidence"]["behavior_tree_transitions"]["execution_sequence"]["recovery_node_classifier"]["policy_sha256"] = "unbound-policy"
    entry["condition"]["method_packet_sha256"] = canonical_sha256(entry["method_packet"])
    output = realize(ontology, entry, contract)
    assert not any(row["contract_id"] == "software-execution-trace" for row in output["clauses"])
