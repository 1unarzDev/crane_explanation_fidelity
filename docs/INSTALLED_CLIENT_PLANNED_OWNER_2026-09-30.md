# Installed-client plan-bound ownership — 2026-09-30

## Candidate and checks

Preserve observer v6. Separate
`analysis/observe_evidence_calibration_app_server_mcp_v7.py` selects coordinator v2,
which wraps unchanged MCP v5/broker v7/ledger v2/executor v10. Each synthetic
observation writes a development execution plan and initializes its bound registry
before launching the offline installed client. Existing study callers do not migrate.

Read-only ownership auditing now verifies raw plan digest, permitted scope and
configuration hash, registry/plan paths and selected source hashes in addition to
owner intent and session records. It repeats this audit after cleanup. Pending
ownership remains `PENDING_OR_UNKNOWN_NO_RESTART`; no graceful terminal is fabricated.
The strict profile, outer network namespace, RPC allowlist and post-cleanup error
retention remain unchanged. No model turn/provider request is available.

Two predeclared **direct constructor** admission probes follow each cleanup:

1. Fresh records and a larger CPU total are denied because their configuration is
   absent from the bound plan.
2. The unchanged permitted configuration is denied because its owner already exists.

Both have empty stdout and create no replacement session. These are deliberate
admission-rejection probes, not study/model retries. No second installed client is
launched, and client reconnection/restart behavior is not established.

## Evidence

Final source passes **74 focused checks** across two invocations: 69 installed-
client/profile/CPU/ledger/owner/retention checks, then five plan-audit drift checks
without client launch. The latter reject changed raw bytes, recomputed plan digests,
changed membership/source and an incorrect planned-configuration hash after owner
reservation. These checks do not reannotate or rescore any study output.

Five separate pre-bound retained observations pass on CLI **0.159.2**. Private raw
root: `/tmp/crane-planned-owner-client-20260930-uh8nl_s3`. Plan, raw framing, logs,
configurations, execution plans, registry/owner/session/CPU records, denied constructor
artifacts and summary are hash-bound in
`manifests/operations/evidence-calibration-installed-client-planned-owner-v7.json`.
Raw framing stays private because it may contain host instructions/paths.

| Assigned inventory | Literal CPU | Failed CPU | Remaining threshold | Total CPU | Overshoot |
| --- | ---: | ---: | ---: | ---: | ---: |
| B2 | 31.336 ms | 294.391 ms | 278.664 ms | 325.727 ms | 15.727 ms |
| B3 | 37.305 ms | 299.423 ms | 272.695 ms | 336.728 ms | 26.728 ms |
| B4 | 34.958 ms | 313.250 ms | 275.042 ms | 348.208 ms | 38.208 ms |

The synthetic total is 310 ms with 300 ms per-call threshold. Exact assigned tool
definitions and Unicode/literal outputs pass; failed work remains charged, later
computation denied with null output, and full reads available. B0/B1 have zero tools;
B2/B3/B4 have identical definitions. All **six** retained services are absent.
All five client stderr captures and turn/item notification counts are zero.

All five app-server groups require recorded SIGTERM cleanup; all owner intents remain
pending with unchanged hashes. All **ten** constructor admission probes are denied.
Keep variable overshoot. These inventory assignments are infrastructure observations,
not scientific method effects or independent experimental episodes.

## Open scientific and execution boundaries

This verifies direct assigned-server RPC through the installed client and membership
in a supplied development plan. It does not authorize that plan scientifically or
establish a governed global schedule. Alternative plans/campaigns, operator bypass,
mutable source/storage, full dependency/runtime binding, distributed/power-loss
durability and complete model-turn accounting remain open. Full provider/model-facing
tools, alternative routes, rendering/truncation and exact capacity remain unverified.
No hard CPU cap or worst-case overshoot bound is claimed.

No semantic output, automated annotation, method-key join, real-pilot score, physical
acquisition, alpha spending or P11 freeze occurs. Preserve failed combined support,
unlaunched C and unanswered measurement reopening. P11 retains nineteen open conditions
and confirmation/replication independent N=0. Prospective five-method reporting,
episode clustering, corrected p-values and inconclusive/unfavorable results remain
required. Scientific population, sample size, endpoint and budgets remain unfrozen.
