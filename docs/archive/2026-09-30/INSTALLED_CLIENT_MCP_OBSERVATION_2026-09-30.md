# Offline installed-client MCP observation — 2026-09-30

The installed Codex CLI **0.159.2** can discover and call the local adapter through its app-server
without starting a model turn. This is a synthetic client-compatibility observation, not a study
request, semantic pilot, capacity certification or provider-harness confinement result.

## Authoritative interfaces and observation

Official OpenAI [app-server documentation](https://developers.openai.com/codex/app-server)
describes `mcpServerStatus/list`, `mcpServer/tool/call` and protocol-schema generation. The
[MCP configuration documentation](https://learn.chatgpt.com/docs/extend/mcp) describes command,
arguments, required startup and enabled-tool lists. Generated schemas from this exact CLI version
confirm thread-scoped inventory/call parameters and ephemeral thread initialization.

`analysis/observe_evidence_calibration_app_server_mcp.py` creates a fresh synthetic file/workspace,
starts a dedicated app-server inside a network namespace, initializes an ephemeral thread and uses
only the four allowlisted RPC methods: `initialize`, `thread/start`, `mcpServerStatus/list` and
`mcpServer/tool/call`. It also sends the `initialized` notification. No `turn/start`, steering,
resume, generic execution, provider authentication change or model invocation is permitted.
The model identifier remains `gpt-6-sol`; selecting a thread model is not invoking that model.

All five method observations return `runtimeStatus=connected` with the exact expected MCP schemas.
B0/B1 list no tools. B2/B3/B4 list identical `read_staged_file` and `compute_visible_python` schemas;
each returns exact synthetic Unicode file text and `42\n` for `print(6*7)`. All five corrected
observations have zero stderr bytes and no turn/item notifications. The private network namespace
also rejects access to a parent loopback listener in the regression test.

The process is stopped after its bounded observation; EOF alone can leave app-server loaded.
All five dedicated process groups require SIGTERM in these observations. This is deliberate local
cleanup, not a failed model request. RPC/tool intents and responses completed before cleanup;
forced process cleanup can leave the overall MCP-session terminal absent, which must not be
rewritten as a graceful terminal. No observation process remains live or is adopted/restarted.
Raw client framing stays under `/tmp` because it may contain host paths/instructions. The repository
retains sanitized schema/results and raw hashes only. Each run requires a fresh namespace and
never adopts an earlier session.

## Retained failed probe and causal correction

The first probe discovered the two schemas but retained an arithmetic `TECHNICAL_FAILURE`:
`PermissionError: [Errno 13] Permission denied: '/dev/null'`. A second assertion-bearing probe
reproduced it. Neither is a model failure and neither historical tool record is replaced.

The failure minimizes to bare Python opening `/dev/null` under the outer
`bwrap --unshare-net --bind / /` inspector. Adding a private `--dev /dev` makes that minimal check
and the original installed-client arithmetic call pass. The inner registered sandbox/broker needs
no repair. The outer inspector exposes the host filesystem and is only a network isolation seam;
it is not appropriate as a confined scientific explanation workspace.

Separately, the first profile emitted an ignored-setting warning for `features.remote_plugins`.
The installed feature catalogue uses singular `remote_plugin`. The final observer uses that exact
name plus `--strict-config`; old plural-spelling observations remain preserved. This prospectively
corrects the profile spelling, without retroactively certifying earlier prompt-inspection flags.
No user configuration file or authentication is edited.

## What remains open

The listing is the assigned MCP server's installed-client inventory. It does not enumerate the
complete model request tool set or certify absence of native, connector, skill or other routes.
Official MCP documentation also exposes per-tool `output_token_limit` and describes default output
truncation. Raw direct app-server tool results do not prove what the model-facing renderer retains.
Exact-route tokenizer/capacity, lossless model-visible tool output, full runtime, fair complete
budgets, alternative-route exclusion and durable top-level one-shot execution remain unbound.

The observer's synthetic limits are test parameters, not scientific budgets. Its twelve tests
cover the minimized device regression, parent network denial, forbidden RPC methods, corrected
flag spelling and actual installed-client discovery/routing for B0–B4. These local invocations add
no independent experimental episodes and qualify no automated annotator.

The combined support canary failure and unlaunched C remain unchanged. The measurement reopening
proposal still awaits explicit adoption. No pilot label, method-key join, endpoint effect, physical
allocation or alpha expenditure occurs. P11 retains nineteen open conditions, with confirmation
and replication independent N=0. Valid whole-episode comparative evidence remains required.
