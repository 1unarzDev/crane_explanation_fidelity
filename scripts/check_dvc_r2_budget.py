#!/usr/bin/env python3
"""Refuse DVC/R2 transfers that approach Cloudflare's monthly free tier.

Cloudflare R2 does not expose a server-side spending cap. This guard is deliberately conservative:
it uses 90% of the published Standard-storage free tier, queries account-wide month-to-date metrics
when requested, overestimates the pending DVC transfer, and refuses unknown operation types.
Metrics may lag, so this is a safety interlock rather than a billing guarantee.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parent.parent
TRACKED_ROOTS = (
    Path("data/robot_visible/dev"),
    Path("data/robot_visible/final"),
    Path("data/evaluator_only/dev"),
    Path("data/evaluator_only/final"),
    Path("model_outputs"),
    Path("research/explanation_fidelity/model_cache"),
)

# Published monthly Standard-storage free tier (decimal GB, as billed by Cloudflare).
FREE_STORAGE_BYTES = 10_000_000_000
FREE_CLASS_A = 1_000_000
FREE_CLASS_B = 10_000_000

# Refuse at 90% to leave room for metric delay, DVC metadata, and non-project R2 activity.
GUARD_STORAGE_BYTES = 9_000_000_000
GUARD_CLASS_A = 900_000
GUARD_CLASS_B = 9_000_000

CLASS_A = {
    "ListBuckets",
    "PutBucket",
    "ListObjects",
    "PutObject",
    "CopyObject",
    "CompleteMultipartUpload",
    "CreateMultipartUpload",
    "LifecycleStorageTierTransition",
    "ListMultipartUploads",
    "UploadPart",
    "UploadPartCopy",
    "ListParts",
    "PutBucketEncryption",
    "PutBucketCors",
    "PutBucketLifecycleConfiguration",
}
CLASS_B = {
    "HeadBucket",
    "HeadObject",
    "GetObject",
    "UsageSummary",
    "GetBucketEncryption",
    "GetBucketLocation",
    "GetBucketCors",
    "GetBucketLifecycleConfiguration",
    # Read-only configuration requests emitted by the R2 dashboard/API. Cloudflare describes
    # Class B as reads of existing state; these newer action names are not yet enumerated in the
    # pricing-page example list.
    "GetBucketNotificationConfiguration",
    "GetBucketSippyConfiguration",
}
FREE_OPERATIONS = {"DeleteObject", "DeleteBucket", "AbortMultipartUpload"}


def local_inventory() -> dict[str, int]:
    files = 0
    directories = 0
    size = 0
    for relative in TRACKED_ROOTS:
        root = WORKSPACE / relative
        if not root.exists():
            continue
        directories += 1
        for path in root.rglob("*"):
            if path.is_symlink():
                raise SystemExit(f"refusing symlink in governed DVC root: {path}")
            if path.is_dir():
                directories += 1
            elif path.is_file():
                files += 1
                size += path.stat().st_size
    # DVC writes content objects plus directory metadata. A 3x request multiplier is deliberately
    # pessimistic for the current small-file workload and leaves ample free-tier headroom.
    estimated_objects = files + directories
    return {
        "bytes": size,
        "files": files,
        "directories": directories,
        "estimated_objects": estimated_objects,
        "estimated_transfer_operations": 3 * estimated_objects + 100,
    }


def graphql(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError) as error:
        raise SystemExit(f"Cloudflare metrics query failed: {error}") from error
    if payload.get("errors"):
        raise SystemExit(f"Cloudflare metrics query returned errors: {payload['errors']}")
    accounts = payload.get("data", {}).get("viewer", {}).get("accounts", [])
    if len(accounts) != 1:
        raise SystemExit(
            "Cloudflare metrics query did not return exactly one account; refusing sync"
        )
    return accounts[0]


def remote_usage(account_id: str, token: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    # Cloudflare retains 31 days of R2 metrics. A rolling window avoids relying on an assumed
    # billing-cycle boundary and can only overcount operations relative to a monthly reset.
    start = now - timedelta(days=31)
    query = """
    query R2Budget($accountTag: string!, $start: Time!, $end: Time!) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          r2OperationsAdaptiveGroups(
            limit: 10000
            filter: {datetime_geq: $start, datetime_leq: $end}
          ) { sum { requests } dimensions { actionType } }
          r2StorageAdaptiveGroups(
            limit: 10000
            filter: {datetime_geq: $start, datetime_leq: $end}
            orderBy: [datetime_DESC]
          ) {
            max { objectCount uploadCount payloadSize metadataSize }
            dimensions { bucketName datetime }
          }
        }
      }
    }
    """
    account = graphql(
        token,
        query,
        {"accountTag": account_id, "start": start.isoformat(), "end": now.isoformat()},
    )
    operations = account["r2OperationsAdaptiveGroups"]
    if len(operations) >= 10_000:
        raise SystemExit("R2 operations query reached its row limit; usage is not safely bounded")
    totals = {"class_a": 0, "class_b": 0, "free": 0}
    unknown: dict[str, int] = {}
    for row in operations:
        action = row["dimensions"]["actionType"]
        requests = int(row["sum"]["requests"])
        if action in CLASS_A:
            totals["class_a"] += requests
        elif action in CLASS_B:
            totals["class_b"] += requests
        elif action in FREE_OPERATIONS:
            totals["free"] += requests
        else:
            unknown[action] = unknown.get(action, 0) + requests
    if unknown:
        raise SystemExit(f"unclassified R2 operation types; refusing sync: {unknown}")

    storage_rows = account["r2StorageAdaptiveGroups"]
    if len(storage_rows) >= 10_000:
        raise SystemExit("R2 storage query reached its row limit; usage is not safely bounded")
    # Sum each account bucket's largest observed value in the window. This deliberately overestimates
    # the account-wide daily-average GB-month calculation and is safer than using only the latest
    # value, especially after objects have been removed.
    peak_by_bucket: dict[str, int] = {}
    for row in storage_rows:
        bucket = row["dimensions"]["bucketName"]
        value = int(row["max"]["payloadSize"] or 0) + int(row["max"]["metadataSize"] or 0)
        peak_by_bucket[bucket] = max(peak_by_bucket.get(bucket, 0), value)
    return {
        **totals,
        "storage_bytes_rolling_peak_upper_bound": sum(peak_by_bucket.values()),
        "bucket_count_observed": len(peak_by_bucket),
        "metrics_start_utc": start.isoformat(),
        "metrics_end_utc": now.isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", choices=("push", "pull", "status"), default="status")
    parser.add_argument(
        "--require-remote-metrics",
        action="store_true",
        help="query account-wide Cloudflare R2 metrics and refuse when unavailable",
    )
    args = parser.parse_args()
    local = local_inventory()
    result: dict[str, Any] = {
        "schema": "crane-explain-r2-budget-check/v1",
        "operation": args.operation,
        "server_side_hard_cap_available": False,
        "published_free_tier": {
            "storage_bytes_month": FREE_STORAGE_BYTES,
            "class_a_operations_month": FREE_CLASS_A,
            "class_b_operations_month": FREE_CLASS_B,
            "standard_storage_only": True,
        },
        "local_guard_at_90_percent": {
            "storage_bytes": GUARD_STORAGE_BYTES,
            "class_a_operations": GUARD_CLASS_A,
            "class_b_operations": GUARD_CLASS_B,
        },
        "local_inventory": local,
        "remote_usage": None,
        "accepted": False,
    }
    projected_storage = local["bytes"] if args.operation == "push" else 0
    # DVC may list or write objects (Class A) and issue HEAD/GET requests (Class B) for any cloud
    # action, including status. Budget the full pessimistic estimate against both classes rather
    # than trying to predict a backend-specific request sequence.
    projected_a = local["estimated_transfer_operations"]
    projected_b = local["estimated_transfer_operations"]

    if args.require_remote_metrics:
        account_id = os.environ.get("R2_ACCOUNT_ID")
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not account_id or not token:
            raise SystemExit(
                "R2_ACCOUNT_ID and CLOUDFLARE_API_TOKEN (Account Analytics Read) are required"
            )
        remote = remote_usage(account_id, token)
        result["remote_usage"] = remote
        projected_storage += remote["storage_bytes_rolling_peak_upper_bound"]
        projected_a += remote["class_a"]
        projected_b += remote["class_b"]

    result["projected_upper_bound"] = {
        "storage_bytes": projected_storage,
        "class_a_operations": projected_a,
        "class_b_operations": projected_b,
    }
    violations = []
    if projected_storage >= GUARD_STORAGE_BYTES:
        violations.append("storage")
    if projected_a >= GUARD_CLASS_A:
        violations.append("class_a")
    if projected_b >= GUARD_CLASS_B:
        violations.append("class_b")
    result["violations"] = violations
    result["accepted"] = not violations
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
