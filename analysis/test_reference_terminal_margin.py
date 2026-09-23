import json
from pathlib import Path

from reference_terminal_margin import calculate


ROOT = Path(__file__).resolve().parents[1]
UNMASKED = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json"
MASKED = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin-masked-speed/evidence.json"
CONFIG = b"xy_goal_tolerance: 0.40\ntrans_stopped_velocity: 0.05\n"


def payload(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    import hashlib

    result["source"]["config_sha256"] = hashlib.sha256(CONFIG).hexdigest()
    return result


def test_unmasked_supports_positional_and_full_terminal_margin_chain():
    result = calculate(payload(UNMASKED), CONFIG)

    findings = result["reference_findings"]
    assert findings["positional_failure_chain_supported"] is True
    assert findings["stopped_speed_state"] == "measured_within_configured_threshold"
    assert findings["full_terminal_margin_mechanism_supported"] is True
    assert findings["physical_source_of_residual_motion"] == "unresolved"


def test_masked_speed_preserves_positional_chain_but_not_stopped_state():
    result = calculate(payload(MASKED), CONFIG)

    findings = result["reference_findings"]
    assert findings["positional_failure_chain_supported"] is True
    assert findings["stopped_speed_state"] == "unresolved_missing_measured_speed"
    assert findings["full_terminal_margin_mechanism_supported"] is False
    assert "exceeded the remaining positional margin" in result["allowed_conclusion"]


def test_reference_ignores_proposed_derived_result():
    evidence = payload(UNMASKED)
    evidence["diagnostic_result"] = {"disposition": "contradictory-sentinel"}

    result = calculate(evidence, CONFIG)

    assert result["reference_findings"]["full_terminal_margin_mechanism_supported"] is True
