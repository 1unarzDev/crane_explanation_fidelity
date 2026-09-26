#!/usr/bin/env python3
"""Measurement-complete wrapper around the finite v1 diagnostic composer."""

from __future__ import annotations

import copy
from typing import Any

from compose_diagnostic_hypotheses import compose as compose_v1


CERTIFICATE_SCHEMA = "crane-diagnostic-composition-certificate/v2"


def compose(packet: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Compose as v1, then retain every supported adapter-authored answer unit.

    The v1 reasoner still selects and verifies the primary mechanism. The v2 language
    contract prevents useful supported measurements and limits from disappearing merely
    because they are not prerequisites of that one mechanism.
    """
    result = copy.deepcopy(compose_v1(packet, registry))
    result["schema"] = CERTIFICATE_SCHEMA
    result["composition_version"] = "measurement-complete-checked-composition-v2"
    plan = result.get("answer_plan")
    if result.get("status") != "composed" or not isinstance(plan, dict):
        return result
    if plan.get("language_ready") is not True:
        return result
    units = packet.get("answer_units")
    if not isinstance(units, list) or not units:
        raise ValueError("v2 composition requires adapter-authored answer units")
    unit_ids = [item.get("unit_id") for item in units]
    if any(not isinstance(value, str) or not value for value in unit_ids):
        raise ValueError("v2 composition received an invalid answer-unit ID")
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("v2 composition received duplicate answer-unit IDs")
    plan["units"] = copy.deepcopy(units)
    plan["compiled_unit_ids"] = unit_ids
    plan["render_internal_scope_metadata"] = False
    return result
