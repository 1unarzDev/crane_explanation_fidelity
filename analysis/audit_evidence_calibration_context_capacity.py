#!/usr/bin/env python3
"""Replay sanitized capacity observations without resolving a provider or launching a call."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBSERVATION = ROOT / "manifests/operations/evidence-calibration-context-capacity-observation-v1.json"


def audit(path: Path = OBSERVATION) -> dict:
    record = json.loads(path.read_text())
    if (record.get("schema") != "crane-context-capacity-observation/v1-development"
            or record.get("scope") != "NON_STUDY_INFRASTRUCTURE_OBSERVATION"
            or record.get("candidate_model") != "gpt-6-sol"
            or record.get("candidate_reasoning_effort") != "high"
            or any(record.get(key) is not False for key in
                   ("complete_request_token_counts_available", "harness_schema_tool_overhead_bound",
                    "output_reasoning_reserve_bound", "provider_route_capacity_verified",
                    "context_or_provider_settings_changed", "study_request_attempted", "model_call_attempted"))):
        raise ValueError("unresolved capacity observation cannot activate model execution")
    config = record["config_observation"]
    if (set(config) != {"provider", "context_window_override_present", "auto_compact_override_present",
                        "catalog_override_present", "secrets_recorded"}
            or config["provider"] != "codex-lb"
            or any(config[key] is not False for key in config if key != "provider")):
        raise ValueError("capacity observation configuration scope changed")
    model = record["codex_catalog"]["selected_model"]
    if set(model) != {"slug", "context_window", "max_context_window", "effective_context_window_percent",
                      "supports_experimental_context", "truncation_policy"} or model["slug"] != record["candidate_model"]:
        raise ValueError("capacity model metadata must remain sanitized and model-specific")
    window, maximum, percent = (model[key] for key in ("context_window", "max_context_window", "effective_context_window_percent"))
    if (any(type(value) is not int for value in (window, maximum, percent))
            or not 0 < window <= maximum or not 0 < percent <= 100):
        raise ValueError("capacity metadata contains invalid limits")
    attempts = record["exact_tokenizer_resolution"]
    if (not attempts or any(attempt.get("model") != record["candidate_model"]
                           or attempt.get("status") != "UNMAPPED_EXACT_MODEL"
                           or attempt.get("alternate_encoding_selected") is not False for attempt in attempts)):
        raise ValueError("unmapped tokenizer cannot silently acquire an alternate encoding")
    binding = record["baseline_request_audit"]
    expected_path = "manifests/study/evidence-calibration-baseline-requests-v1-development.json"
    if (binding["path"] != expected_path
            or hashlib.sha256((ROOT / expected_path).read_bytes()).hexdigest() != binding["raw_sha256"]):
        raise ValueError("capacity observation baseline-request binding changed")
    requests = json.loads((ROOT / expected_path).read_text())
    published_window = record["official_documentation"][0]["context_window_tokens"]
    return {"schema": "crane-context-capacity-audit/v1-development",
            "status": "CAPACITY_UNRESOLVED_EXECUTION_CLOSED", "model": record["candidate_model"],
            "cli_catalog_context_window": window, "cli_catalog_max_context_window": maximum,
            "cli_catalog_effective_default_tokens": window * percent // 100,
            "published_api_context_window": published_window,
            "published_and_cli_catalog_limits_differ": published_window != window,
            "baseline_request_count": requests["baseline_request_count"],
            "prompt_utf8_byte_ranges": requests["prompt_utf8_byte_ranges"],
            "token_fit": None, "tokenizer_binding_verified": False,
            "remaining_capacity_requirements": ["exact model/provider/tokenizer binding",
                "complete model-visible prompt/schema/harness/tool token accounting",
                "prospective output and reasoning reserve", "verified capacity for the actual route"],
            "model_calls_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
