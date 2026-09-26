#!/usr/bin/env python3
"""Deterministically render an audited diagnostic-composition certificate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _section(title: str, values: list[str]) -> str:
    return f"{title}:\n" + "\n".join(f"- {value}" for value in values)


def render(certificate: dict[str, Any]) -> str:
    if certificate.get("schema") != "crane-diagnostic-composition-certificate/v1":
        raise ValueError("unsupported composition certificate")
    if certificate.get("status") != "composed":
        raise ValueError("cannot render an evidence-problem certificate")
    plan = certificate.get("answer_plan")
    if not isinstance(plan, dict):
        raise ValueError("composition certificate has no answer plan")
    if plan.get("language_ready") is not True:
        missing = plan.get("missing_required_unit_ids", [])
        detail = f"; missing required units: {', '.join(missing)}" if missing else ""
        raise ValueError(f"composition certificate is not language-ready{detail}")
    units = plan.get("units", [])
    by_role: dict[str, list[str]] = {}
    for item in units:
        by_role.setdefault(item["role"], []).append(item["text"])

    diagnosis = by_role.get("diagnosis", [])
    if not diagnosis:
        diagnosis = [
            plan.get("primary_claim")
            or "The retained evidence does not entail one of the registered diagnostic mechanisms."
        ]
    decisive = by_role.get("evidence", []) + by_role.get("execution", [])
    if not decisive:
        decisive = ["No additional decisive measurement unit is available in the checked plan."]
    limits = by_role.get("limit", []) + [plan["scope_limit"]]
    if plan.get("missing_discriminators"):
        limits.append(
            "Missing discriminators: " + ", ".join(plan["missing_discriminators"]) + "."
        )
    outcome = by_role.get("outcome", [])

    sections = [
        _section("Diagnosis", diagnosis),
        _section("Decisive evidence", decisive),
    ]
    if outcome:
        sections.append(_section("Recorded outcome", outcome))
    sections.append(_section("Limits", limits))
    return "\n\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(certificate) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
