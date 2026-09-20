#!/usr/bin/env python3
"""Content-address the files governing the sealed provenance study."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

FROZEN_PATHS = (
    "docs/STUDY_DESIGN.md",
    "docs/ANNOTATION_GUIDE.md",
    "docs/BENCHMARK.md",
    "research/explanation_fidelity/dataset_splits/provenance-final-v1.json",
    "research/explanation_fidelity/prompts/direct_v1.txt",
    "research/explanation_fidelity/prompts/extraction_v1.txt",
    "research/explanation_fidelity/prompts/realization_v1.txt",
    "research/explanation_fidelity/prompts/repository_agent_v1.txt",
    "research/explanation_fidelity/prompts/checked_runtime_suffix_v1.txt",
    "analysis/run_llm_episode_pilot.py",
    "analysis/run_provenance_agent_pilot.py",
    "analysis/build_fgh_runtime_presentation.py",
    "analysis/analyze_provenance_study.py",
    "analysis/scan_robot_visible_leakage.py",
    "analysis/results/provenance-power-sensitivity-20260919.json",
    "scripts/run_land_capture.sh",
    "scripts/build_runtime_manifest.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/models.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/runtime_presentation.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/reasoning.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/verification.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/realize.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/provenance.py",
    "packages/astro_dock/src/crane_explain/src/crane_explain/nav2_provenance.py",
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", "-C", str(root), *args), text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--codex-version", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = (root / args.output).resolve()
    if output.exists():
        raise SystemExit(f"refusing existing freeze manifest: {output}")
    files = []
    for relative in FROZEN_PATHS:
        path = root / relative
        payload = path.read_bytes()
        files.append(
            {"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        )
    split = json.loads(
        (root / "research/explanation_fidelity/dataset_splits/provenance-final-v1.json").read_text()
    )
    payload = {
        "schema": "crane-provenance-study-freeze/v1",
        "status": "FROZEN_BEFORE_SEALED_COLLECTION",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "umbrella_parent_before_freeze_commit": git(root, "rev-parse", "HEAD"),
        "component_commits": {
            "crane_explain_core": git(root / "packages/astro_dock/src/crane_explain", "rev-parse", "HEAD"),
            "crane_explain_ros": git(root / "packages/astro_dock/src/crane_explain_ros", "rev-parse", "HEAD"),
            "astro_dock": git(root / "packages/astro_dock", "rev-parse", "HEAD"),
            "crane_ml": git(root / "packages/crane_ml", "rev-parse", "HEAD"),
        },
        "primary_comparison": "F versus G",
        "primary_outcome": "response-level material-error rate jointly with substantive coverage",
        "coverage_noninferiority_margin": -0.05,
        "smallest_practical_absolute_risk_reduction": 0.15,
        "model": "gpt-5.6-luna",
        "reasoning_effort": "low",
        "model_calls": "single sample, no retry or resampling",
        "codex_cli_version": args.codex_version,
        "verifier": "binary exact sentence licensing; no repair call; deterministic fallback",
        "minimum_included_episodes": split["minimum_included_episodes"],
        "target_included_episodes": split["target_included_episodes"],
        "preferred_included_episodes": split["preferred_included_episodes"],
        "question_kinds": split["question_kinds"],
        "frozen_files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
