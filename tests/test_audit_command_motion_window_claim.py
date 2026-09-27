import pytest

from audit_command_motion_window_claim import audit


def test_audit_uses_half_open_window_and_declared_sample_thresholds():
    payload = {
        "schema": "crane-command-motion-diagnostic-export-v1",
        "episode_id": "e",
        "method_input": {
            "windowing": {
                "minimum_command_samples_per_window": 2,
                "minimum_odometry_samples_per_window": 2,
                "minimum_commanded_speed_mps": 0.1,
            },
            "command_samples": [
                {"offset_s": 18.0, "planar_speed_mps": 0.2},
                {"offset_s": 18.5, "planar_speed_mps": 0.4},
                {"offset_s": 19.0, "planar_speed_mps": 9.0},
            ],
            "odometry_samples": [
                {"offset_s": 18.0, "planar_speed_mps": 0.0},
                {"offset_s": 18.9, "planar_speed_mps": 0.0},
            ],
        },
    }
    result = audit(payload, 18.0, 19.0)
    assert result["command_sample_count"] == 2
    assert result["median_commanded_planar_speed_mps"] == pytest.approx(0.3)
    assert result["median_measured_planar_speed_mps"] == 0.0
    assert result["qualifying_command_motion_window"] is True
