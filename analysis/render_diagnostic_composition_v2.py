#!/usr/bin/env python3
"""Render all checked v2 answer units without exposing internal registry metadata."""

from __future__ import annotations

from typing import Any


def _section(title: str, values: list[str]) -> str:
    return f"{title}:\n" + "\n".join(f"- {value}" for value in values)


def render(certificate: dict[str, Any]) -> str:
    if certificate.get("schema") != "crane-diagnostic-composition-certificate/v2":
        raise ValueError("unsupported v2 composition certificate")
    if certificate.get("status") != "composed":
        raise ValueError("cannot render an evidence-problem certificate")
    plan = certificate.get("answer_plan")
    if not isinstance(plan, dict) or plan.get("language_ready") is not True:
        raise ValueError("v2 composition certificate is not language-ready")
    units = plan.get("units")
    if not isinstance(units, list) or not units:
        raise ValueError("v2 composition certificate has no answer units")
    if [item.get("unit_id") for item in units] != plan.get("compiled_unit_ids"):
        raise ValueError("v2 compiled answer-unit inventory differs")

    by_role: dict[str, list[str]] = {}
    seen: set[str] = set()
    for item in units:
        text = item.get("text")
        role = item.get("role")
        if not isinstance(text, str) or not text.strip() or role not in {
            "diagnosis", "evidence", "execution", "limit", "outcome"
        }:
            raise ValueError("v2 answer unit is invalid")
        normalized = " ".join(text.split())
        if normalized in seen:
            continue
        seen.add(normalized)
        by_role.setdefault(role, []).append(text)

    diagnosis = by_role.get("diagnosis") or [plan["primary_claim"]]
    decisive = by_role.get("evidence", []) + by_role.get("execution", [])
    sections = [_section("Diagnosis", diagnosis)]
    if decisive:
        sections.append(_section("Decisive evidence", decisive))
    if by_role.get("outcome"):
        sections.append(_section("Recorded outcome", by_role["outcome"]))
    if by_role.get("limit"):
        sections.append(_section("Limits", by_role["limit"]))
    rendered = "\n\n".join(sections)
    if "certificate" in rendered.lower() or "declared registry" in rendered.lower():
        raise ValueError("v2 renderer exposed internal certificate or registry metadata")
    return rendered
