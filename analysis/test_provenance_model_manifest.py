from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_provenance_model_manifest.py")
SPEC = importlib.util.spec_from_file_location("build_provenance_model_manifest", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_condition_accounting_separates_model_calls_from_smoke_outputs() -> None:
    outputs = [
        {
            "outputs": [
                {"condition": condition}
                for condition in ("A", "B", "C", "D", "E", "F", "G", "H")
            ]
        }
        for _ in range(2)
    ]
    calls = [
        {"request": {"workspace_identity": {"condition": condition}}}
        for condition in ("F", "G", "H", "F", "G", "H")
    ]

    assert MODULE.condition_accounting(outputs, calls) == {
        "conditions": ["F", "G", "H"],
        "model_condition_outputs": 6,
        "embedded_non_model_smoke_conditions": ["A", "B", "C", "D", "E"],
        "embedded_non_model_smoke_outputs": 10,
        "result_envelope_conditions": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "result_envelope_outputs": 16,
    }
