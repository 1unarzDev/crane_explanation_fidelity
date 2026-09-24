from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "run_luna_single_diagnostic_packet.py"
SPEC = importlib.util.spec_from_file_location("run_luna_single_diagnostic_packet", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_supported_success_requires_mechanism_and_no_material_error() -> None:
    assert MODULE.success({"mechanism_identification": "correct", "material_error": False})
    assert not MODULE.success({"mechanism_identification": "correct", "material_error": True})
    assert not MODULE.success({"mechanism_identification": "omitted", "material_error": False})
