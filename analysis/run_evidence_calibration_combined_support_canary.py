#!/usr/bin/env python3
"""Execute only three frozen synthetic compatibility calls; never opens pilot calls."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

from adjudicate_evidence_calibration_annotations import compare
from audit_b2_transport_readiness import audit as transport_audit
from build_evidence_calibration_combined_support_canary import build
from build_evidence_calibration_pilot_support_packets import bound_disposition
from evidence_calibration_io import canonical_sha256
from evidence_calibration_support_execution import (
    VALID, annotation_payload, adjudication_payload, validate_support, validate_adjudication, call_once,
)
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once

ROOT = Path(__file__).resolve().parents[1]
FREEZE = "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-combined-support-canary-v1-freeze.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_bound(root: Path = ROOT) -> tuple[dict, dict, str, dict, dict]:
    freeze = json.loads((root / FREEZE).read_text())
    expected = {"schema": "crane-combined-support-canary-freeze/v1", "status": "FROZEN_BEFORE_CANARY_CALLS",
                "scope": "SYNTHETIC_COMBINED_FORMAT_COMPATIBILITY_ONLY", "planned_calls": 3,
                "call_order": ["A", "B", "C_CONSTRUCTED"], "timeout_s": 300, "tools": "none",
                "quality_driven_retries": 0, "further_candidate_cycles_authorized": False,
                "pilot_annotation_authorized": False, "endpoint_scoring_authorized": False,
                "highest_level_qualified": False, "raw_rank_endpoint_use_prohibited": True,
                "p11_authorized": False, "confirmation_independent_n": 0, "replication_independent_n": 0,
                "cli_version": "codex-cli 0.159.2",
                "candidate": {"model": "gpt-6-astra", "reasoning_effort": "high", "transport": "codex-cli-chatgpt-login-ephemeral/v1"}}
    if any(freeze.get(key) != value for key, value in expected.items()):
        raise ValueError("combined canary declaration scope changed")
    required_bindings = {"suite", "reference_review", "review_document", "suite_builder", "runner", "auditor",
                         "execution_helper", "packet_builder", "agent_packet_builder", "atomic_packet_builder",
                         "level_definitions", "structural_validator", "io_helpers", "intent_helpers",
                         "transport_auditor", "qualified_disposition", "prompt", "annotation_schema", "adjudication_schema",
                         "canary_tests", "execution_tests"}
    if set(freeze["bindings"]) != required_bindings:
        raise ValueError("combined canary component inventory changed")
    for item in freeze["bindings"].values():
        if digest(root / item["path"]) != item["raw_sha256"]:
            raise ValueError(f"changed combined canary component: {item['path']}")
    disposition = bound_disposition(root)
    qualified = disposition["qualified_binding"]
    if freeze["candidate"] != {key: qualified[key] for key in ("model", "reasoning_effort", "transport")}:
        raise ValueError("combined canary changed qualified model configuration")
    for name in ("prompt", "annotation_schema", "adjudication_schema"):
        if freeze["bindings"][name] != {"path": qualified[name]["path"], "raw_sha256": qualified[name]["sha256"]}:
            raise ValueError("combined canary changed qualified prompt or schema")
    suite = json.loads((root / freeze["bindings"]["suite"]["path"]).read_text())
    if suite != build():
        raise ValueError("synthetic canary references differ from construction")
    review = json.loads((root / freeze["bindings"]["reference_review"]["path"]).read_text())
    if (review.get("status") != "ACCEPTED_PROJECT_CONSTRUCTION_REVIEW"
            or review.get("suite") != freeze["bindings"]["suite"]
            or review.get("independent_reference_critique_claimed") is not False
            or review.get("human_validation_claimed") is not False
            or review.get("reference_changes_after_model_calls_allowed") is not False):
        raise ValueError("combined canary reference review changed")
    prompt = (root / freeze["bindings"]["prompt"]["path"]).read_text()
    schemas = [json.loads((root / freeze["bindings"][name]["path"]).read_text())
               for name in ("annotation_schema", "adjudication_schema")]
    return freeze, suite, prompt, *schemas


def requests(suite: dict, annotation_schema: dict, adjudication_schema: dict) -> list[dict]:
    packet, agents = suite["packet"], suite["agents"]
    tasks = []
    for slot in ("A", "B"):
        tasks.append({"slot": slot, "payload": annotation_payload(packet, slot, agents[slot]), "schema": annotation_schema,
                      "validate": lambda value, slot=slot: validate_support(packet, value, agents[slot], slot)})
    report = suite["constructed_disagreement_report"]
    tasks.append({"slot": "C_CONSTRUCTED", "payload": adjudication_payload(packet, report, agents["C"]),
                  "schema": adjudication_schema, "validate": lambda value: validate_adjudication(report, value, agents["C"])})
    return tasks


def support_checks(suite: dict, records: dict) -> dict:
    checks = {}
    for slot in ("A", "B"):
        observed, reference = records[slot]["parsed_final"], suite["support_references"][slot]
        checks[slot] = {
            "atomic_labels": {item["item_id"]: item["label"] for item in observed["atomic_labels"]}
                == {item["item_id"]: item["label"] for item in reference["atomic_labels"]},
            "required_unit_coverage": {item["unit_prompt"]: item["communicated"] for item in observed["required_unit_coverage"]}
                == {item["unit_prompt"]: item["communicated"] for item in reference["required_unit_coverage"]},
            "limitation_preservation": {item["limitation_prompt"]: item["preserved"] for item in observed["limitation_preservation"]}
                == {item["limitation_prompt"]: item["preserved"] for item in reference["limitation_preservation"]},
            "false_premise_handling": observed["false_premise_handling"] == reference["false_premise_handling"],
        }
    return checks


def result_for(freeze: dict, suite: dict, records: dict, freeze_hash: str) -> dict:
    result = {"schema": "crane-combined-support-canary-result/v1", "freeze_raw_sha256": freeze_hash,
              "suite_sha256": canonical_sha256(suite), "scientific_sample": False,
              "pilot_annotation_authorized": False, "endpoint_scoring_authorized": False, "p11_authorized": False,
              "highest_level_qualified": False, "confirmation_independent_n": 0, "replication_independent_n": 0,
              "constructed_c_not_observed_ab_disagreement": True, "completed_slots": list(records)}
    if any(record["status"] != VALID for record in records.values()):
        return {**result, "status": "FAILED_TECHNICAL_RETAIN_NO_RETRY"}
    if not {"A", "B"}.issubset(records):
        return {**result, "status": "INCOMPLETE_NO_ACCURACY_SCORE"}
    checks = support_checks(suite, records)
    result["support_checks"] = checks
    if not all(all(check.values()) for check in checks.values()):
        return {**result, "status": "FAILED_SYNTHETIC_REFERENCE_RETAIN_NO_RETRY"}
    if "C_CONSTRUCTED" not in records:
        return {**result, "status": "SUPPORT_PASS_C_NOT_RUN"}
    reference = suite["adjudication_reference"]
    observed = records["C_CONSTRUCTED"]["parsed_final"]
    result["constructed_adjudication_matches_reference"] = {
        item["disagreement_id"]: item["selected_value"] for item in observed["decisions"]} == {
        item["disagreement_id"]: item["selected_value"] for item in reference["decisions"]}
    report = compare(suite["packet"], records["A"]["parsed_final"], records["B"]["parsed_final"])
    result["actual_ab_disagreement_count_including_unqualified_raw_level"] = report["disagreement_count"]
    result["status"] = ("PASS_COMBINED_SYNTHETIC_CANARY_PENDING_ARTIFACT_PUSH"
                        if result["constructed_adjudication_matches_reference"] else "FAILED_CONSTRUCTED_C_RETAIN_NO_RETRY")
    return result


def run(root: Path = ROOT) -> dict:
    freeze, suite, prompt, annotation_schema, adjudication_schema = load_bound(root)
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"transport not ready: {preflight['status']}")
    cli = subprocess.run(["codex", "--version"], text=True, capture_output=True, check=True).stdout.strip()
    if cli != freeze["cli_version"]:
        raise RuntimeError("CLI version differs from combined canary declaration")
    output_root = root / freeze["output_root"]
    freeze_hash = digest(root / FREEZE)
    records = {}
    for task in requests(suite, annotation_schema, adjudication_schema):
        slot = task["slot"]
        if slot == "C_CONSTRUCTED" and result_for(freeze, suite, records, freeze_hash)["status"] != "SUPPORT_PASS_C_NOT_RUN":
            break
        records[slot] = call_once(output=output_root / f"{slot}.json", payload=task["payload"], schema=task["schema"],
                                  prompt=prompt, freeze=freeze, freeze_sha256=freeze_hash, cli_version=cli,
                                  validate=task["validate"])
        print(json.dumps({"slot": slot, "status": records[slot]["status"]}), flush=True)
        if records[slot]["status"] != VALID:
            break
    result = result_for(freeze, suite, records, freeze_hash)
    output = output_root / "canary-result.json"
    if output.exists():
        if json.loads(output.read_text()) != result:
            raise RuntimeError("retained combined canary result changed")
    else:
        _write_once(output, result)
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("PASS_") else 1)
