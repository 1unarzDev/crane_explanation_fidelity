# Local MCP stdio adapter candidate — 2026-09-30

`analysis/evidence_calibration_mcp_stdio.py` connects the existing bounded v2 tool broker to a
local newline-delimited JSON-RPC stdio surface. It implements a limited MCP tools server, with no
provider client, model invocation, authentication change or study activation. Existing callers
and frozen components are unchanged.

## Protocol and tool boundary

The implementation follows the official MCP **2025-06-18**
[stdio transport](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports),
[lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle) and
[tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) specifications.
It negotiates that single supported version, advertises only the tools capability, waits for
`notifications/initialized`, and supports `ping`, `tools/list` and `tools/call`. It issues no
server-to-client requests. Resources, prompts, sampling and other execution routes are absent.
No general MCP conformance or live-client compatibility certification is claimed.

The exact wire-advertised schemas come from the unchanged broker definitions: B0/B1 list no tools;
B2/B3/B4 list identical registered-file-read and isolated-Python tools. The coordinator binds the
method through the hash-checked workspace identity. A client cannot select or change its method.
Normal results include matching serialized text and structured content. Runtime/technical failures
set `isError=true`; bounded partial subprocess bytes remain in the local audit and are not supplied
as substitute evidence. Full registered-file reads and explicit reconstructible slices remain
available, preserving B2 source/configuration and primitive-computation access.

## Retention and framing

A fresh records namespace binds protocol, method/workspace hash, exact advertised tools and all
explicit local limits before serving. Each received frame has an immutable byte/hash intent and
terminal response/hash record, including notifications and protocol errors. Each dispatched tool
also has the existing broker intent/terminal boundary. No result is sent before its terminal record
is written. Storage failure stops the service and preserves any unknown intent without replay.

A repeated tool-call ID cannot execute again within the session. Distinct calculations under new
IDs remain allowed by the bound budget. A new server cannot adopt an existing records directory.
Unknown or interrupted intents remain quarantined; this adapter adds no automatic restart policy.
A future provider client must separately enforce no replay/retry and durable top-level execution.

JSON parsing rejects duplicate keys, nonfinite numbers (including overflow), invalid UTF-8 and
escaped lone surrogates; batches, null/Boolean IDs and nonrequest messages are rejected. Explicit
message count and request byte limits bound control traffic. Stdio reads at most the frame budget
plus one detection byte. Oversize or unterminated frames stop the session without processing later
input. Output contains only JSON-RPC messages; framing/message-budget termination exits with code
65. EOF closes the local session, and does not establish successful model execution.

## Invocation and remaining execution gates

The CLI requires `--configuration` pointing to a coordinator-owned JSON object with exactly:
`workspace`, `identity`, `records`, `limits`, `max_calls`, `max_messages`, `max_request_bytes`.
The identity must match the staged inventory. Limits have the v2 sandbox's four explicit fields.
The coordinator file and event records must stay outside model-visible workspaces. This is an
interface for later integration; no study configuration or prospective scientific budget is chosen.

Twenty-six focused deterministic tests inspect exact wire tools for all five methods and exercise
actual subprocess stdio initialization/list/call/EOF for each method, baseline denial, isolated
computation, lossless reads, runtime/overflow errors, repeated IDs, malformed JSON, absent routes,
framing/message/tool limits, unknown-intent preservation and simulated retention failure.
Synthetic calls invoke local Python only. These counts add no independent experimental episodes.

The adapter is sequential and does not implement in-flight cancellation or an idle timeout.
It does not bound complete transport output tokens, file-read memory, aggregate process resources
or scratch storage. The host `/usr` runtime remains incompletely bound. Provider integration,
actual provider request tool enumeration, disabling all alternative host/connector/web/file routes,
exact-route model/tokenizer capacity and complete turn/output/reasoning budgets remain open.
The offline adapter's schemas are not proof of the tools a live model receives or of harness
confinement. No model-backed development output follows from these checks.

The failed combined support canary, unlaunched C and pending measurement reopening decision remain
unchanged. No pilot annotation, method-key join, endpoint estimate, alpha binding or physical
allocation occurs. P11 remains closed with nineteen open conditions and confirmation/replication
independent N=0; primary B2/B4 and corrected B0/B1/B3-versus-B4 comparisons still require valid
whole-episode evidence, including inconclusive and unfavorable results.
