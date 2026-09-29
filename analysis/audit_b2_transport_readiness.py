#!/usr/bin/env python3
"""Fail-fast, non-study readiness audit for the B2 Codex transport."""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tomllib
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def assess(
    *,
    provider_name: str,
    base_url: str,
    wire_api: str | None,
    cli_path: str | None,
    cli_version: str | None,
    credential_present: bool,
    resolved_addresses: list[str],
    chatgpt_login_present: bool = False,
    alternate_dns: dict[str, list[str]] | None = None,
    sandbox_network_disabled: bool = False,
) -> dict[str, Any]:
    hostname = urlparse(base_url).hostname
    checks = {
        "codex_cli_available": bool(cli_path and cli_version),
        "provider_base_url_https": urlparse(base_url).scheme == "https" and bool(hostname),
        "responses_wire_api": wire_api == "responses",
        "authentication_present": credential_present or chatgpt_login_present,
        "provider_dns_resolved": bool(resolved_addresses),
    }
    checks["parent_network_enabled"] = not sandbox_network_disabled
    ready = all(checks.values())
    alternate_dns = alternate_dns or {}
    alternate_route = {
        "chatgpt_login_present": chatgpt_login_present,
        "dns": {host: bool(addresses) for host, addresses in sorted(alternate_dns.items())},
    }
    alternate_route["status"] = (
        "LOGIN_ROUTE_NETWORK_REACHABLE"
        if chatgpt_login_present and any(alternate_route["dns"].values())
        else "LOGIN_PRESENT_BUT_NETWORK_UNRESOLVED"
        if chatgpt_login_present
        else "LOGIN_ROUTE_UNAVAILABLE"
    )
    status = (
        "READY_FOR_SCHEMA_CANARY"
        if ready
        else "RUN_FROM_NETWORK_ENABLED_HOST"
        if sandbox_network_disabled
        else "TRANSPORT_PREFLIGHT_BLOCKED"
    )
    return {
        "schema": "crane-evidence-calibration-b2-transport-readiness/v1",
        "audit_id": "evidence-calibration-b2-transport-canary-v1",
        "recorded_date": date.today().isoformat(),
        "scope": "NON_STUDY_INFRASTRUCTURE_CANARY",
        "provider_name": provider_name,
        "provider_scheme": urlparse(base_url).scheme,
        "provider_hostname": hostname,
        "wire_api": wire_api,
        "codex_cli_path": cli_path,
        "codex_cli_version": cli_version,
        "resolved_address_count": len(resolved_addresses),
        "checks": checks,
        "authentication": {
            "codex_lb_api_key_present": credential_present,
            "chatgpt_login_present": chatgpt_login_present,
            "secret_values_recorded": False,
        },
        "execution_environment": {
            "codex_sandbox_network_disabled": sandbox_network_disabled,
            "bubblewrap_share_net_can_bypass_parent": False,
        },
        "alternate_chatgpt_login_route": alternate_route,
        "status": status,
        "next_action": (
            "Run this same audit from a normal network-enabled host terminal; do not change DNS, credentials, repository artifacts, or caches in this managed session."
            if sandbox_network_disabled
            else "Run the non-study schema canary."
            if ready
            else "Resolve the failed host-terminal preflight check before any model call."
        ),
        "model_call_attempted": False,
        "study_request_attempted": False,
        "scientific_sample": False,
        "confirmation_independent_n": 0,
        "replication_independent_n": 0,
    }


def audit(config_path: Path, environ: dict[str, str]) -> dict[str, Any]:
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    provider_name = config.get("model_provider")
    provider = config.get("model_providers", {}).get(provider_name)
    if not isinstance(provider_name, str) or not isinstance(provider, dict):
        raise ValueError("active Codex model provider is missing")
    base_url = provider.get("base_url")
    if not isinstance(base_url, str):
        raise ValueError("active provider base_url is missing")
    hostname = urlparse(base_url).hostname
    addresses: list[str] = []
    if hostname:
        try:
            addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, 443)})
        except socket.gaierror:
            addresses = []
    cli_path = shutil.which("codex")
    cli_version = None
    if cli_path:
        completed = subprocess.run(
            [cli_path, "--version"], text=True, capture_output=True, check=False, timeout=10
        )
        if completed.returncode == 0:
            cli_version = completed.stdout.strip()
    env_key = provider.get("env_key")
    credential_present = isinstance(env_key, str) and bool(environ.get(env_key))
    auth_path = config_path.parent / "auth.json"
    chatgpt_login_present = False
    if auth_path.is_file():
        try:
            auth = json.loads(auth_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            auth = {}
        chatgpt_login_present = auth.get("auth_mode") == "chatgpt" and isinstance(
            auth.get("tokens"), dict
        )
    alternate_dns: dict[str, list[str]] = {}
    for alternate_host in ("api.openai.com", "chatgpt.com", "auth.openai.com"):
        try:
            alternate_dns[alternate_host] = sorted(
                {item[4][0] for item in socket.getaddrinfo(alternate_host, 443)}
            )
        except socket.gaierror:
            alternate_dns[alternate_host] = []
    return assess(
        provider_name=provider_name,
        base_url=base_url,
        wire_api=provider.get("wire_api"),
        cli_path=cli_path,
        cli_version=cli_version,
        credential_present=credential_present,
        resolved_addresses=addresses,
        chatgpt_login_present=chatgpt_login_present,
        alternate_dns=alternate_dns,
        sandbox_network_disabled=environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path.home() / ".codex/config.toml")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "manifests/operations/evidence-calibration-b2-transport-canary-v1.json",
    )
    args = parser.parse_args()
    result = audit(args.config, dict(os.environ))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
