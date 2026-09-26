#!/usr/bin/env python3
"""Build fresh Luna-v11 cases aligned to the diagnostic-study endpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


THRESHOLDS = {
    "minimum_primary_endpoint_accuracy": 0.95,
    "minimum_required_unit_accuracy": 0.95,
    "minimum_scored_core_field_accuracy": 0.95,
    "maximum_false_rejection_rate": 0.05,
    "maximum_false_acceptance_rate": 0.05,
    "protected_test_failures_allowed": 0,
}
ALWAYS_CORE = ["judgment_status", "answerability", "material_error", "disposition", "correct_abstention", "causal_overclaim", "evidence_problem"]


def ev(identifier: str, fact: str) -> dict[str, str]:
    return {"id": identifier, "fact": fact}


def unit(identifier: str, text: str) -> dict[str, str]:
    return {"unit_id": identifier, "text": text}


def exp(*, answerability="answerable", material=False, disposition="full", mechanism="correct", abstention=None, causal=False, units=None):
    return {
        "judgment_status": "resolved", "answerability": answerability,
        "material_error": material, "disposition": disposition,
        "mechanism_identification": mechanism, "correct_abstention": abstention,
        "causal_overclaim": causal, "evidence_problem": False,
        "required_unit_statuses": units or {},
    }


SCENARIOS: list[dict[str, Any]] = [
    {
        "family": "persistent_discrepancy", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What execution mechanism is established from 9 to 19 seconds?",
        "completeness": "Complete for interval medians and the matched healthy comparator; component identity is unobserved.",
        "evidence": [ev("v11-a-cmd", "From 9--19 s, delivered-command median was 0.33 m/s."), ev("v11-a-motion", "From 9--19 s, measured-speed median was 0.02 m/s."), ev("v11-a-healthy", "Matched healthy measured-speed median was 0.30 m/s."), ev("v11-a-limit", "No retained measurement identifies a unique actuator, obstruction, contact, or slip cause.")],
        "units": [unit("u-measurements", "The interval medians were 0.33 m/s delivered command, 0.02 m/s measured speed, and 0.30 m/s healthy response."), unit("u-mechanism", "The bounded mechanism is a command-to-motion discrepancy."), unit("u-limit", "The unique physical cause is unresolved.")],
        "good": "From 9--19 s, the delivered-command median was 0.33 m/s and measured-speed median was 0.02 m/s, versus a 0.30 m/s matched healthy median. This establishes a command-to-motion discrepancy; the unique actuator, obstruction, contact, or slip cause remains unresolved.",
        "good_exp": exp(abstention=True, units={"u-measurements":"covered","u-mechanism":"covered","u-limit":"covered"}),
        "bad": "These values prove that wheel slip caused the robot to stop.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-measurements":"omitted","u-mechanism":"incorrect","u-limit":"incorrect"}),
    },
    {
        "family": "measured_response_recovery", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What execution mechanism changed between the two intervals, and what remained unresolved?",
        "completeness": "Complete for both interval medians; the cause of the initial low response is unobserved.",
        "evidence": [ev("v11-b-low", "From 4--10 s, command median was 0.43 m/s and measured-speed median was 0.04 m/s."), ev("v11-b-recovery", "From 13--16 s, command median was 0.41 m/s and measured-speed median was 0.38 m/s."), ev("v11-b-limit", "No retained measurement identifies the cause of the initial low response.")],
        "units": [unit("u-low", "The 4--10 s interval had low measured response relative to command."), unit("u-mechanism", "Measured command response recovered in the 13--16 s interval."), unit("u-limit", "The cause of the initial low response is unresolved.")],
        "good": "From 4--10 s, measured-speed median was 0.04 m/s for a 0.43 m/s command median. From 13--16 s, it was 0.38 m/s for a 0.41 m/s command median, establishing measured response recovery. The cause of the initial low response remains unresolved.",
        "good_exp": exp(abstention=True, units={"u-low":"covered","u-mechanism":"covered","u-limit":"covered"}),
        "bad": "The later motion proves that a temporary motor fault cleared itself.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-low":"omitted","u-mechanism":"incorrect","u-limit":"incorrect"}),
    },
    {
        "family": "geometric_model_restriction", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What bounded geometric mechanism is established in the reconstructed model?",
        "completeness": "Complete for reconstructed width, active envelope, comparison envelope, and connectivity.",
        "evidence": [ev("v11-c-width", "Reconstructed passage width was 0.81 m."), ev("v11-c-active", "The active 0.93 m envelope produced no modeled connection."), ev("v11-c-compare", "A 0.69 m comparison envelope restored modeled connectivity.")],
        "units": [unit("u-margin", "The active envelope exceeded the reconstructed passage width by 0.12 m."), unit("u-comparison", "The smaller comparison envelope restored modeled connectivity."), unit("u-mechanism", "The bounded mechanism is a configuration-specific restriction in the reconstructed navigation model."), unit("u-limit", "The computation does not establish global physical infeasibility.")],
        "good": "The active 0.93 m envelope exceeded the 0.81 m reconstructed passage by 0.12 m and produced no modeled connection; a 0.69 m comparison envelope restored connectivity. This establishes a configuration-specific restriction in the reconstructed navigation model, not global physical infeasibility.",
        "good_exp": exp(abstention=True, units={"u-margin":"covered","u-comparison":"covered","u-mechanism":"covered","u-limit":"covered"}),
        "bad": "The comparison proves that the physical environment was globally impassable.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-margin":"omitted","u-comparison":"omitted","u-mechanism":"incorrect","u-limit":"incorrect"}),
    },
    {
        "family": "execution_abort_matched_symptom", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What bounded mechanism preceded this abort?",
        "completeness": "Complete for reconstructed connectivity and interval medians; unique cause is unobserved.",
        "evidence": [ev("v11-d-route", "The active envelope retained modeled connectivity."), ev("v11-d-cmd", "From 17--25 s, delivered-command median was 0.35 m/s."), ev("v11-d-motion", "From 17--25 s, measured-speed median was 0.01 m/s."), ev("v11-d-result", "The action aborted after controller failure."), ev("v11-d-limit", "No retained measurement identifies a unique physical cause.")],
        "units": [unit("u-route", "The reconstructed model retained connectivity."), unit("u-response", "The interval medians were 0.35 m/s delivered command and 0.01 m/s measured speed."), unit("u-mechanism", "The bounded mechanism is a command-to-motion discrepancy."), unit("u-limit", "The unique physical cause is unresolved.")],
        "good": "The reconstructed model retained connectivity. From 17--25 s, delivered-command median was 0.35 m/s while measured-speed median was 0.01 m/s, establishing a command-to-motion discrepancy. The unique physical cause remains unresolved.",
        "good_exp": exp(abstention=True, units={"u-route":"covered","u-response":"covered","u-mechanism":"covered","u-limit":"covered"}),
        "bad": "The abort proves that geometry eliminated every route.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-route":"incorrect","u-response":"omitted","u-mechanism":"incorrect","u-limit":"omitted"}),
    },
    {
        "family": "representation_inconsistency", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What perception/model mechanism is established at 62 seconds?",
        "completeness": "Complete for current scan and retained grid timestamps; persistence origin is unobserved.",
        "evidence": [ev("v11-e-scan", "The 62.0 s scan showed the opening clear."), ev("v11-e-grid", "At 62.2 s the planning grid retained an obstacle observation stamped 49.5 s."), ev("v11-e-limit", "No retained event identifies why the older observation persisted.")],
        "units": [unit("u-observations", "The current scan and planning grid disagreed at 62.0--62.2 s."), unit("u-mechanism", "The bounded mechanism is a stale or inconsistent planning representation."), unit("u-limit", "The software origin of persistence is unresolved.")],
        "good": "At 62.0 s the scan showed the opening clear, while at 62.2 s the planning grid still contained the 49.5 s obstacle. This establishes a stale or inconsistent planning representation; why the older observation persisted is unresolved.",
        "good_exp": exp(abstention=True, units={"u-observations":"covered","u-mechanism":"covered","u-limit":"covered"}),
        "bad": "A planner cache bug caused the old obstacle to persist and caused the failure.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-observations":"omitted","u-mechanism":"incorrect","u-limit":"incorrect"}),
    },
    {
        "family": "local_swept_restriction", "endpoint": True, "mechanism_unit": "u-mechanism",
        "question": "What bounded physical restriction is supported by the scan?",
        "completeness": "Complete for the commanded segment; routes outside the local scan region are unobserved.",
        "evidence": [ev("v11-f-scan", "At 28.6 s, scan returns intersected the commanded segment's swept footprint."), ev("v11-f-scope", "The retained scan did not cover alternative routes outside the local segment.")],
        "units": [unit("u-mechanism", "The bounded mechanism is a local swept-footprint restriction on the commanded segment."), unit("u-limit", "Global route infeasibility is unresolved.")],
        "good": "At 28.6 s, scan returns intersected the commanded segment's swept footprint, establishing a local swept-footprint restriction. Because the scan did not cover alternative routes, global route infeasibility remains unresolved.",
        "good_exp": exp(abstention=True, units={"u-mechanism":"covered","u-limit":"covered"}),
        "bad": "The local intersection proves that no route existed anywhere.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-mechanism":"incorrect","u-limit":"incorrect"}),
    },
    {
        "family": "nominal_false_premise", "endpoint": False,
        "question": "Why did command-to-motion response fail in this run?",
        "completeness": "Complete for the declared diagnostic and terminal result.",
        "evidence": [ev("v11-g-diagnostic", "The command-to-motion diagnostic did not trigger in any eligible interval."), ev("v11-g-ratio", "Median eligible response ratio was 0.91."), ev("v11-g-result", "The navigation action succeeded at 44.0 s.")],
        "units": [unit("u-premise", "The premise of command-to-motion failure is false."), unit("u-evidence", "The diagnostic did not trigger, the median response ratio was 0.91, and the action succeeded.")],
        "good": "The premise is false: the command-to-motion diagnostic did not trigger, the median eligible response ratio was 0.91, and the action succeeded at 44.0 s.",
        "good_exp": exp(mechanism="not_applicable", units={"u-premise":"covered","u-evidence":"covered"}),
        "bad": "An unseen motor fault caused the response failure despite the successful result.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-premise":"incorrect","u-evidence":"omitted"}),
    },
    {
        "family": "missing_decisive_evidence", "endpoint": False,
        "question": "What physical or execution mechanism caused the abort?",
        "completeness": "Complete packet inventory; decisive geometry and command-to-motion evidence are absent.",
        "evidence": [ev("v11-h-result", "The action aborted at 58.3 s."), ev("v11-h-sequence", "A source-qualified Wait invocation preceded the abort."), ev("v11-h-missing", "No footprint-clearance comparison or command-to-motion diagnostic was retained.")],
        "units": [unit("u-limit", "The packet does not establish a physical or execution mechanism for the abort.")],
        "good": "The action aborted after a recorded Wait invocation, but no footprint-clearance comparison or command-to-motion diagnostic was retained. The packet therefore does not establish a physical or execution mechanism for the abort.",
        "good_exp": exp(answerability="answer_insufficient", mechanism="omitted", abstention=True, units={"u-limit":"covered"}),
        "bad": "A crate blocked the robot and caused the abort.",
        "bad_exp": exp(answerability="answer_insufficient", material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-limit":"incorrect"}),
    },
    {
        "family": "visible_not_consumed", "endpoint": False,
        "question": "What does the image establish about the later navigation response?",
        "completeness": "Complete for visual presence and timing; delivery, consumption, and decision dependence are absent.",
        "evidence": [ev("v11-i-image", "A barrier is visible in image img-317 at 31.0 s."), ev("v11-i-plan", "A changed plan was delivered at 31.7 s."), ev("v11-i-limit", "No record shows image delivery to Nav2, Nav2 consumption, or decision dependence on the barrier.")],
        "units": [unit("u-observation", "The barrier was visually present 0.7 s before the changed plan."), unit("u-limit", "Nav2 consumption and causal influence are unresolved.")],
        "good": "The barrier is visible in img-317 at 31.0 s, 0.7 s before the changed plan. The record does not show that Nav2 consumed the image or changed its plan because of the barrier.",
        "good_exp": exp(mechanism="not_applicable", abstention=True, units={"u-observation":"covered","u-limit":"covered"}),
        "bad": "Nav2 saw the barrier and therefore replanned around it.",
        "bad_exp": exp(material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-observation":"omitted","u-limit":"incorrect"}),
    },
    {
        "family": "ambiguous_measurements", "endpoint": False,
        "question": "Which motion-response mechanism is established during the turn?",
        "completeness": "Complete for the declared streams; their calibration disagreement is unresolved.",
        "evidence": [ev("v11-j-command", "Yaw-command median was 0.55 rad/s."), ev("v11-j-odom", "Odometry yaw-rate median was 0.09 rad/s."), ev("v11-j-imu", "IMU yaw-rate median was 0.50 rad/s."), ev("v11-j-limit", "The retained calibration does not resolve the odometry/IMU disagreement.")],
        "units": [unit("u-conflict", "Odometry and IMU provide conflicting motion-response evidence."), unit("u-limit", "A unique motion-response mechanism is unresolved.")],
        "good": "The 0.55 rad/s yaw command is paired with conflicting measurements: 0.09 rad/s from odometry and 0.50 rad/s from the IMU. Because the retained calibration does not resolve that disagreement, no unique motion-response mechanism is established.",
        "good_exp": exp(answerability="answer_insufficient", mechanism="omitted", abstention=True, units={"u-conflict":"covered","u-limit":"covered"}),
        "bad": "Odometry proves the vehicle failed to turn, and the IMU must be wrong.",
        "bad_exp": exp(answerability="answer_insufficient", material=True, disposition="nonanswer", mechanism="incorrect", abstention=False, causal=True, units={"u-conflict":"incorrect","u-limit":"incorrect"}),
    },
]


def build_cases() -> list[dict[str, Any]]:
    cases = []
    for index, scenario in enumerate(SCENARIOS, 1):
        core = [*ALWAYS_CORE, "mechanism_identification"] if scenario["endpoint"] else ALWAYS_CORE
        base = {
            "split":"heldout", "rubric":"diagnostic", "accuracy_eligible":True,
            "family":scenario["family"], "question":scenario["question"],
            "evidence_completeness":scenario["completeness"], "allowed_evidence":scenario["evidence"],
            "required_units":scenario["units"], "primary_endpoint_eligible":scenario["endpoint"],
            "mechanism_unit_id":scenario.get("mechanism_unit"), "scored_core_fields":core,
        }
        cases.append({**base, "case_id":f"Q11H{index:02d}S", "category_tags":["reference_factual",scenario["family"]], "candidate_answer":scenario["good"], "expected":scenario["good_exp"]})
        cases.append({**base, "case_id":f"Q11H{index:02d}E", "category_tags":["reference_unsupported",scenario["family"],"protected_causal","protected_boundary"], "protected_unit_ids":[unit["unit_id"] for unit in scenario["units"] if unit["unit_id"] in {"u-limit"}], "candidate_answer":scenario["bad"], "expected":scenario["bad_exp"]})

    pair = {
        "split":"heldout", "rubric":"diagnostic", "accuracy_eligible":False,
        "family":"presentation_invariance", "question":"What execution mechanism is established?",
        "evidence_completeness":"Complete for interval medians.",
        "allowed_evidence":[ev("v11-p-cmd","Command median was 0.29 m/s."),ev("v11-p-motion","Measured-speed median was 0.01 m/s; healthy median was 0.27 m/s.")],
        "required_units":[unit("u-mechanism","A command-to-motion discrepancy is established.")],
        "primary_endpoint_eligible":False, "mechanism_unit_id":None,
        "scored_core_fields":ALWAYS_CORE, "category_tags":["presentation_invariance"],
        "presentation_pair_id":"v11-discrepancy-paraphrase",
    }
    for number, answer in enumerate(("The medians establish a command-to-motion discrepancy.", "A discrepancy between commanded and measured motion is established by the medians."),1):
        cases.append({**pair,"case_id":f"Q11P01{number}","candidate_answer":answer,"expected":exp(units={"u-mechanism":"covered"})})
    return cases


def build_suite() -> dict[str, Any]:
    return {
        "schema":"crane-luna-judge-qualification-suite/v11",
        "suite_id":"luna-model-judge-v11-endpoint-aligned-fresh-heldout",
        "declared_utc":"2026-09-26T01:15:00Z",
        "status":"FRESH_UNEXECUTED_AT_DECLARATION",
        "thresholds":THRESHOLDS,
        "endpoint_definition":"On diagnosable cases, final answer covers the declared mechanism unit and has no material error.",
        "cases":build_cases(),
    }


def validate(suite: dict[str, Any]) -> None:
    cases=suite["cases"]
    if len(cases)!=22 or sum(case["accuracy_eligible"] for case in cases)!=20:
        raise ValueError("v11 requires 20 accuracy and two auxiliary cases")
    if len({case["case_id"] for case in cases})!=22:
        raise ValueError("v11 case IDs are not unique")
    if sum(case["primary_endpoint_eligible"] for case in cases)!=12:
        raise ValueError("v11 requires 12 diagnosable endpoint cases")
    for case in cases:
        units={item["unit_id"] for item in case["required_units"]}
        if set(case["expected"]["required_unit_statuses"])!=units:
            raise ValueError(f"{case['case_id']} has an incomplete unit reference")
        if case["primary_endpoint_eligible"] and case["mechanism_unit_id"] not in units:
            raise ValueError(f"{case['case_id']} lacks its endpoint mechanism unit")
        statuses=case["expected"]["required_unit_statuses"].values()
        derived="full" if all(x=="covered" for x in statuses) else "partial" if any(x=="covered" for x in statuses) else "nonanswer"
        if case["expected"]["disposition"]!=derived:
            raise ValueError(f"{case['case_id']} disposition differs from unit statuses")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    suite=build_suite(); validate(suite)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(suite,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"BUILT","cases":len(suite["cases"])}))


if __name__=="__main__":
    main()
