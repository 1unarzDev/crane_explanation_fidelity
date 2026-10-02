# Bounded local execution candidate — 2026-09-30

This prospective development version closes the original subprocess capture gap for local Python
computation. The original sandbox/broker and their hash-bound records remain unchanged. Select
`analysis/evidence_calibration_local_tool_sandbox_v2.py` and
`analysis/evidence_calibration_tool_broker_v2.py` explicitly; no existing caller switches versions.
This candidate authorizes zero provider, annotation or study calls.

## Enforced local limits

The caller supplies every `Limits` field without defaults: wall seconds, CPU seconds per process,
address-space bytes per process and combined stdout/stderr capture bytes. The accepted safety
ranges are 1–60 seconds, 1–60 CPU seconds, 64 MiB–8 GiB address space and 1 byte–16 MiB output.
These ranges are implementation constraints, not selected scientific budgets. B2/B3/B4 must receive
fair, prospectively bound budgets before execution; B0/B1 still have no tool access.

`prlimit` executes inside the unchanged bubblewrap namespace before isolated stdlib Python,
setting equal soft/hard CPU and address-space limits and disabling core dumps. Limits are inherited
by descendants. Nonzero exits, including resource termination, retain their return code and captured
streams as tool runtime failures. This is not a reliable classifier of a hidden physical failure or
of which resource caused a nonzero exit.

The host drains both pipes with selectors and a shared byte budget. Capture stores at most that
budget and reads at most one extra byte to detect overflow. Overflow stops execution and raises
`OUTPUT_LIMIT`; elapsed wall time raises `WALL_TIME_LIMIT`. The launcher group is killed and reaped
on cleanup; bubblewrap's private PID namespace terminates its descendants. Output decoding is
strict UTF-8; invalid bytes become `INVALID_UTF8_OUTPUT`, rather than lossy successful text.

The v2 broker records limits in its immutable intent before dispatch. Bounded-execution failures
retain a terminal `TECHNICAL_FAILURE`, null successful result, reason, captured-byte count,
observed-byte lower bound and base64 partial stdout/stderr. Partial bytes are audit material only.
They are never returned as a successful truncated tool result. The existing no-replay/unknown-intent
rules remain. A distinct permitted tool call is not a replacement of the failed event.

Registered-file reads remain lossless, including complete reads and explicit reconstructible
Unicode ranges. They are outside the subprocess capture limit; no evidence is silently removed.
Full read/tool-result token capacity must still be established for the actual provider route.

## Scope and remaining gates

Address-space/CPU limits apply separately to each process; they do not bound aggregate process-tree
memory/CPU, process count, scratch storage, host file-read memory or total tool output over calls.
This is not complete resource containment. The exposed `/usr` runtime is not fully hash-bound.
Provider/MCP integration, actual tool-schema enumeration, alternative-route exclusion, exact
model/tokenizer capacity, complete turn/reasoning/output budgets, durable top-level execution and
study budget selection remain open. No provider-harness confinement claim follows from these tests.

Fifteen focused synthetic checks cover exact Unicode and byte-boundary output, both-pipe floods,
detached descendants under timeout and normal namespace exit, actual CPU/address-space enforcement,
invalid UTF-8, invalid budgets, immutable overflow retention/no replay, lossless larger file reads,
method parity and the original staged inventory tool. The synthetic budgets (including 128 MiB,
1 CPU second and 1 KiB capture in most cases) are not pilot or confirmatory parameters.

P11 retains nineteen open conditions and confirmation/replication independent N=0. The failed
combined support canary and unlaunched C remain retained. The measurement reopening proposal is
pending explicit user adoption. No method key, endpoint scoring, physical allocation or alpha is
opened by this local implementation. Whole-episode B2/B4 and Holm-corrected B0/B1/B3-versus-B4
comparisons, including inconclusive outcomes, remain required prospectively.
