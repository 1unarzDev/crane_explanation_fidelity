#!/usr/bin/env python3
"""Run the qualified Luna arm on preselected diagnostic development packets.

The model caller sees only blinded packet rows. Evaluator-only condition keys are loaded only after
all calls finish, by the coordinator, to produce a descriptive development report.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any

from luna_model_judge import LunaIsolatedCodexCaller, atomic_write_json, packet_envelope


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "manifests/annotation/diagnostic-development-pilot-v1.json"
SELECTION = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/development"
    / "diagnostic-pilot-primary-endpoints-v1.json"
)
QUALIFICATION = ROOT / "manifests/annotation/luna-model-judge-v1-heldout-v7-reference-audited.json"
MECHANISM_PACKETS = {
    "land-s-turn-unmasked",
    "warehouse-recovery-sequence",
    "command-motion-supported",
    "command-motion-compensation",
    "land-delivered-plan-change",
}
FALSE_PREMISE_PACKET = "land-prospective-nominal-false-premise"
CONDITIONS = ("R", "P", "T", "N")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def selected_specs() -> list[dict[str, Any]]:
    qualification = load(QUALIFICATION)
    if qualification.get("status") != "HELDOUT_QUALIFIED" or not qualification.get(
        "study_evaluation_allowed"
    ):
        raise ValueError("Luna v7 is not activated for prospective scoring")
    selection = load(SELECTION)
    inventory = load(INVENTORY)
    selected_names = {item["packet_name"] for item in selection["selected"]}
    expected = MECHANISM_PACKETS | {FALSE_PREMISE_PACKET}
    if selected_names != expected:
        raise ValueError("development primary selection differs from frozen six-packet inventory")
    by_name = {item["name"]: item for item in inventory["packets"]}
    if not selected_names <= set(by_name):
        raise ValueError("selected development packet is absent from annotation inventory")
    specs = [by_name[name] for name in sorted(selected_names)]
    for spec in specs:
        packet = ROOT / spec["packet"]
        key = ROOT / spec["key"]
        if digest(packet) != spec["packet_sha256"] or digest(key) != spec["key_sha256"]:
            raise ValueError(f"{spec['name']}: governed packet or key hash differs")
        if len(read_jsonl(packet)) != 4:
            raise ValueError(f"{spec['name']}: expected exactly four blinded responses")
    return specs


def success(judgment: dict[str, Any]) -> bool:
    return judgment["mechanism_identification"] == "correct" and judgment["material_error"] is False


def false_premise_success(judgment: dict[str, Any]) -> bool:
    return (
        judgment["mechanism_identification"] == "not_applicable"
        and judgment["material_error"] is False
        and judgment["disposition"] == "full"
    )


def summarize(joined: list[dict[str, Any]], call_failures: list[dict[str, str]]) -> dict[str, Any]:
    pass_reports: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        rows = [row for row in joined if row["pass_id"] == pass_id]
        mechanism = [row for row in rows if row["packet_name"] in MECHANISM_PACKETS]
        nominal = [row for row in rows if row["packet_name"] == FALSE_PREMISE_PACKET]
        condition_reports: dict[str, Any] = {}
        for condition in CONDITIONS:
            selected = [row for row in mechanism if row["condition"] == condition]
            nominal_selected = [row for row in nominal if row["condition"] == condition]
            condition_reports[condition] = {
                "mechanism_successes": sum(success(row["judgment"]) for row in selected),
                "mechanism_total": len(selected),
                "material_errors": sum(row["judgment"]["material_error"] is True for row in selected),
                "false_premise_successes": sum(
                    false_premise_success(row["judgment"]) for row in nominal_selected
                ),
                "false_premise_total": len(nominal_selected),
            }
        p = condition_reports["P"]
        r = condition_reports["R"]
        pass_reports[pass_id] = {
            "conditions": condition_reports,
            "p_minus_r_mechanism_success_difference": (
                p["mechanism_successes"] / p["mechanism_total"]
                - r["mechanism_successes"] / r["mechanism_total"]
            ),
            "inference": "DEVELOPMENT_ONLY_NO_CONFIDENCE_INTERVAL_OR_SIGNIFICANCE_TEST",
        }
    by_response: dict[str, dict[str, bool]] = defaultdict(dict)
    for row in joined:
        if row["packet_name"] in MECHANISM_PACKETS:
            by_response[row["response_id"]][row["pass_id"]] = success(row["judgment"])
    disagreements = [
        response_id
        for response_id, values in sorted(by_response.items())
        if len(values) == 2 and values["pass-1"] != values["pass-2"]
    ]
    return {
        "schema": "crane-luna-diagnostic-development-summary/v1",
        "status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
        "responses": len({row["response_id"] for row in joined}),
        "judge_measurements": len(joined),
        "statistical_clusters": 6,
        "mechanism_clusters": 5,
        "false_premise_clusters": 1,
        "passes": pass_reports,
        "primary_endpoint_disagreements": disagreements,
        "primary_endpoint_disagreement_count": len(disagreements),
        "call_failures": call_failures,
        "confirmatory_alpha_consumed": 0.0,
        "selection_rule": "Candidate selection may use this development evidence; these labels cannot enter confirmation or replication.",
    }


def run(output_root: Path) -> dict[str, Any]:
    specs = selected_specs()
    blinded: list[tuple[str, dict[str, Any]]] = []
    condition_by_response: dict[str, tuple[str, str]] = {}
    for spec in specs:
        packet_rows = read_jsonl(ROOT / spec["packet"])
        key = load(ROOT / spec["key"])
        key_entries = {item["response_id"]: item["condition"] for item in key["entries"]}
        if {row["response_id"] for row in packet_rows} != set(key_entries):
            raise ValueError(f"{spec['name']}: packet/key response inventory differs")
        blinded.extend((spec["name"], row) for row in packet_rows)
        condition_by_response.update(
            {response_id: (spec["name"], condition) for response_id, condition in key_entries.items()}
        )

    joined: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    cache_keys: dict[str, dict[str, str]] = {}
    for pass_id in ("pass-1", "pass-2"):
        caller = LunaIsolatedCodexCaller(
            cache=output_root / "calls" / "high" / pass_id, effort="high"
        )
        cache_keys[pass_id] = {}
        pass_judgments: list[dict[str, Any]] = []
        for packet_name, row in blinded:
            response_id = row["response_id"]
            try:
                record = caller.call(packet_envelope(row, "diagnostic", pass_id))
            except RuntimeError as error:
                failures.append(
                    {"pass_id": pass_id, "response_id": response_id, "error": str(error)}
                )
                continue
            cache_keys[pass_id][response_id] = record["cache_key"]
            pass_judgments.append(record["judgment"])
            joined.append(
                {
                    "pass_id": pass_id,
                    "response_id": response_id,
                    "packet_name": packet_name,
                    "condition": condition_by_response[response_id][1],
                    "judgment": record["judgment"],
                }
            )
        output_root.mkdir(parents=True, exist_ok=True)
        with (output_root / f"{pass_id}-judgments.jsonl").open("w", encoding="utf-8") as handle:
            for judgment in pass_judgments:
                handle.write(json.dumps(judgment, sort_keys=True) + "\n")
    report = summarize(joined, failures)
    report["cache_keys"] = cache_keys
    report["inputs"] = [
        {"name": spec["name"], "packet": spec["packet"], "sha256": spec["packet_sha256"]}
        for spec in specs
    ]
    atomic_write_json(output_root / "development-summary.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("validate", "run"), required=True)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    specs = selected_specs()
    if args.phase == "validate":
        print(json.dumps({"status": "VALID", "packets": len(specs), "responses": 24}))
        return 0
    if args.output_root is None:
        parser.error("--output-root is required for run")
    output_root = args.output_root.resolve()
    if (output_root / "development-summary.json").exists():
        raise SystemExit("refusing to overwrite a completed development summary")
    report = run(output_root)
    print(json.dumps({"status": report["status"], "call_failures": len(report["call_failures"])}))
    return 0 if not report["call_failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
