import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "b2_transport", ROOT / "analysis/audit_b2_transport_readiness.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _assess(**changes):
    values = {
        "provider_name": "pilot-provider",
        "base_url": "https://provider.example/v1",
        "wire_api": "responses",
        "cli_path": "/usr/bin/codex",
        "cli_version": "codex-cli 0.158.0",
        "credential_present": True,
        "resolved_addresses": ["192.0.2.1"],
    }
    values.update(changes)
    return MODULE.assess(**values)


def test_ready_requires_every_preflight_check() -> None:
    result = _assess()
    assert result["status"] == "READY_FOR_SCHEMA_CANARY"
    assert all(result["checks"].values())
    assert result["model_call_attempted"] is False
    assert result["scientific_sample"] is False


def test_dns_failure_blocks_before_any_model_call() -> None:
    result = _assess(resolved_addresses=[])
    assert result["status"] == "TRANSPORT_PREFLIGHT_BLOCKED"
    assert result["checks"]["provider_dns_resolved"] is False
    assert result["model_call_attempted"] is False
    assert result["study_request_attempted"] is False


def test_missing_credential_blocks_without_exposing_value() -> None:
    result = _assess(credential_present=False)
    assert result["status"] == "TRANSPORT_PREFLIGHT_BLOCKED"
    assert set(result) >= {"checks", "status"}
    assert "credential" not in result


def test_chatgpt_login_is_valid_alternative_authentication() -> None:
    result = _assess(credential_present=False, chatgpt_login_present=True)
    assert result["status"] == "READY_FOR_SCHEMA_CANARY"
    assert result["checks"]["authentication_present"] is True
    assert result["authentication"]["codex_lb_api_key_present"] is False
    assert result["authentication"]["chatgpt_login_present"] is True


def test_wrong_wire_api_blocks() -> None:
    result = _assess(wire_api="chat")
    assert result["status"] == "TRANSPORT_PREFLIGHT_BLOCKED"
    assert result["checks"]["responses_wire_api"] is False


def test_login_route_is_reported_without_exposing_auth_material() -> None:
    result = _assess(
        chatgpt_login_present=True,
        alternate_dns={"api.openai.com": [], "chatgpt.com": []},
    )
    alternate = result["alternate_chatgpt_login_route"]
    assert alternate["status"] == "LOGIN_PRESENT_BUT_NETWORK_UNRESOLVED"
    assert alternate["chatgpt_login_present"] is True
    assert not any(alternate["dns"].values())
    assert "token" not in str(alternate).lower()


def test_managed_network_sandbox_requires_external_host_even_with_dns_fixture() -> None:
    result = _assess(sandbox_network_disabled=True)
    assert result["status"] == "RUN_FROM_NETWORK_ENABLED_HOST"
    assert result["checks"]["parent_network_enabled"] is False
    assert result["execution_environment"]["bubblewrap_share_net_can_bypass_parent"] is False
    assert result["model_call_attempted"] is False
