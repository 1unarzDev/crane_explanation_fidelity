#!/usr/bin/env python3
"""Run one isolated, cached, no-retry B2 development-pilot condition."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "packages/astro_dock/src/crane_explain/src"))

from build_nested_evidence_conditions import build_conditions  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from normalize_command_motion_evidence import normalize  # noqa: E402
from run_llm_episode_pilot import ANSWER_SCHEMA  # noqa: E402


class BoundedCodexCliCaller:
    """Study-local Codex adapter with durable timeout/failure retention."""

    def __init__(self, cache: Path, model: str, reasoning_effort: str, timeout_s: float = 300.0):
        self.cache, self.model, self.reasoning_effort = cache, model, reasoning_effort
        self.timeout_s = timeout_s
        self.cache.mkdir(parents=True, exist_ok=True)
        self.cli_version = subprocess.run(["codex", "--version"], check=True,
                                          capture_output=True, text=True).stdout.strip()

    def call(self, role: str, prompt: str, schema: dict[str, Any], *,
             working_directory: Path, workspace_identity: dict[str, Any]) -> dict[str, Any]:
        request = {
            "adapter": "codex-cli-json-bounded/v1", "provider": "codex-lb-direct",
            "model": self.model, "reasoning_effort": self.reasoning_effort,
            "temperature": None, "seed": None, "role": role, "prompt": prompt,
            "schema": schema, "cli_version": self.cli_version,
            "workspace_identity": workspace_identity, "timeout_s": self.timeout_s,
        }
        cache_key = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        cache_path = self.cache / f"{cache_key}.json"
        if cache_path.exists():
            record = json.loads(cache_path.read_text())
            if record["request"] != request:
                raise RuntimeError(f"cache collision at {cache_path}")
            if record["return_code"] != 0 or record["parsed_final"] is None:
                raise RuntimeError(f"retained model failure at {cache_path}")
            return record
        with tempfile.TemporaryDirectory(prefix="crane-ec-b2-call-") as temporary:
            temporary_path = Path(temporary)
            schema_path, output_path = temporary_path / "schema.json", temporary_path / "answer.json"
            schema_path.write_text(json.dumps(schema))
            command = [
                "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--cd", str(working_directory), "--model", self.model,
                "--config", f'model_reasoning_effort="{self.reasoning_effort}"',
                "--output-schema", str(schema_path), "--output-last-message", str(output_path), "-",
            ]
            started_ns = time.time_ns()
            timed_out = False
            try:
                completed = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                           check=False, env={**os.environ, "NO_COLOR": "1"},
                                           timeout=self.timeout_s)
                return_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
            except subprocess.TimeoutExpired as error:
                timed_out = True
                return_code = 124
                stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
                stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
            latency_ms = (time.time_ns() - started_ns) / 1_000_000
            events = []
            for line in stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    events.append({"type": "unparsed_stdout", "text": line})
            raw_final = output_path.read_text() if output_path.exists() else ""
            try:
                parsed_final = json.loads(raw_final)
            except json.JSONDecodeError as error:
                parsed_final, parse_error = None, str(error)
            else:
                parse_error = None
            record = {
                "schema": "crane-explain-model-call/v1", "cache_key": cache_key,
                "request": request, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "started_wall_time_ns": started_ns, "latency_ms": latency_ms, "cost_usd": None,
                "cost_status": "not_reported_by_codex_cli", "return_code": return_code,
                "timed_out": timed_out, "events": events, "stderr": stderr,
                "raw_final": raw_final, "parsed_final": parsed_final, "parse_error": parse_error,
            }
            cache_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        if return_code != 0 or parsed_final is None:
            raise RuntimeError(f"model call failed; retained at {cache_path}")
        return record


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage_writable_codex_home(target: Path) -> None:
    source = Path.home() / ".codex"
    target.mkdir(exist_ok=True)
    config = tomllib.loads((source / "config.toml").read_text())
    provider = config["model_providers"]["codex-lb"]
    staged = "\n".join((
        'model_provider = "pilot-provider"',
        '[model_providers.pilot-provider]',
        'name = "openai"',
        f'base_url = "{provider["base_url"]}"',
        'env_key = "CODEX_LB_API_KEY"',
        'wire_api = "responses"',
        'supports_websockets = true',
        'requires_openai_auth = false',
        '[features]',
        'apps = false',
        'browser_use = false',
        'computer_use = false',
        'image_generation = false',
        'plugins = false',
        'code_mode_host = false',
        '',
    ))
    (target / "config.toml").write_text(staged)


def _materialize(root: Path, pilot: dict[str, Any], schedule: dict[str, Any],
                 condition_id: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    run_id, level_text = condition_id.rsplit("-E", 1)
    level = int(level_text)
    if run_id not in pilot["selection"]["episode_ids"]:
        raise ValueError("condition is outside the fixed pilot")
    runs = {item["run_id"]: item for item in schedule["cohorts"][0]["runs"]}
    run = runs[run_id]
    family_map = {
        "persistent-discrepancy": "persistent_command_motion_discrepancy",
        "transient-compensation": "measured_response_recovery",
        "ambiguous-missing-odometry": "missing_decisive_evidence",
        "nominal-false-premise": "nominal_false_premise",
    }
    family = family_map[run["family"]]
    diagnostic_path = root / f"data/robot_visible/dev/{run_id}/command-motion-diagnostic-v3.json"
    diagnostic = json.loads(diagnostic_path.read_text())
    question = "The episode succeeded; was there nevertheless a navigation failure, and what does the evidence support?" \
        if family == "nominal_false_premise" else \
        "What is the strongest navigation diagnosis supported by the available robot-visible evidence?"
    source = normalize(diagnostic, configuration_id=run["cluster_id"], question=question,
                       omit_odometry=family == "missing_decisive_evidence")
    if family == "nominal_false_premise":
        removals = [["/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], []]
    elif family == "missing_decisive_evidence":
        removals = [["/evidence/behavior_tree_transitions", "/evidence/source_anchors", "/evidence/delivered_command_stream"], ["/evidence/delivered_command_stream"], []]
    else:
        removals = [["/evidence/behavior_tree_transitions", "/evidence/source_anchors", "/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], ["/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], []]
    if level >= len(removals):
        raise ValueError("condition level is outside the family ladder")
    spec = {
        "schema": "crane-nested-evidence-mask-spec/v1", "ladder_id": f"{family}-ladder-v1-development",
        "condition_builder_id": "nested-evidence-condition-builder", "condition_builder_version": "v1",
        "condition_builder_sha256": sha256(root / "analysis/build_nested_evidence_conditions.py"),
        "source_configuration_sha256": diagnostic["source"]["nav2_config_sha256"],
        "runtime_manifest_sha256": diagnostic["source"]["runtime_manifest_sha256"],
        "conditions": [
            {"condition_id": f"{run_id}-E{index}", "level_index": index,
             "removed_json_pointers": pointers,
             "mask_id": None if not pointers else f"{family}-E{index}",
             "mask_version": None if not pointers else "v1-development"}
            for index, pointers in enumerate(removals)
        ],
    }
    return build_conditions(source, spec)[level], diagnostic, family


def run(args: argparse.Namespace, caller: Any | None = None) -> dict[str, Any]:
    pilot = json.loads(args.pilot.read_text())
    schedule = json.loads(args.schedule.read_text())
    validation = json.loads(args.validation.read_text())
    entry, diagnostic, family = _materialize(ROOT, pilot, schedule, args.condition_id)
    expected_episode = next(item for item in validation["episodes"] if item["run_id"] == args.condition_id.rsplit("-E", 1)[0])
    index = expected_episode["condition_ids"].index(args.condition_id)
    expected_hash = expected_episode["condition_packet_sha256s"][index]
    if entry["condition"]["method_packet_sha256"] != expected_hash:
        raise ValueError("materialized packet differs from the validated pilot input")
    output = args.output_root / f"{args.condition_id}.json"
    if output.exists():
        retained = json.loads(output.read_text())
        if retained["method_packet_sha256"] != expected_hash:
            raise ValueError("existing output is bound to a different packet")
        return retained

    caller = caller or BoundedCodexCliCaller(
        args.cache, pilot["methods"]["B2"]["model"],
        pilot["methods"]["B2"]["reasoning_effort"], args.timeout_seconds,
    )
    with tempfile.TemporaryDirectory(prefix=f"crane-ec-b2-{args.condition_id}-") as temporary, \
            tempfile.TemporaryDirectory(prefix="crane-ec-codex-home-") as codex_temporary:
        workspace = Path(temporary)
        codex_home = Path(codex_temporary)
        _stage_writable_codex_home(codex_home)
        evidence_dir, source_dir, tools_dir = workspace / "robot_visible", workspace / "source", workspace / "tools"
        evidence_dir.mkdir(); source_dir.mkdir(); tools_dir.mkdir()
        evidence_path = evidence_dir / "evidence.json"
        evidence_path.write_text(json.dumps(entry["method_packet"], indent=2, sort_keys=True) + "\n")
        assets = [
            (ROOT / "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml", source_dir / "behavior_tree.xml", diagnostic["source"]["bt_policy_sha256"]),
            (ROOT / "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml", source_dir / "nav2.yaml", diagnostic["source"]["nav2_config_sha256"]),
            (ROOT / "configs/diagnostic_command_motion_low_speed_v1.json", source_dir / "diagnostic_config.json", diagnostic["source"]["diagnostic_config_sha256"]),
        ]
        for source, target, expected in assets:
            if sha256(source) != expected:
                raise ValueError(f"source asset hash mismatch: {source}")
            shutil.copy2(source, target)
        tool_source = ROOT / "analysis/inspect_evidence_calibration_packet.py"
        shutil.copy2(tool_source, tools_dir / tool_source.name)
        prompt_template = (ROOT / pilot["methods"]["B2"]["prompt"]).read_text()
        prompt = prompt_template + "\n\nThe governed job files are:\n- robot_visible/evidence.json\n- source/behavior_tree.xml\n- source/nav2.yaml\n- source/diagnostic_config.json\n- tools/inspect_evidence_calibration_packet.py\n\nYou may inspect these files and run the primitive tool. Return the answer object required by the output schema."
        previous_codex_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(codex_home)
        try:
            record = caller.call(
                f"evidence-calibration-B2-{args.condition_id}", prompt, ANSWER_SCHEMA,
                working_directory=workspace,
                workspace_identity={"pilot_id": pilot["pilot_id"], "condition_id": args.condition_id,
                                    "method": "B2", "method_packet_sha256": expected_hash,
                                    "tool_sha256": sha256(tool_source)},
            )
        finally:
            if previous_codex_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_codex_home
    result = {
        "schema": "crane-evidence-calibration-b2-development-output/v1",
        "pilot_id": pilot["pilot_id"], "condition_id": args.condition_id, "family": family,
        "method": "B2", "method_packet_sha256": expected_hash,
        "model": pilot["methods"]["B2"]["model"],
        "reasoning_effort": pilot["methods"]["B2"]["reasoning_effort"],
        "single_call_no_retry": True, "cache_key": record["cache_key"],
        "answer": record["parsed_final"]["answer"], "raw_call_record_sha256": canonical_sha256(record),
        "development_only": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-id", required=True)
    parser.add_argument("--pilot", type=Path, default=ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json")
    parser.add_argument("--schedule", type=Path, default=ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json")
    parser.add_argument("--validation", type=Path, default=ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json")
    parser.add_argument("--cache", type=Path, default=ROOT / "research/explanation_fidelity/model_cache/evidence-calibration-b2-b4-pilot-v1")
    parser.add_argument("--output-root", type=Path, default=ROOT / "model_outputs/evidence-calibration-b2-b4-pilot-v1/b2")
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
