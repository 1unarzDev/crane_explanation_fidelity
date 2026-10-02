# Installed-client response egress — 2026-09-30

## Preserved auditor failure and repair

Observer v8 selected coordinator v4/writer v2, but reconstructed original response
bytes by encoding the retained RPC object. RPC storage sorts object keys while wire
encoding preserves insertion order. The initial suite had **68 passes and 6 failures**:
five installed-method observations and one cleanup-injection check failed on
`generated response hash mismatch`. Their temporary raw directories were deleted;
they are not claimed as retained client failure artifacts. This is an auditor failure,
not a model failure. Preserve v8 source/tests and a separately retained read-only replay
on unchanged prior infrastructure records in
`output/infrastructure/egress-audit-failure-v8/`. That replay launches no client or model.

Writer v3 retains exact framed bytes after reservation intent and before any transport
write or budget denial, using exclusive binary storage, a complete-count check, flush
and fsync. Storage failure leaves pending ownership and sends nothing. Coordinator v5
selects this writer; prior versions remain preserved. Observer v9 checks retained bytes
against both the original RPC response hash and egress reservation/settlement records.
It separately checks typed canonical RPC content, without assuming JSON key order.
Wire reads reject symlinks/nonregular files and are bounded by the configured budget.
Missing, extra, pending, withheld, mistyped or mismatched records fail closed.

The corrected sources passed **140 distinct focused checks** across two invocations:
122 initial checks, then 18 added checks for partial exact-wire storage and egress
corruption. The latter do not launch clients. Old defect evidence remains unchanged.

## Retained offline observations

Five fresh pre-bound observations pass on **codex-cli 0.159.3**. The earlier 0.159.2
observations remain historical records. Private raw root:
`/tmp/crane-egress-client-v9-20260930-y78j5vv9`. Its pre-call plan binds selected
sources, CLI version, B0–B4 assignments and two direct constructor probes per method;
model calls and retries are disabled. Exact configuration membership is separately
bound before each launch. Raw framing stays private; hashes and sanitized summaries
are retained in the operation manifest.

| Assigned inventory | Retained responses | Local flushed bytes | Total service CPU | Overshoot above 310 ms |
| --- | ---: | ---: | ---: | ---: |
| B0 | 2 | 229 | — | — |
| B1 | 2 | 229 | — | — |
| B2 | 7 | 3,058 | 395.458 ms | 85.458 ms |
| B3 | 7 | 3,058 | 333.840 ms | 23.840 ms |
| B4 | 7 | 3,058 | 366.522 ms | 56.522 ms |

Exact tool inventories, Unicode/literal outputs, failed-computation CPU charges and
denied later computations with preserved full reads pass. All six retained computation
services have `LoadState=not-found`. All stderr captures and turn/item notification
counts are zero. All five groups require recorded SIGTERM cleanup; owner intents remain
`PENDING_OR_UNKNOWN_NO_RESTART`. No graceful owner terminal is fabricated. Ten direct
constructor probes are denied before session creation: changed configurations fail
plan membership, unchanged configurations fail retained ownership. No second installed
client is launched for a condition, and no study request is retried.

## Scope and remaining gates

The audit verifies a complete **retained response prefix**, before and after cleanup;
it explicitly does not verify whole-session completion. Local written/flushed bytes,
assigned-client RPC results, peer receipt and model-visible rendering are distinct.
Peer receipt, provider/model tool inventory, rendering/truncation and exact capacity
remain unverified. These synthetic inventory assignments are infrastructure checks,
not comparative method effects or independent physical episodes. CPU sampling is not
a hard cap; preserve measured overshoots without a worst-case bound claim.

Existing study callers do not migrate. Scientific plan authorization, alternate-route
exclusion, complete model-turn ownership/costs, immutable runtime/storage and durable
distributed execution remain open. No semantic output, automated annotation, pilot
score, method-key join, physical acquisition, alpha spending or P11 freeze occurs.
The newer failed combined-support canary and unanswered measurement-reopening proposal
remain controlling despite the earlier Astra-high qualification.

P11 retains **19 open conditions**, zero component hash mismatches, and confirmation/
replication independent N=0. Freshness remains 120 former confirmation and 20 replication
layouts materialized; the other 100 allocated replication layouts remain quarantined.
Alpha remains 0.02 consumed, at most 0.01 discovery and 0.02 replication-only. B2/B4
is primary; prospective B0/B1/B3 versus B4 must report episode effects, intervals,
exact and three-contrast Holm-corrected p-values, including unfavorable/inconclusive
results. Correction creates no alpha allocation. The nine-page manuscript passes
packaging and 220 numeric assertions; scientific submission readiness remains open.
