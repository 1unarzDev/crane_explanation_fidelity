import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "run_diagnostic_land_capture.sh"
MANIFEST_BUILDER = ROOT / "scripts" / "build_diagnostic_runtime_manifest.py"


def test_print_config_resolves_proving_ground_capture_contract():
    completed = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--print-config",
            "diagnostic-land-dev-002",
            "121",
            "12321",
            "v4",
            "diagnostic-development-connected-detour-002",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    config = json.loads(completed.stdout)
    assert config == {
        "action_duration_s": 100,
        "bt_xml": "packages/crane_ml/Tools/Performance/nav2_roboboat_distance_replanning.xml",
        "catalog": "v4",
        "command_flag": "--crane-ros-differential-cmd-vel",
        "data_split": "dev",
        "diagnostic_mechanism": "connected-detour",
        "goal_distance_m": 18.0,
        "layout": "diagnostic-development-connected-detour-002",
        "layout_seed": 62001,
        "lidar_frame": "base_scan",
        "nav2_params": "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml",
        "ros_domain_id": 121,
        "ros_tcp_port": 12321,
        "run_id": "diagnostic-land-dev-002",
        "runtime_manifest_builder": "scripts/build_diagnostic_runtime_manifest.py",
        "scene": "TurtleBot3 Warehouse Validation",
        "schema": "crane-diagnostic-land-capture-config/v1",
    }


@pytest.mark.parametrize(
    ("extra_env", "layout", "expected_error"),
    [
        (
            {},
            "diagnostic-confirmatory-connected-detour-001",
            "confirmatory layouts are sealed until protocol freeze",
        ),
        (
            {},
            "diagnostic-development-grid-disconnection-001",
            "calibration-only or outside the active diagnostic scope",
        ),
        (
            {"CRANE_DATA_SPLIT": "final"},
            "diagnostic-development-connected-detour-002",
            "held-out/final capture is not authorized before protocol freeze",
        ),
    ],
)
def test_capture_contract_fails_closed_before_prospective_freeze(
    extra_env, layout, expected_error, monkeypatch
):
    monkeypatch.delenv("CRANE_DATA_SPLIT", raising=False)
    for name, value in extra_env.items():
        monkeypatch.setenv(name, value)

    completed = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--print-config",
            "diagnostic-land-dev-rejected",
            "121",
            "12321",
            "v4",
            layout,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2 or completed.returncode == 1
    assert expected_error in completed.stderr


def test_capture_rejects_legacy_corridor_intervention_with_proving_ground(monkeypatch):
    monkeypatch.setenv(
        "CRANE_NAV2_UNITY_EXTRA_ARGS", "--crane-land-mobility-hold-after 18.0"
    )

    completed = subprocess.run(
        [
            "bash",
            str(SCRIPT),
            "--print-config",
            "diagnostic-land-composition-rejected",
            "130",
            "12328",
            "v4",
            "diagnostic-development-connected-detour-008",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "cannot be combined with legacy corridor interventions" in completed.stderr


def test_runtime_manifest_hashes_the_executed_nav2_fixture_observer():
    text = MANIFEST_BUILDER.read_text(encoding="utf-8")

    assert '"Tools/Performance/nav2_follow_path_fixture.py"' in text
    assert '"nav2_fixture_observer"' in text


def test_capture_requires_exact_post_run_scenario_binding():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "validate_land_scenario_binding.py" in text
    assert "--catalog-id \"${catalog}\"" in text
    assert "--layout \"${layout}\"" in text
    assert "scenario-binding-audit.json" in text


def test_capture_requires_declared_full_player_bundle_before_launch():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "CRANE_EXPECTED_BUILD_MANIFEST_SHA256" in text
    assert "CRANE_EXPECTED_MANAGED_ASSEMBLIES_SHA256" in text
    assert "validate_diagnostic_player_build.py" in text
    assert "player-build-audit.json" in text
    assert '--catalog "${catalog_file}"' in text
    assert '--player "${player}"' in text
    assert text.index("validate_diagnostic_player_build.py") < text.index("docker run -d")
