#!/usr/bin/env python3
"""Run one frozen coverage-complete-v4 development case against fair baseline R.

This is a narrow, separately versioned successor adapter.  It deliberately reuses the validated
measurement-complete-v2 transport while pinning the v4 geometric adapter and a distinct contract,
cache, question, result, and generation identity.  The frozen v2 runner remains byte-unchanged.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import tempfile
from typing import Any, Iterator

import run_measurement_complete_v2_development as base
from build_geometric_composition_packet_v4 import build as build_geometric_packet


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = "crane-coverage-complete-v4-development-screen/v1"
RUN_SCHEMA = "crane-coverage-complete-v4-development-case-result/v1"
RUNNER_PATH = Path(__file__).resolve()
BASE_RUNNER_PATH = ROOT / "analysis/run_measurement_complete_v2_development.py"
GEOMETRIC_ADAPTER_PATH = ROOT / "analysis/build_geometric_composition_packet_v4.py"


def _build_packet(adapter: str, document: dict[str, Any], digest: str) -> dict[str, Any]:
    if adapter == "command_motion_v2":
        return base.build_command_packet(document, source_sha256=digest)
    if adapter == "geometric_v4":
        return build_geometric_packet(document, source_sha256=digest)
    raise ValueError(f"unsupported coverage-complete-v4 composition adapter: {adapter}")


def frozen_artifact_paths(contract: dict[str, Any]) -> dict[str, Path]:
    paths = {
        "registry": base.REGISTRY_PATH,
        "composer": base.COMPOSER_PATH,
        "command_adapter": base.COMMAND_ADAPTER_PATH,
        "geometric_adapter": GEOMETRIC_ADAPTER_PATH,
        "renderer": base.RENDERER_PATH,
        "reference_builder": base.REFERENCE_BUILDER_PATH,
        "command_reference_builder": base.COMMAND_REFERENCE_BUILDER_PATH,
        "packet_builder": base.PACKET_BUILDER_PATH,
        "base_runner": BASE_RUNNER_PATH,
        "runner": RUNNER_PATH,
        "baseline_prompt": ROOT / contract["baseline"]["prompt"],
        "reference_inventory": ROOT / contract["reference_inventory"],
    }
    paths.update(
        {f"baseline_tool:{name}": path for name, path in base.BASELINE_TOOL_PATHS.items()}
    )
    return paths


def verify_frozen_artifacts(contract: dict[str, Any]) -> None:
    declared = contract.get("frozen_artifact_sha256")
    paths = frozen_artifact_paths(contract)
    if not isinstance(declared, dict) or set(declared) != set(paths):
        raise ValueError("frozen artifact hash inventory is incomplete")
    mismatches = [
        name for name, path in paths.items() if declared[name] != base.sha256_path(path)
    ]
    if mismatches:
        raise ValueError("frozen artifact hash mismatch: " + ", ".join(sorted(mismatches)))


@contextmanager
def _successor_transport() -> Iterator[None]:
    replacements = {
        "CONTRACT_SCHEMA": CONTRACT_SCHEMA,
        "RUN_SCHEMA": RUN_SCHEMA,
        "GEOMETRIC_ADAPTER_PATH": GEOMETRIC_ADAPTER_PATH,
        "RUNNER_PATH": RUNNER_PATH,
        "_build_packet": _build_packet,
        "frozen_artifact_paths": frozen_artifact_paths,
        "verify_frozen_artifacts": verify_frozen_artifacts,
    }
    previous = {name: getattr(base, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(base, name, value)
        yield
    finally:
        for name, value in previous.items():
            setattr(base, name, value)


class _NamespacedCaller:
    def __init__(self, delegate: Any):
        self.delegate = delegate

    def call(self, call_id: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        prefix = "measurement-complete-v2-"
        if not call_id.startswith(prefix):
            raise ValueError("unexpected inherited baseline call identity")
        return self.delegate.call(
            "coverage-complete-v4-" + call_id[len(prefix) :], *args, **kwargs
        )


def run(args: argparse.Namespace, caller: Any = None) -> dict[str, Any]:
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    model = contract.get("model", {})
    if caller is None:
        caller = base.caller_for(
            model["provider"], args.cache, model["model"], model["reasoning_effort"]
        )

    with tempfile.TemporaryDirectory(prefix="crane-coverage-complete-v4-runner-") as temporary:
        inherited_args = copy.copy(args)
        inherited_args.output = Path(temporary) / "inherited-result.json"
        with _successor_transport():
            result = base.run(inherited_args, caller=_NamespacedCaller(caller))

    result["schema"] = RUN_SCHEMA
    result["question_id"] = f"coverage-complete-v4:{result['case_id']}"
    for output in result["outputs"]:
        if output["condition"] == "P":
            output["generation_method"] = "coverage_complete_checked_composition_v4_deterministic"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
