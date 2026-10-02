# Sampled CPU broker and MCP candidate — 2026-09-30

## Separate integration

[Broker v5](../analysis/evidence_calibration_tool_broker_v5.py) selects service executor
v10 and requires explicit local/tree/scratch limits plus a typed CPU threshold,
polling interval and query timeout. All four limit groups bind into each tool intent;
computation passes them unchanged to the nested execution transaction. Original
brokers/executors remain preserved. Full reads retain explicit Unicode offsets and
are not capped by the computation-output limit or CPU threshold.

[MCP stdio v4](../analysis/evidence_calibration_mcp_stdio_v4.py) selects broker v5.
Its strict coordinator config requires `cpu_budget`; session intents bind it with
the other limits. Session/terminal schemas become v4-development and broker request
schema becomes v5-development. MCP protocol remains 2025-06-18. Exact B0/B1 empty
inventories and B2/B3/B4 identical read/computation definitions remain unchanged.
Per-call CPU thresholds are not cumulative across a model turn.

Successful tool replies retain only the existing result/status envelope. Interrupted
computations return `isError`, technical failure and null result. Full operator audit,
partial bytes, CPU counter samples and observed overshoot remain in nested records;
they are not supplied as substitute evidence to the method. The future coordinator
can inspect retained accounting without adding information to the method-visible
reply. Repeated event/call identities and adopted session namespaces remain forbidden.

## Actual evidence and tests

Forty-four focused checks pass across two invocations: thirteen broker checks and
thirty-one MCP checks. They cover exact inventories, full reads, literals, nested
limit bindings, mandatory CPU configuration, CPU cutoff/null result, prior overflow/
OOM failures, one-shot identities, framing/budgets/strict JSON, namespace failure,
program-error disposition, retention failure and staged B2 primitive parity.

Five separately retained fixed stdio subprocess exchanges pass in
`output/infrastructure/cpu-mcp-development-v1/`. Pre-call plan/client/config/request
identities and all raw transactions bind into the development manifest. B0/B1 deny
the fixed computation request and execute zero tools. B2/B3/B4 each perform exactly
three calls: full 4096-character Unicode read, literal computation and a fixed
four-descendant CPU workload. Literal percent/dollar/Unicode text remains exact.
CPU workloads return only null `CUMULATIVE_CPU_LIMIT` technical errors; partial
payload output does not appear on the wire. All subprocesses exit normally on stdin
EOF and emit only JSON-RPC stdout with no stderr.

The three equipped assignments use the same synthetic 0.300-second CPU threshold,
20 ms requested poll and 250 ms query timeout. Their observed cutoff records are:

| Assigned inventory | Final service CPU | Observed overshoot |
| --- | ---: | ---: |
| B2 | 0.367638 s | 67.638 ms |
| B3 | 0.320257 s | 20.257 ms |
| B4 | 0.358609 s | 58.609 ms |

These are fixed infrastructure observations, not semantic method outputs, episode
comparisons or statistical samples. Differences in scheduling/termination do not
establish a scientific method effect. Exact literal successes retain final accounting
and verified namespace exit. The three CPU interruptions retain null results and
incomplete/terminated lifecycle. All six computation services are absent after
cleanup, verified again after the fixed client completes.

## Remaining gates

This route has not yet been observed through the installed Codex client. Existing
installed-client observers and study callers do not migrate. Full provider/model-
facing tool exposure, alternative-route exclusion, lossless model-visible rendering,
exact tokenizer/capacity and complete kernel/provider confinement remain open.

The CPU guard is a sampled threshold stop with observed overshoot, not a hard cap or
worst-case bound. Whole-turn CPU aggregation, a prospectively bound overshoot policy,
query-failure disposition/admission, read/tool/output/reasoning budgets, operator-
crash durability and immutable runtime adoption remain open. CPU controls account
the computation service tree; host control/monitor and provider costs are outside
that counter. Synthetic limits are not frozen study budgets. Preserve all executor
v8 startup failures and v9/v10 observations and larger overshoots.

No semantic model/automated annotation call, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched C and unanswered reopening remain preserved. P11 keeps nineteen open
conditions, no hash mismatches and confirmation/replication N=0. B2/B4 remains the
primary scientific comparison; required B0/B1/B3 versus B4 reporting retains episode
effects, intervals and three-contrast Holm p-values, including inconclusive results.
