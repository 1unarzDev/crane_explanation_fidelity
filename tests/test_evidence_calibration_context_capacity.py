import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_context_capacity import OBSERVATION, audit  # noqa: E402


def changed(tmp_path, mutate):
    record = json.loads(OBSERVATION.read_text())
    mutate(record)
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(record))
    return path


def test_observed_metadata_and_failed_resolver_do_not_certify_token_fit():
    result = audit()
    assert result["cli_catalog_effective_default_tokens"] == 258400
    assert result["published_api_context_window"] == 1050000
    assert result["published_and_cli_catalog_limits_differ"] is True
    assert result["baseline_request_count"] == 120
    assert result["token_fit"] is None
    assert result["model_calls_authorized"] is False


def test_unsupported_tokenizer_alias_cannot_be_substituted(tmp_path):
    path = changed(tmp_path, lambda x: x["exact_tokenizer_resolution"][0].update(alternate_encoding_selected=True))
    with pytest.raises(ValueError, match="alternate encoding"):
        audit(path)


def test_context_override_or_claimed_provider_success_is_rejected(tmp_path):
    path = changed(tmp_path, lambda x: x["config_observation"].update(context_window_override_present=True))
    with pytest.raises(ValueError, match="configuration scope"):
        audit(path)
    path = changed(tmp_path, lambda x: x.update(provider_route_capacity_verified=True))
    with pytest.raises(ValueError, match="cannot activate"):
        audit(path)


def test_cached_model_instructions_or_identity_cannot_enter_selected_metadata(tmp_path):
    path = changed(tmp_path, lambda x: x["codex_catalog"]["selected_model"].update(model_messages="extra context"))
    with pytest.raises(ValueError, match="sanitized"):
        audit(path)


def test_boolean_capacity_limit_is_not_an_integer_count(tmp_path):
    path = changed(tmp_path, lambda x: x["codex_catalog"]["selected_model"].update(context_window=True))
    with pytest.raises(ValueError, match="invalid limits"):
        audit(path)
