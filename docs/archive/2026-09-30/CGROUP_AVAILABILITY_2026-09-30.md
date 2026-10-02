# Process-tree resource-control availability — 2026-09-30

## Actual offline observation

The preserved local sandbox v2 limits CPU and address space per process, wall time
and captured output. Aggregate process-tree resources remain a separate open gate.
An exploratory operator command first observed that the current user systemd
manager accepts a transient service with resource properties; it ran only a fixed
Python cgroup-path inspection. That preliminary command has no one-shot repository
transaction and is not counted as a governed harness result.

A separate one-shot [observer](../analysis/observe_evidence_calibration_cgroup_limits.py)
records its exact command/code hash and fresh service identity before launch. The
fixed synthetic probe reads its own kernel cgroup settings and creates bounded
sleeping children until the requested task limit prevents another process.
Its immutable intent/terminal stay in ignored local output:
`output/infrastructure/cgroup-availability-development-v1/`.

Observed settings: `memory.max=67108864`, `memory.swap.max=0`, `pids.max=8`, and
`cpu.max=100000 100000`. Seven children started; the next creation was blocked.
All children were killed/reaped and the collected transient unit was absent after
completion. Eleven synthetic validator/record tests pass. No evidence file, retained
method response, evaluator key, provider/authentication or annotation packet was read.

## Scope and remaining integration

This establishes current user-service availability and task-limit enforcement for
one fixed operator probe. CPUQuota bounds CPU rate, not cumulative CPU time. The
memory setting is observed; no allocation-pressure/OOM test occurred. Ancestor
limits, process-tree CPU accounting, scratch capacity, failure classification,
namespace/service integration, restored-runtime binding and durable model execution
remain open. The transient service runs a fixed host Python probe; it is not a
replacement for the registered bubblewrap computation path or provider harness.
The observed constants are development probe limits, not selected study budgets.

Existing sandbox/broker callers are unchanged. This result authorizes zero model
or automated-annotation calls, no real-pilot scoring, no fresh physical allocation,
no alpha spending and no P11 freeze. Failed combined support/unlaunched C and pending
measurement reopening are preserved. Confirmation/replication independent N stay zero.
