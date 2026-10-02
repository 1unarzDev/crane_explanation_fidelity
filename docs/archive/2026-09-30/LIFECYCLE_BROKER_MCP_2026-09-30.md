# Scratch/lifecycle broker and MCP candidate — 2026-09-30

## Separate integration

[Broker v4](../analysis/evidence_calibration_tool_broker_v4.py) selects executor v7
with explicit local, process-tree and scratch limits. It preserves the exact tool
definitions and full staged-file reads of prior versions. B0/B1 have no tools;
B2/B3/B4 share the same read/computation surface. Computation intents bind all
three limit objects and retain nested namespace requests/status and executor
terminals. No previous version or study caller is silently migrated.

[MCP stdio v3](../analysis/evidence_calibration_mcp_stdio_v3.py) requires scratch
limits in its exact coordinator configuration and session descriptor. It preserves
the existing strict tools-only protocol, request/response retention and call-ID
replay prevention. A namespace lifecycle failure returns `isError`, technical
failure and a null result; partial output/status audit bytes are not substitute
robot-visible evidence. A verified nonzero program exit remains a runtime failure.

## Actual verification

40 focused checks pass across two invocations: eleven new broker checks and 29
new-adapter checks. They include real service computation/stdio processes, all five
method permissions, full Unicode reads beyond the computation byte cap, exact
literal code, local/tree/scratch binding, no replay, output/OOM failure, strict
wire framing and retention errors. Injected incomplete namespace status is withheld
on the wire; setup-looking program stderr still has its verified runtime disposition.
An existing staged B2 primitive continues to match its deterministic reference.

A separately recorded fixed client performs actual stdio exchanges for all five
methods. B0/B1 execute zero tools; B2/B3/B4 each receive exact full Unicode text,
literal computation output and a null-result output-overflow error. Their tool
inventory hashes are identical. All six computation service units are absent after
cleanup. A distinct in-process MCP dispatch probe (not an installed-client route)
injects a missing mount and verifies a null technical-failure reply with incomplete
lifecycle. That additional service is also absent. Exact clients, pre-call plans,
configs, wires and nested records remain local in ignored
`output/infrastructure/lifecycle-mcp-development-v1/`.

## Remaining scope and scientific boundary

Only these candidate entry points select the combined controls. Existing installed-
client inspectors and study callers remain unchanged; actual installed-client/model-
facing integration is not established by this stdio observation. Complete native/
alternative tool exclusion, lossless model-visible rendering, exact-route tokenizer/
capacity and durable provider/model execution remain open.

Synthetic scratch/resource parameters are not selected study budgets. Full read
memory, total turn output/tokens, cumulative CPU, metadata/inode and kernel-memory
mechanisms, immutable restored-runtime adoption and full harness binding remain
open. Namespace final status does not attest every intermediate interpreter/tool
startup stage or authorize semantic/model-failure attribution.

No semantic method output, automated annotation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Preserve failed combined
support, unlaunched C and the unanswered measurement-reopening decision. P11 retains
nineteen open conditions and zero confirmation/replication independent N. All five-
method prospective episode effects, intervals and corrected p-values remain required,
including inconclusive and unfavorable results.
