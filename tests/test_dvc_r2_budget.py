from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_dvc_r2_budget", ROOT / "scripts/check_dvc_r2_budget.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_remote_usage_classifies_operations_and_uses_monthly_bucket_peaks(monkeypatch):
    def fake_graphql(token, query, variables):
        assert token == "token"
        assert variables["accountTag"] == "account"
        return {
            "r2OperationsAdaptiveGroups": [
                {"dimensions": {"actionType": "PutObject"}, "sum": {"requests": 11}},
                {"dimensions": {"actionType": "GetObject"}, "sum": {"requests": 22}},
                {
                    "dimensions": {"actionType": "GetBucketNotificationConfiguration"},
                    "sum": {"requests": 2},
                },
                {
                    "dimensions": {"actionType": "GetBucketSippyConfiguration"},
                    "sum": {"requests": 1},
                },
                {"dimensions": {"actionType": "DeleteObject"}, "sum": {"requests": 3}},
            ],
            "r2StorageAdaptiveGroups": [
                {
                    "dimensions": {"bucketName": "a", "datetime": "later"},
                    "max": {"payloadSize": 100, "metadataSize": 5},
                },
                {
                    "dimensions": {"bucketName": "a", "datetime": "earlier"},
                    "max": {"payloadSize": 150, "metadataSize": 5},
                },
                {
                    "dimensions": {"bucketName": "b", "datetime": "later"},
                    "max": {"payloadSize": 200, "metadataSize": 10},
                },
            ],
        }

    monkeypatch.setattr(MODULE, "graphql", fake_graphql)
    usage = MODULE.remote_usage("account", "token")
    assert usage["class_a"] == 11
    assert usage["class_b"] == 25
    assert usage["free"] == 3
    assert usage["storage_bytes_rolling_peak_upper_bound"] == 365
    assert usage["bucket_count_observed"] == 2


def test_remote_usage_refuses_unknown_operation_type(monkeypatch):
    monkeypatch.setattr(
        MODULE,
        "graphql",
        lambda *args, **kwargs: {
            "r2OperationsAdaptiveGroups": [
                {"dimensions": {"actionType": "FutureOperation"}, "sum": {"requests": 1}}
            ],
            "r2StorageAdaptiveGroups": [],
        },
    )
    with pytest.raises(SystemExit, match="unclassified R2 operation"):
        MODULE.remote_usage("account", "token")


def test_guard_thresholds_leave_ten_percent_headroom():
    assert MODULE.GUARD_STORAGE_BYTES == int(MODULE.FREE_STORAGE_BYTES * 0.9)
    assert MODULE.GUARD_CLASS_A == int(MODULE.FREE_CLASS_A * 0.9)
    assert MODULE.GUARD_CLASS_B == int(MODULE.FREE_CLASS_B * 0.9)


def test_graphql_refuses_missing_account(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(MODULE.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(
        MODULE.json,
        "load",
        lambda response: {"data": {"viewer": {"accounts": []}}},
    )
    with pytest.raises(SystemExit, match="exactly one account"):
        MODULE.graphql("token", "query", {})
