# Installed-client scratch/lifecycle MCP observation — 2026-09-30

## Candidate and boundaries

The [separate observer v3](../analysis/observe_evidence_calibration_app_server_mcp_v3.py)
selects MCP stdio v3, broker v4 and service executor v7. Prior versions, recorded
failures and study callers remain preserved. Coordinator configs explicitly bind
local, process-tree and scratch limits: two seconds wall time, one second CPU per
process, 256 MiB address space per process, 1024 combined output bytes, 64 MiB tree
memory, sixteen tasks, one-core CPU rate, and 1 MiB each for temporary/shared memory.
These are synthetic observation limits, not prospectively frozen study budgets.

The outer inspector disables networking, supplies private devices, uses strict
configuration and forwards only the two service-control variables documented in
the [previous installed-client record](INSTALLED_CLIENT_SERVICE_MCP_2026-09-30.md).
It exposes the host filesystem and does not establish full method confinement.
The RPC allowlist permits initialization, ephemeral thread start, assigned-server
inventory and direct MCP calls. No model turn, resume, steering or generic execution
RPC is permitted. Selecting a model in thread metadata launches no model turn.
An intent binds command, configuration and source before launch; existing sessions
are never adopted or retried. Raw client framing remains private under `/tmp`.

## Observed results

Codex CLI 0.159.2 discovers and routes all five assigned inventories. B0/B1 expose
zero tools. B2/B3/B4 expose identical full-read/computation definitions. Each equipped
method returns exact synthetic Unicode file text and literal `%n ${HOME} $$ αβ`
output. Its separate overflow call returns `isError`, technical failure and null
result without partial audit bytes.

The observer also inspects both nested computation transactions. Each intent and
terminal binds the same local/tree/scratch limits as its coordinator; namespace
status hashes match retained bytes; all six services have `not-found` cleanup.
The three literal successes have verified payload exit and exact output. The three
overflows retain `OUTPUT_LIMIT` and incomplete lifecycle after termination; they
are not represented as successful payload completion or semantic failures.

Twenty-two focused tests pass across two invocations: fourteen installed-client/
profile/network/allowlist/launch-retention checks, plus eight nested-record rejection
checks covering missing terminals, bad status hashes, cleanup, scratch mismatch,
incomplete success lifecycle, altered text and non-null overflow results. Five
additional fresh observations are separately retained and hash-bound in the
[development manifest](../manifests/operations/evidence-calibration-installed-client-lifecycle-mcp-v3.json).
All emit zero client stderr bytes and zero turn/item notifications. The dedicated
app-server groups require recorded SIGTERM cleanup after RPC completion. An overall
MCP-session terminal may be absent; no graceful session terminal is fabricated.

## Current gates

Assigned-server discovery and direct routing do not establish the complete provider
request tool set, alternative-route exclusion, model-visible rendering or default
truncation. Exact-route tokenizer/capacity, cumulative CPU and total turn/read/tool/
output/reasoning budgets, immutable runtime/storage/distribution, complete kernel/
provider confinement and durable one-shot model execution remain open. Existing
study callers have not adopted this candidate.

Recomputed readiness retains nineteen open conditions and no hash mismatches.
Confirmation and replication independent N remain zero. Error-budget audit remains
provisional/unbound: 0.02 consumed, at most 0.01 discovery, 0.02 replication-only.
Freshness audit reconciles 120 former confirmation and twenty replication layouts
already materialized; the other 100 allocated replication layouts stay quarantined.
Numeric traceability passes 220 assertions; the manuscript builds as nine pages.
Mechanical manuscript readiness does not establish scientific submission readiness.

No semantic method output, automated annotation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched adjudication C and unanswered measurement reopening remain preserved.
B2/B4 remains primary; B0/B1/B3 versus B4 retain the prospective episode-level effects,
intervals and three-contrast Holm reporting, including inconclusive results. Secondary
correction grants no additional alpha or confirmatory status.
