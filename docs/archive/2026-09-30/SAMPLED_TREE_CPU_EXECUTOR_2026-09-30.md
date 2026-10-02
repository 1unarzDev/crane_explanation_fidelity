# Sampled cumulative CPU execution candidate — 2026-09-30

## Candidate and retained startup defect

The [separate executor v8](../analysis/evidence_calibration_local_tool_sandbox_v8.py)
extends preserved v7 with explicit cumulative CPU threshold, polling interval and
query timeout. It retains namespace/lifecycle verification, scratch/memory/task/rate
constraints, per-process limits, bounded output capture and exclusive intent/terminal
records. CPU is total service-tree CPU, including wrapper/startup and descendants;
the privileged monitor/control processes are outside that target service tree.

Each query is recorded with monotonic start/end times and raw service properties in
an exclusive, fsynced sample file before interpretation. Missing or regressing
counters cannot become successful output. Successful service state is retained with
`RemainAfterExit=yes` until final CPU is saved, then released. Threshold and other
resource interruptions kill the exact service tree before its final counter is
queried and failed state reset. Partial payload bytes stay audit-only.

V8's first two fixed transactions stop on a startup expectation error: a loaded
transient service can briefly be `inactive/dead` with ExecMainCode=0, Result=success
and an unset CPU counter before the command starts. Both v8 null technical failures,
raw samples, missing namespace-status records and cleanup stay preserved in
`output/infrastructure/sampled-cpu-executor-development-v1/`. They are operator
accounting failures, not semantic model failures. No failed transaction is retried.

The [separate v9](../analysis/evidence_calibration_local_tool_sandbox_v9.py) recognizes
only that unobserved startup form as pending, alongside an initially absent unit.
It never assigns zero CPU to either form. Once a numeric counter is observed,
missing/regressing counters fail closed. A successful result requires final accounting.
The source repair and version changes are mechanically checked against unchanged v8.

## Quiescent final counter and actual evidence

V9's twenty-one focused checks pass, including exact literals, detached-descendant
cutoff, overflow, OOM, wall cutoff, invalid UTF-8, program error, incomplete namespace
setup, CPU limit validation and invalid/lost counter rejection. Two separate retained
fixed v9 transactions return the exact literal and a null CPU-threshold failure.
The descendant transaction records 0.366374 service CPU seconds against a 0.300-second
threshold, with 66.374 ms observed overshoot.

Review identifies a remaining final-counter defect: terminal main-process state alone
is insufficient to establish that all CPU-consuming descendants have stopped. The
[separate v10](../analysis/evidence_calibration_local_tool_sandbox_v10.py) adds a
quiescence guard: accept either an explicit zero task counter or the retired-cgroup
form with empty ControlGroup and unset TasksCurrent. Unknown/nonzero task counts do
not license a final CPU total. V9 and its observations remain unchanged. This repair
changes only final-counter acceptance and versioned schemas.

Fifteen v10 checks pass across two invocations. They include nine final-state/task
combinations, actual literal success, detached-descendant cutoff, program error,
exact repair boundaries, a staged B2 diagnostic primitive matching its deterministic
reference, and injected missing live counter producing null technical failure.
This staged workload is development regression evidence; it generates no explanation
or endpoint score and adds no independent experimental sample.

Two additional retained v10 transactions pass their fixed mechanical expectations:

| Fixed transaction | Disposition | Final service CPU | Overshoot |
| --- | --- | ---: | ---: |
| Unicode/literal output, 1 s threshold | Exact returned result | 0.032443 s | 0 |
| Four detached CPU-bound children, 0.300 s threshold | Null `CUMULATIVE_CPU_LIMIT` | 0.310511 s | 10.511 ms |

All six retained services across v8/v9/v10 are absent after cleanup. Intents, clients,
pre-call plans, namespace requests/statuses, CPU samples, terminals and summaries
are hash-bound in the development manifest. Both v8 failures remain visible. No
payload result from an interrupted computation is promoted to evidence.

## Scope and next integration

This is a **sampled threshold stop**, not a kernel hard cumulative CPU cap. Observed
overshoot is retained rather than hidden or used to select a favorable budget.
Requested 20 ms polls are not a guaranteed 20 ms sampling bound: query, filesystem,
scheduler and termination delays matter. The recorded maximum sample spacing also
includes final queries after termination; the v10 retained cutoff has 772.365755 ms
maximum spacing. That value is not represented as a demonstrated upper bound on CPU
overshoot. No worst-case cutoff/overshoot bound is established by these finite probes.
The independent wall/per-process/rate limits still apply.

Whole-turn aggregation, provider/reasoning/token costs, operator-crash durability,
immutable runtime and complete kernel/provider confinement remain open. Query
transport failures can leave final CPU unknown; such computations return no result.
A future coordinator must reject unknown accounting, preserve consumed CPU, bind a
prospective overshoot policy and enforce fair B2/B3/B4 budgets. Synthetic constants
are probe parameters, not frozen scientific budgets.

Existing brokers, MCP adapters, installed-client observers and study callers have
not adopted v10. No semantic method output, automated annotation, method-key join,
real-pilot score, physical acquisition, alpha spending or P11 freeze occurs. Failed
combined support, unlaunched C and unanswered measurement reopening stay preserved.
P11 retains nineteen open conditions, no hash mismatches and confirmation/replication
independent N=0. All prospective B0/B1/B3 versus B4 comparisons remain required,
including episode effects, intervals and corrected p-values for inconclusive results.
