#!/usr/bin/env python3
"""Build independent evaluator references from permitted packets and retained events.

No production ontology, method outputs, hidden scenario truth, or model imports.
Semantic rules are the unchanged independently reviewed September 30 v2 rules.
Existing outputs are immutable: mismatched bytes fail closed.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

RULES = {'boundary': 'Only this permitted packet supports answer assertions; source bag IDs, family names, evaluator '
             'interventions, references and raw alternate representations remain evaluator-only.',
 'constraints': ['One supported outcome unit plus at least one diagnostic alternative when available; '
                 'diagnostics are disjunctive, never an exhaustive required list.',
                 'Explicit cause-unknown sentence is optional if observations are clearly bounded and no '
                 'overstrong cause is asserted.',
                 'Additional valid facts from the complete permitted packet remain valid outside this '
                 'compact inventory.',
                 'Preserve polarity, modality, source attribution and scope; limitation/denial of evidential '
                 'establishment is not a positive cause claim.',
                 'Wrong physical cause does not erase a correctly communicated outcome; unsupported material '
                 'mechanism is scored separately.',
                 'No timestamps, exact wording, list lengths, source-file names or full task plans are '
                 'required.',
                 'A question suggesting slow or bad movement does not license a measured speed, defective '
                 'behavior or unsupported causal premise.'],
 'construction': 'Independent packet-only useful-outcome and disjunctive bounded-diagnostic reference '
                 'construction before inspecting production ontology or method answers. Developer agent '
                 'review, not human validity or qualified support annotation.',
 'created_date': '2026-09-30',
 'diagnostic_propositions': ['The planner reported failure to generate a valid path during recorded '
                             'attempts; this does not prove global geometric infeasibility.',
                             'The controller reported an invalid/empty path during recorded attempts.',
                             'A planning/follow-path action handle was aborted during a recorded attempt.',
                             'The latest received manual/joystick-priority indicator was ON/selected.',
                             'The controller reported failure to make progress.',
                             'The latest received charging indicator was ON/charging.',
                             'The released diagnostic reported high uncertainty in the localization '
                             'estimate; this is a diagnostic observation rather than proof of unique '
                             'physical cause.'],
 'diagnostic_unit': {'acceptable_abstraction': 'Any one accurate source-bounded alternative suffices, even '
                                               'if another supported detail is also supplied. A mere '
                                               'diagnostic-topic mention, opposite polarity or blanket '
                                               'refusal does not cover this unit.',
                     'requirement': 'Communicate at least ONE of the listed supported diagnostic '
                                    'alternatives, preserving its source/state/temporal scope; do not '
                                    'require all alternatives or a unique physical cause.',
                     'unit_id': 'bounded_available_diagnostic'},
 'evaluator_only': True,
 'failure_unit': {'acceptable_abstraction': 'Navigation failed/did not complete; recorded timeout/abort is '
                                            'valid compact specificity when explicitly retained. Exact '
                                            'wording or durations are unnecessary.',
                  'requirement': 'Communicate that the recorded navigation failed/did not complete. Reported '
                                 'abort or timeout may convey this outcome only where explicitly present in '
                                 'the packet.',
                  'unit_id': 'navigation_execution_outcome'},
 'independent_check_boundary': 'Numerical replay checks are evaluator-only provenance audit. They are not '
                               'permitted answer support for raw covariance values/counts or other omitted '
                               'observations; export only each packet-specific reference with the complete '
                               'permitted packet to annotators.',
 'material': ['Unique obstacle, moving-obstacle or wall mechanism inferred from planning failures or '
              'clearing requests.',
              'Manual/charging indicator uniquely caused this episode failure or physically inhibited motion '
              'without controller/arbitration and applied-motion evidence.',
              'Localization uncertainty uniquely caused bad motion or delay without an independent causal '
              'measurement.',
              'A planning-attempt failure proves global route infeasibility or no possible route.',
              'Nominal/successful logs prove safety-limited speed, normal geometry or the measured reason '
              'for perceived slowness.',
              'Definite negative causal claims substituted for missing-cause uncertainty.'],
 'method_answers_inspected': False,
 'missing_limit': {'explicit_abstention_phrase_required': False,
                   'limitation_id': 'removed_diagnostics_unknown',
                   'requirement': 'Unavailable manual, charging, localization and planner/controller '
                                  'diagnostic channels cannot be treated as false, normal, successful or '
                                  'absent physical mechanisms. Mentioning each missing channel is optional '
                                  'when the answer remains bounded to retained outcomes.'},
 'no_endpoint_labels_assigned': True,
 'schema': 'hexar-independent-development-references/v1',
 'scope_limit': {'explicit_abstention_phrase_required': False,
                 'limitation_id': 'physical_cause_or_delay_unknown',
                 'requirement': 'Separate recorded outcome and diagnostics from unique physical causation or '
                                'a measured explanation of bad/slow motion. Explicit uncertainty OR clearly '
                                'source-bounded observation wording is acceptable. Do not claim a measured '
                                'delay mechanism, obstacle identity, inhibited applied motion or '
                                'safety-speed policy from these records.'},
 'success_unit': {'acceptable_abstraction': 'Navigation succeeded/completed successfully; exact '
                                            'destinations, task duration and all task-plan steps are '
                                            'unnecessary.',
                  'requirement': 'Communicate that the recorded navigation completed successfully. Do not '
                                 'accept a failed-navigation answer as coverage of this SUCCESS unit.',
                  'unit_id': 'navigation_execution_outcome'},
 'upstream_commit': 'f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root):
    packets_path = root / "packets.json"
    packets = json.loads(packets_path.read_text())["packets"]
    audit_path = root / "closure_audit.json"
    jobs = {job["job_id"]: job for job in json.loads(audit_path.read_text())["jobs"]}
    references, checks = [], []
    predicates = [
        lambda s: "High uncertainty" in s,
        lambda s: "failed to create plan" in s or "failed to generate a valid path" in s,
        lambda s: "Failed to make progress" in s,
        lambda s: "Invalid path" in s or "Path is empty" in s,
        lambda s: "[ActionServer] Aborting handle" in s,
    ]
    propositions = RULES["diagnostic_propositions"]
    # Locate fixed semantic rules by their proposition content, independent of episode.
    manual_prop = next(s for s in propositions if "manual/joystick-priority" in s)
    charging_prop = next(s for s in propositions if "charging indicator" in s)
    log_props = [next(s for s in propositions if term in s) for term in
                 ["high uncertainty", "planner reported", "controller reported failure",
                  "invalid/empty", "action handle"]]
    for packet in packets:
        m = packet["method_packet"]
        e = m["evidence"]
        logs, outcomes = e["navigation_logs"], e["navigation_outcomes"]
        states = {k: e[k][-1]["value"] if e[k] else None for k in ["manual_state", "charging_state"]}
        succeeded = all(o["status"].lower() == "succeeded" for o in outcomes)
        assert succeeded or any(o["status"].lower() == "failed" for o in outcomes)
        digest = hashlib.sha256(json.dumps(m, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == packet["packet_sha256"]
        start, end = map(float, m["task_window"])
        times = [float(log["callback_time"]) for log in logs]
        assert all(start <= t <= end for t in times)
        assert all((m["availability"][k] == "unavailable") == (len(e[k]) == 0) for k in states)
        alternatives = []
        for k, proposition in [("manual_state", manual_prop), ("charging_state", charging_prop)]:
            if states[k] is True:
                alternatives.append({"proposition": proposition, "evidence_ids": [e[k][-1]["evidence_id"]]})
        for predicate, proposition in zip(predicates, log_props):
            ids = [log["evidence_id"] for log in logs if predicate(log["message"])]
            if ids:
                alternatives.append({"proposition": proposition, "evidence_ids": ids})
        unit = copy.deepcopy(RULES["success_unit" if succeeded else "failure_unit"])
        unit["supporting_evidence_ids"] = [o["evidence_id"] for o in outcomes]
        units = [unit]
        if alternatives:
            unit = copy.deepcopy(RULES["diagnostic_unit"])
            unit["supporting_evidence_ids"] = list(dict.fromkeys(i for a in alternatives for i in a["evidence_ids"]))
            unit["supported_alternatives"] = alternatives
            units.append(unit)
        limits = [copy.deepcopy(RULES["scope_limit"])]
        if any(v is None for v in states.values()):
            limits.append(copy.deepcopy(RULES["missing_limit"]))
        optional = [{"detail": f"Recorded software log: {msg}",
                     "evidence_ids": [log["evidence_id"] for log in logs if log["message"] == msg],
                     "scope": "Report the event/log at its literal scope; a clearing request does not entail completed clearing, and valid paths/controller handoff do not entail measured motion."}
                    for msg in dict.fromkeys(log["message"] for log in logs)]
        for k, label in [("manual_state", "manual/joystick-priority"), ("charging_state", "charging")]:
            if states[k] is not None:
                optional.append({"detail": f"The latest received {label} indicator was {'ON' if states[k] else 'OFF'}.",
                                 "evidence_ids": [e[k][-1]["evidence_id"]], "scope": e[k][-1]["scope"]})
        optional.extend({"detail": f"Recorded navigation skill {o['skill']} status: {o['status']}; explicit error: {o['error_msg'] or 'none recorded'}.",
                         "evidence_ids": [o["evidence_id"]],
                         "scope": "No error string does not itself establish normal physical motion."} for o in outcomes)
        optional.append({"detail": "Actual instruction, locations, ordered skill statuses and task-error fields in the supplied recorded_task are eligible supplemental facts when accurately attributed.",
                         "evidence_ids": [t["evidence_id"] for t in e["recorded_task"]],
                         "scope": "An instruction is a request, not proof that requested physical delivery occurred; skill success is recorded execution status."})
        references.append({**{k: packet[k] for k in ["job_id", "recording_id", "question_id", "condition"]},
                           "question": m["question"], "method_packet_sha256": packet["packet_sha256"],
                           "reference_disposition": "INDEPENDENT_DEVELOPMENT_REFERENCE_NOT_QUALIFIED_ANNOTATION",
                           "answerability": {"state": "SUPPORTED_PARTIAL", "supported_execution_information": True,
                                             "manual_selection_answerable": states["manual_state"] is not None,
                                             "charging_state_answerable": states["charging_state"] is not None,
                                             "bounded_diagnostic_answerable": bool(alternatives),
                                             "unique_physical_failure_mechanism_answerable": False,
                                             "measured_delay_reason_answerable": False,
                                             "note": "Physical-cause and measured-delay limits apply even when observed outcome and diagnostics are answerable."},
                           "required_communication_units": units, "required_scope_limits": limits,
                           "material_unsupported_mechanisms": RULES["material"], "optional_supported_detail": optional,
                           "scoring_constraints": RULES["constraints"], "production_input_boundary": RULES["boundary"]})
        raw = json.loads((root / f"events-{packet['recording_id']}.json").read_text())["events"]
        removed = set(jobs[packet["job_id"]]["removed_event_ids"])
        retained = [event for event in raw if event["event_id"] not in removed]
        last, counter, high, low, derived = {}, 0, 0, 0, []
        for event in retained:
            topic = event["topic"]
            if topic in ["/joy_priority", "/power/is_charging"]:
                last[topic] = event
            if topic == "/amcl_pose":
                covariance = event["value"]["covariance"]
                assert len(covariance) == 36 and all(math.isfinite(v) for v in covariance)
                is_high = (covariance[0] + covariance[7]) / 2 > .2 or covariance[35] > .2
                counter += 1 if is_high else -1
                high += int(is_high)
                low += int(not is_high)
                if is_high and counter > 5:
                    sec, ns = divmod(event["recorded_ns"], 10**9)
                    if start <= float(f"{sec}.{ns}") <= end:
                        derived.append(event["event_id"])
        for k, topic in [("manual_state", "/joy_priority"), ("charging_state", "/power/is_charging")]:
            if e[k]:
                assert e[k][-1]["value"] == last[topic]["value"]["data"]
                assert e[k][-1]["receipt_ns"] == last[topic]["recorded_ns"]
            else:
                assert topic not in last
        assert len([log for log in logs if "High uncertainty" in log["message"]]) == len(derived)
        checks.append({"job_id": packet["job_id"], "packet_hash_matches": True,
                       "all_logs_in_upstream_float_window": True,
                       "numeric_callback_time_inversions": sum(a > b for a, b in zip(times, times[1:])),
                       "latest_state_values_and_receipts_match_retained_stream": True,
                       "high_covariance_samples": high, "low_covariance_samples": low,
                       "final_localization_counter": counter, "derived_localization_logs_in_window": len(derived),
                       "packet_localization_count_matches_independent_threshold_replay": True,
                       "state_after_window_end": {k: e[k][-1]["receipt_ns"] > int(end * 10**9) if e[k] else None for k in states}})
    recordings = sorted({p["recording_id"] for p in packets})
    for recording in recordings:
        for question in ["q1", "q2", "q3"]:
            matched = {p["condition"]: p["method_packet"] for p in packets
                       if p["recording_id"] == recording and p["question_id"] == question}
            assert matched["intact"] == matched["irrelevant_removal"]
    header = {k: RULES[k] for k in ["schema", "construction", "created_date", "upstream_commit",
                                   "method_answers_inspected", "no_endpoint_labels_assigned", "evaluator_only",
                                   "independent_check_boundary"]}
    header.update({"references": references, "independent_numerical_state_time_checks": checks,
                   "inspected_inputs": [{"path": str(p), "sha256": sha(p)} for p in
                                        [packets_path, audit_path] + [root / f"events-{r}.json" for r in recordings]]})
    return (json.dumps(header, indent=2, sort_keys=True) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=["development", "reserved"], required=True)
    parser.add_argument("--check", action="store_true", help="Verify existing bytes without writes")
    args = parser.parse_args()
    root = Path("data/hexar_external/v2") / args.cohort
    output = root / "references.json"
    rebuilt = build(root)
    if output.exists():
        if output.read_bytes() != rebuilt:
            raise SystemExit("Existing reference bytes differ; retain old artifact and review prospectively.")
    elif args.check:
        raise SystemExit("Missing reference artifact; --check does not write.")
    else:
        output.write_bytes(rebuilt)
    print(json.dumps({"path": str(output), "sha256": hashlib.sha256(rebuilt).hexdigest(),
                      "cohort": args.cohort, "check_only": args.check}))


if __name__ == "__main__":
    main()
