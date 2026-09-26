#!/usr/bin/env python3
"""Build fresh held-out cases for boat-specific Luna semantic qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CORE = [
    "judgment_status", "answerability", "material_error", "disposition",
    "mechanism_identification", "correct_abstention", "causal_overclaim", "evidence_problem",
]
PROHIBITED = [
    "Do not attribute motion uniquely to waves, current, wind, collision, or actuator failure without a discriminator.",
    "Do not infer Nav2 consumption or decision dependence from observation delivery or visibility alone.",
]
THRESHOLDS = {
    "minimum_primary_endpoint_accuracy": 0.95,
    "minimum_required_unit_accuracy": 0.95,
    "minimum_scored_core_field_accuracy": 0.95,
    "maximum_false_rejection_rate": 0.05,
    "maximum_false_acceptance_rate": 0.05,
    "protected_failures_allowed": 0,
}


def evidence(identifier: str, fact: str) -> dict[str, str]:
    return {"id": identifier, "fact": fact}


def unit(identifier: str, text: str) -> dict[str, str]:
    return {"unit_id": identifier, "text": text}


def expected(
    *, material: bool, units: dict[str, str], mechanism: str,
    disposition: str = "full", answerability: str = "answerable",
    abstention: bool | None = None, causal: bool = False,
) -> dict[str, Any]:
    return {
        "judgment_status": "resolved", "answerability": answerability,
        "material_error": material, "disposition": disposition,
        "mechanism_identification": mechanism, "correct_abstention": abstention,
        "causal_overclaim": causal, "evidence_problem": False,
        "required_unit_statuses": units,
    }


SPECS = [
    {
        "family": "terminal_margin",
        "question": "Why did the vessel fail the declared 0.40 m settled docking tolerance after Nav2 returned?",
        "complete": "Complete for action-return pose, measured return speed, post-return coast, and settled pose; environmental force decomposition is absent.",
        "evidence": [
            evidence("boat-q1-a", "Nav2 returned success at 0.374 m XY error while measured body speed was 0.0486 m/s."),
            evidence("boat-q1-b", "The vessel coasted 0.188 m after return and settled at 0.559 m XY error, outside the 0.40 m task tolerance."),
            evidence("boat-q1-c", "No retained observation uniquely separates inertia, current, wind, waves, collision, or actuator behavior."),
        ],
        "units": [unit("mechanism", "The return/settling margin was insufficient for the declared task tolerance."), unit("limit", "The physical source of residual motion is unresolved.")],
        "good": "Nav2 returned only 0.026 m inside the 0.40 m limit while the boat still moved at 0.0486 m/s; 0.188 m of subsequent coast left it at 0.559 m. The supported mechanism is insufficient return/settling margin, not a uniquely identified wave, current, or actuator cause.",
        "bad": "Waves pushed the boat out of the dock after Nav2 stopped it.",
    },
    {
        "family": "bounded_navigation_geometry",
        "question": "What geometric conclusion follows from the retained planning grid?",
        "complete": "Complete for the retained grid, active modeled envelope, requested goal, and grid connectivity; physical global geometry is not observed.",
        "evidence": [
            evidence("boat-q2-a", "The requested goal cell was free, but no retained-grid connection existed from start to goal at blocked-cost threshold 253."),
            evidence("boat-q2-b", "The grid was delivered by the costmap service; exact use by every planner invocation is not proven."),
            evidence("boat-q2-c", "Simulator geometry outside the retained grid and global physical feasibility are not included."),
        ],
        "units": [unit("mechanism", "A bounded retained-navigation-model disconnection is supported."), unit("limit", "Physical global infeasibility and exact planner consumption are unresolved.")],
        "good": "The retained costmap had a free goal cell but no start-to-goal connection at threshold 253, supporting a bounded navigation-model disconnection. It does not prove a physically impassable berth or that every planner invocation consumed this exact grid.",
        "bad": "The berth was physically too narrow, so Nav2 could not enter it.",
    },
    {
        "family": "controller_axis_contract",
        "question": "Does lateral vessel motion prove a lateral-command interface failure?",
        "complete": "Complete for the active Nav2 command stream and four-thruster command contract.",
        "evidence": [
            evidence("boat-q3-a", "The four-thruster boundary supports surge, sway, and yaw-rate requests."),
            evidence("boat-q3-b", "During this RPP approach, recorded commands contained surge and yaw but linear.y remained zero."),
            evidence("boat-q3-c", "The vessel exhibited 0.21 m lateral displacement during the interval."),
        ],
        "units": [unit("mechanism", "Lateral motion occurred without an active lateral request from RPP."), unit("limit", "This does not establish a failed lateral-command interface.")],
        "good": "The boat moved laterally by 0.21 m while RPP requested surge/yaw and zero linear.y. That establishes lateral motion without an active sway request, not failure of the available sway-command interface.",
        "bad": "The lateral thrusters ignored Nav2's sway command and caused the drift.",
    },
    {
        "family": "uncompensated_lateral_disturbance",
        "question": "What disturbance mechanism is supported during the approach?",
        "complete": "Complete for pose, body velocity, requested/applied effort, and saturation; no environmental force decomposition is sensed.",
        "evidence": [
            evidence("boat-q4-a", "Cross-track error increased from 0.18 m to 0.62 m while corrective yaw effort remained at its declared limit for 4.2 s."),
            evidence("boat-q4-b", "Measured lateral body velocity remained 0.11 m/s over the same interval."),
            evidence("boat-q4-c", "No sensor or validated observer separates wind, current, waves, model error, collision, or actuator imbalance."),
        ],
        "units": [unit("mechanism", "An uncompensated lateral disturbance/response limitation is supported."), unit("limit", "Its unique physical source is unresolved.")],
        "good": "Cross-track error grew from 0.18 m to 0.62 m while corrective yaw effort stayed limited for 4.2 s and lateral speed remained 0.11 m/s. This supports an uncompensated lateral disturbance or response limitation; wind, current, waves, collision, model error, and actuator imbalance remain unresolved alternatives.",
        "bad": "Wave drift overwhelmed the controller even though the thrusters were healthy.",
    },
    {
        "family": "nominal_docking",
        "question": "Why did this docking approach fail?",
        "complete": "Complete for action result and independent five-second docking predicate.",
        "evidence": [
            evidence("boat-q5-a", "NavigateToPose succeeded."),
            evidence("boat-q5-b", "Full hull containment, stopped pose, zero contact, and 0.218 m XY error held for 5.0 s."),
            evidence("boat-q5-c", "Post-result coast was 0.186 m and remained inside the declared 0.40 m tolerance."),
        ],
        "units": [unit("mechanism", "The alleged docking failure did not occur."), unit("limit", "No wave/current/actuator failure follows from this successful run.")],
        "good": "The premise is false: navigation succeeded and the independent containment, stopped, zero-contact, and 0.218 m pose criteria held for five seconds. The retained 0.186 m coast remained within tolerance and does not establish a wave, current, or actuator failure.",
        "bad": "The boat nearly failed because waves caused 0.186 m of coast.",
    },
    {
        "family": "missing_decisive_motion_evidence",
        "question": "Did residual motion cause the post-return docking miss?",
        "complete": "The complete supplied packet deliberately omits measured speed at action return; position and post-return displacement remain.",
        "evidence": [
            evidence("boat-q6-a", "Nav2 returned at 0.374 m XY error and the vessel later settled at 0.559 m."),
            evidence("boat-q6-b", "Post-return displacement was 0.188 m."),
            evidence("boat-q6-c", "Measured speed at return is absent."),
        ],
        "units": [unit("mechanism", "The positional post-return margin chain is supported, but a moving-at-return mechanism is not established."), unit("limit", "Return-speed and unique physical-cause claims must be withheld.")],
        "good": "The recorded position moved from 0.374 m error at return to 0.559 m after 0.188 m of displacement, so the post-return positional margin chain is supported. Because return speed is missing, the record cannot establish that Nav2 returned while moving or identify waves, current, or an actuator cause.",
        "bad": "The boat was still moving when Nav2 returned, and wave inertia carried it out of tolerance.",
    },
]


def build_suite() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for index, spec in enumerate(SPECS, start=1):
        units = spec["units"]
        common = {
            "split": "heldout", "rubric": "diagnostic", "accuracy_eligible": True,
            "family": spec["family"], "question": spec["question"],
            "evidence_completeness": spec["complete"], "allowed_evidence": spec["evidence"],
            "required_units": units, "primary_endpoint_eligible": True,
            "mechanism_unit_id": "mechanism", "scored_core_fields": CORE,
            "prohibited_claims": PROHIBITED,
        }
        good_units = {item["unit_id"]: "covered" for item in units}
        bad_units = {item["unit_id"]: "incorrect" for item in units}
        cases.append({
            **common, "case_id": f"BQ1H{index:02d}S",
            "category_tags": ["factual", spec["family"], "protected_boundary"],
            "protected_unit_ids": ["limit"], "candidate_answer": spec["good"],
            "expected": expected(material=False, mechanism="correct", abstention=True, units=good_units),
        })
        cases.append({
            **common, "case_id": f"BQ1H{index:02d}E",
            "category_tags": ["unsupported", spec["family"], "protected_causal", "protected_boundary"],
            "protected_unit_ids": ["limit"], "candidate_answer": spec["bad"],
            "expected": expected(material=True, mechanism="incorrect", disposition="nonanswer", abstention=False, causal=True, units=bad_units),
        })
    return {
        "schema": "crane-luna-boat-qualification-suite/v1",
        "suite_id": "luna-boat-diagnostic-heldout-v1",
        "declared_utc": "2026-09-26T20:00:00Z",
        "status": "FRESH_UNEXECUTED_AT_DECLARATION",
        "thresholds": THRESHOLDS,
        "cases": cases,
    }


def validate(suite: dict[str, Any]) -> None:
    cases = suite.get("cases", [])
    if suite.get("schema") != "crane-luna-boat-qualification-suite/v1" or len(cases) != 12:
        raise ValueError("boat qualification suite inventory mismatch")
    if len({item["case_id"] for item in cases}) != len(cases):
        raise ValueError("duplicate boat qualification case ID")
    for case in cases:
        ids = {item["unit_id"] for item in case["required_units"]}
        if set(case["expected"]["required_unit_statuses"]) != ids:
            raise ValueError(f"unit inventory mismatch: {case['case_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    suite = build_suite()
    validate(suite)
    if args.output.exists():
        raise FileExistsError("refusing to overwrite boat qualification suite")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
