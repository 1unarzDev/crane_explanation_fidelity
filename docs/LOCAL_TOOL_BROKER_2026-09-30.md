# Offline local tool broker — 2026-09-30

`analysis/evidence_calibration_tool_broker.py` provides provider-neutral dispatch for two candidate
tools: exact staged-file reads and Python computation over visible records. It adds no provider
client, MCP transport, model call, execution declaration or automatic pilot activation.

## Access and parity

B0/B1 tool definitions are empty and tool attempts are denied. B2/B3/B4 share the same two tool
schemas. Their staged inventories govern file access: B2 receives no contract or evaluator files;
B3/B4 may read their public contract asset. The computation tool runs through the existing local
bubblewrap seam and retains its source/configuration and arithmetic capabilities. It has no host
execution fallback. This does not certify the complete system runtime or provider harness.

File reads accept only exact registered paths and verify content hashes. Unicode character offsets,
requested length, total size, returned range and EOF are explicit. A full read is permitted; an
explicit requested slice can be reconstructed without lossy summaries or silent truncation.
Computation returns the exact stdout/stderr and return code. Runtime errors remain tool outcomes;
there is no semantic verifier, answer repair or replacement response.

## Durable event boundary

The broker requires a fresh event namespace outside the workspace and explicit positive call and
1–60 second runtime limits. It reuses the existing exclusive-create/fsync helper for immutable
request intents and terminal records. The intent binds method/workspace identity, tool name and
arguments, ordinal and limits before dispatch. Denied requests, technical failures and timeouts
receive terminal failure records. Existing intent/result identities cannot be replayed, and existing
event directories cannot be adopted by a new broker. An interrupted intent stays unknown and
quarantined. Successful tool results are retained before they are returned to a caller.

This is local event retention, not complete top-level model-call retention or a recovery policy.
A model may deliberately request repeated calculations under distinct events within its bound
budget; such normal agent tool use does not create more independent episodes. Durable provider
intent/return handling remains separate. The broker is intended for sequential dispatch; concurrent
calls and concurrent external workspace mutation are not a validated execution mode.

## Remaining execution requirements

The broker currently uses in-memory subprocess stdout/stderr capture. No output-byte, aggregate
memory/CPU or total tool-result token limit is bound; it does not certify resource containment.
Future execution must bind those limits and fail explicitly on overflow while retaining the event,
without quietly presenting truncated evidence/output or restricting B2 to summaries.

An enforcing MCP/provider integration must advertise only the assigned method's tools, route every
call through this broker, disable alternative file/shell/web/connector access, inspect the actual
request tool schemas and audit events. The earlier CLI prompt inspection does not establish any
of these conditions. Actual-route tokenizer/capacity, full runtime and budgets, fair B2 access,
provider/model binding and immutable execution declarations remain open.

The twelve focused broker checks cover exact Unicode reads/chunks, method parity, unknown paths,
baseline denial, real isolated computation/outside-file exclusion, retained runtime errors,
unknown intents, budgets, the original staged inventory tool and timeout retention. Nine existing
namespace tests and two P11 readiness checks provide additional targeted verification. All test
calls are deterministic local infrastructure actions; none invokes a model or annotator.

The measurement reopening proposal remains pending. The failed combined support canary and
unlaunched C remain unchanged; no pilot labels, key join, effects, alpha spending, fresh physical
allocation or P11 authorization follow. Confirmation/replication independent N remain zero.
