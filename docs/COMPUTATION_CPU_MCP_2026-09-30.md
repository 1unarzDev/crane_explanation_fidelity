# Serial computation CPU ledger through MCP — 2026-09-30

## Candidate and scope

Preserve MCP v4. Separate `analysis/evidence_calibration_mcp_stdio_v5.py`
selects broker v7, ledger v2 and executor v10. The coordinator must supply an
explicit typed `computation_cpu_limit` in addition to the per-call CPU budget.
Session intent binds both; operator session terminal retains the ledger snapshot.
MCP protocol remains `2025-06-18`. Existing study callers do not migrate.

One server owns one fresh ledger across serial calls. This verifies service CPU
accounting across this session; it does not establish the eventual model-turn or
condition boundary. Fresh sibling servers are not authorized budget resets.
Host reads, monitor/control work and provider/model costs remain outside this
counter. The sampled termination threshold is not a hard cap or a worst-case
overshoot bound. Complete turn budgets and overshoot policy remain open.

Method-facing replies retain only status/result or null technical error. Partial
bytes, reservations, settlements and ledger counters stay operator-side. Known
computation exhaustion preserves full reads. Unknown accounting blocks reads and
computations and withholds otherwise successful execution. Settlement retention
failure leaves its reservation pending, prohibits settlement replay and closes
admission. Restart cannot adopt the existing record namespace.

## Verification

`python -m pytest -q tests/test_evidence_calibration_mcp_stdio_v5.py`:
**35 passed**. These include mandatory strict configuration, session binding,
actual shared-total charging, failed work, read preservation, operator-injected
audit uncertainty, settlement storage failure, non-adoption and existing framing,
inventory, literal, namespace and partial-output checks.

Ignored retained root:
`output/infrastructure/computation-cpu-mcp-v5/`. Its client and pre-call plan bind
five fixed subprocess stdio exchanges, one separate auditor fault injection and
synthetic budgets before execution. Raw input/output, configuration, execution,
CPU samples, reservations and session records are retained and hash-bound in
`manifests/operations/evidence-calibration-computation-cpu-mcp-v5-development.json`.

| Assigned inventory | First computation CPU | Failed computation CPU | Remaining threshold | Total CPU | Overshoot |
| --- | ---: | ---: | ---: | ---: | ---: |
| B2 | 34.628 ms | 295.781 ms | 275.372 ms | 330.409 ms | 20.409 ms |
| B3 | 35.343 ms | 301.439 ms | 274.657 ms | 336.782 ms | 26.782 ms |
| B4 | 32.688 ms | 370.569 ms | 277.312 ms | 403.257 ms | 93.257 ms |

Each uses a 310 ms synthetic session total and 300 ms per-call threshold. The
next computation is denied without a service launch; the exact 4096-character
Unicode read remains available. B0/B1 expose zero tools; B2/B3/B4 expose the
same exact assigned definitions. These inventory assignments are infrastructure
checks, not method outcomes or a comparative pilot. Retain variable overshoot.

The separate B2 injection supplies the auditor a copied terminal with final CPU
removed. Original successful executor bytes stay unchanged, success is withheld,
and later read/compute calls return null errors. This deliberately injected
uncertainty is not an observed model or method failure. All **seven** retained
services have `LoadState=not-found` after cleanup.

## Governance and next gate

Direct stdio verifies this adapter only. Installed-client routing for v5, full
model-facing tool inventory, lossless model-visible rendering, exact capacity,
immutable runtime/distribution and durable one-shot model execution remain open.
No semantic model call, automated annotation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs here.

Readiness recomputation retains **19 open conditions**, zero hash mismatches and
confirmation/replication independent N=0. Alpha stays 0.02 consumed, at most 0.01
discovery, 0.02 replication-only. Freshness remains 120 former confirmation plus
20 replication layouts materialized and 100 allocated replication layouts
quarantined. The newer combined-support canary failure and unanswered measurement
reopening remain controlling; older qualification does not reopen annotation.

The existing prospective five-method plan retains B2/B4 primary and B0/B1/B3
versus B4 secondary: episode effects, intervals, exact p-values, Holm across three
secondary contrasts and inconclusive/unfavorable outcomes. Correction creates no
alpha. The nine-page manuscript passes numeric traceability and full mechanical
submission checks; the scientific result remains unfrozen.
