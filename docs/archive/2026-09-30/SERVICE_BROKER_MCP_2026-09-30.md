# Service-backed broker and MCP candidate — 2026-09-30

## Integration with preserved interfaces

A separate [broker v3](../analysis/evidence_calibration_tool_broker_v3.py) selects
only the service executor v4, requiring explicit TreeLimits alongside existing
local limits and call budget. Tool definitions, role permissions, exact staged
file reads, character offsets and read hashes are preserved. B0/B1 have no tools;
B2/B3/B4 share the same primitive read/computation definitions. Full reads are not
silently capped by the computation output-byte budget.

Each computation has the original broker-level intent/terminal plus a distinct
nested executor transaction under the same event identity. Requests bind both
limit objects. Technical failures retain matching records at both levels and no
successful partial result. Ordinary nonzero program exits remain runtime failures.
Existing event IDs, intents and unknown states cannot be replayed. No previous
broker or executor version is edited or silently adopted by a study caller.

A separate [MCP stdio v2](../analysis/evidence_calibration_mcp_stdio_v2.py) exposes
the same MCP 2025-06-18 tools-only protocol through this broker. Coordinator config
now requires exact tree-limit fields; the session descriptor binds them. It retains
request/response bytes and hashes as before. Technical failure replies are marked
`isError` with a null result, without passing bounded partial audit bytes back as
robot-visible evidence. Existing provider/CLI inspectors remain unchanged.

## Observed checks

62 focused tests pass: ten broker checks, 26 new-adapter checks and 26 preserved
adapter checks. They exercise actual service computation and stdio subprocesses,
all five method tool inventories, full Unicode reads beyond the compute byte cap,
exact dollar/percent/Unicode code, OOM/output failure disposition, no replay, wire
framing/strict JSON and retention failure. The staged B2 inventory computation on
an existing development fixture still matches its deterministic reference. It does
not generate a natural-language explanation or score a retained answer.

A separate fixed operator client records a pre-call plan, exact configurations,
wire hashes, client transactions and all server/broker/executor records in ignored
`output/infrastructure/service-mcp-development-v1/`. Actual stdio exchanges pass for
all five methods. B0/B1 deny computation and execute zero tools. B2/B3/B4 each read
4096 Unicode characters losslessly, preserve literal computation output and retain
an output-overflow technical failure with no partial bytes on the wire. Their three
tool inventories have the same canonical hash. Every computation service is absent
after cleanup. The three calls per equipped method are not independent episodes.

## Scope and remaining gates

This is an actual local stdio observation, not full model-facing request enumeration,
lossless provider rendering or certification that alternative tools are excluded.
No Codex turn, provider request, model/annotation output or remote study call occurs.
Only these separate candidate entry points select service execution; existing study
callers, runtime selection, prompts and contracts remain unchanged.

Read-tool host memory and total turn output/token capacity remain unbounded by this
candidate; it preserves full relevant evidence rather than choosing a silent limit.
Cumulative CPU, scratch storage, complete model/turn budgets, immutable restored
runtime adoption, full kernel/provider harness, valid automated measurement and
fresh aligned B0–B4 outputs remain open. Synthetic limits are not study budgets.

No method-key join, retained response score, physical acquisition, alpha spending or
P11 freeze occurs. Failed combined support/unlaunched C and pending measurement
reopening remain preserved. P11 retains nineteen open conditions and zero
confirmation/replication independent N. All prospective B0/B1/B3 versus B4 effects,
intervals and corrected p-values remain required, including inconclusive results.
