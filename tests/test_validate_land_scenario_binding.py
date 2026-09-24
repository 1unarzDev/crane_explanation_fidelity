import hashlib
import json
from pathlib import Path

from analysis.validate_land_scenario_binding import validate_binding


def catalog_and_hash():
    catalog = {
        "layouts": [
            {
                "id": "development-detour-001",
                "seed": 42,
                "generatorSeed": 42,
                "studySplit": "development",
                "diagnosticMechanism": "connected-detour",
                "expectedBroadOutcome": "avoidance-and-path-change",
                "relevantObstacles": ["barrier-near", "barrier-far"],
                "obstacles": [
                    {"id": "barrier-near", "activeInitially": True},
                    {"id": "barrier-far", "activeInitially": True},
                ],
            }
        ]
    }
    encoded = json.dumps(catalog).encode()
    return catalog, hashlib.sha256(encoded).hexdigest()


def valid_truth(catalog_sha256):
    return {
        "schema": "crane-land-proving-ground-truth-v1",
        "environmentId": "crane-land-proving-ground-v4",
        "manifestSha256": catalog_sha256,
        "layoutId": "development-detour-001",
        "seed": 42,
        "generatorSeed": 42,
        "studySplit": "development",
        "diagnosticMechanism": "connected-detour",
        "expectedBroadOutcome": "avoidance-and-path-change",
        "relevantObstacles": ["barrier-near", "barrier-far"],
        "obstacleSemanticIds": ["barrier-near", "barrier-far"],
        "obstacleActive": [True, True],
    }


def test_exact_proving_ground_binding_is_accepted():
    catalog, digest = catalog_and_hash()
    result = validate_binding(
        valid_truth(digest), catalog, catalog_sha256=digest,
        catalog_id="v4", layout_id="development-detour-001"
    )
    assert result["accepted"] is True
    assert result["failed_checks"] == []


def test_legacy_corridor_truth_fails_closed_for_requested_layout():
    catalog, digest = catalog_and_hash()
    truth = {
        "schema": "crane-land-corridor-truth-v1",
        "seed": 42,
        "blocker": "none",
    }
    result = validate_binding(
        truth, catalog, catalog_sha256=digest,
        catalog_id="v4", layout_id="development-detour-001"
    )
    assert result["accepted"] is False
    assert "truth_schema" in result["failed_checks"]
    assert "layout_id" in result["failed_checks"]
    assert "relevant_obstacles" in result["failed_checks"]


def test_misspelled_or_wrong_layout_id_is_rejected():
    catalog, digest = catalog_and_hash()
    truth = valid_truth(digest)
    truth["layoutId"] = "development-detour-01"
    result = validate_binding(
        truth, catalog, catalog_sha256=digest,
        catalog_id="v4", layout_id="development-detour-001"
    )
    assert result["accepted"] is False
    assert result["failed_checks"] == ["layout_id"]


def test_inactive_expected_obstacle_is_rejected():
    catalog, digest = catalog_and_hash()
    truth = valid_truth(digest)
    truth["obstacleActive"] = [True, False]
    result = validate_binding(
        truth, catalog, catalog_sha256=digest,
        catalog_id="v4", layout_id="development-detour-001"
    )
    assert result["accepted"] is False
    assert result["failed_checks"] == ["obstacles_active"]
