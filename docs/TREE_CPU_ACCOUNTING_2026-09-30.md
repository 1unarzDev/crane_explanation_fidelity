# Exited-descendant CPU accounting — 2026-09-30

## Purpose and preserved observations

The current service executor caps process-tree CPU rate and CPU per process. Neither
is a cumulative CPU cutoff across a whole tool tree or model turn. This fixed offline
probe tests the accounting prerequisite without adopting a new executor or study
budget. It runs three children with 0.15 CPU seconds of work each and 0.10 CPU seconds
of parent work; all processes have a one-second RLIMIT_CPU. Children are waited and
reaped. Kernel `cpu.stat` before/after, child process-time reports, child `getrusage`
and external service counters are compared. The command, fixed source, fresh service
identity and limits are bound before launch.

The [first observer](../analysis/observe_evidence_calibration_tree_cpu_accounting.py)
stops on a strict property-schema mismatch. Installed systemd ignores deprecated
`CPUAccounting=yes` and omits that queried property. Its launch warning, returned
properties, failure and absent-service cleanup remain in
`output/infrastructure/tree-cpu-accounting-development-v1/`. The installed
`systemd.resource-control(5)` manual explicitly dates the deprecation to systemd 258:
CPU accounting is always available on the unified hierarchy. No model failure is
attributed to this operator expectation error.

The [separate v2](../analysis/observe_evidence_calibration_tree_cpu_accounting_v2.py)
removes only the obsolete property/query/check and changes versioned schemas. It
completes the fixed CPU work but fails a second mechanical expectation: after main
and children exit, systemd retires the kernel cgroup even with `RemainAfterExit=yes`.
The loaded service is `active/exited`, `ControlGroup` is empty and `TasksCurrent` is
`[not set]`. The retained CPU counter is still available. The original v2 terminal
remains `TECHNICAL_FAILURE`; it is not rewritten as an overall successful launch.

## Corrected interpretation of unchanged bytes

A [separate v3](../analysis/observe_evidence_calibration_tree_cpu_accounting_v3.py)
accepts the observed retired-cgroup form, requiring an earlier running snapshot
whose cgroup matches the fixed probe. It still requires successful main exit and
three identical final CPU counters. **V3 has not launched a new service.** A
[separate audit](../analysis/audit_evidence_calibration_tree_cpu_accounting.py)
validates the unchanged v2 bytes, binds their hash and writes an exclusive
expectation-correction record. It checks the exact original failed disposition and
cleanup; it launches no process and does not overwrite or adopt a transaction.

Observed v2 accounting:

| Quantity | Recorded value |
| --- | ---: |
| Children CPU work, summed | 0.452576876 s |
| Parent CPU work | 0.100655330 s |
| Reaped-child `getrusage` CPU | 0.489972000 s |
| Kernel tree CPU before work | 0.018870 s |
| Kernel tree CPU after reaping | 0.610111 s |
| Retained service CPU, final three samples | 0.616181 s |

Kernel accounting includes descendant consumption after those descendants exit.
Service accounting retains that total after kernel-cgroup retirement, including
additional startup/exit overhead. The registered fixed validation permits 20 ms
of measurement/scheduling tolerance between work reports and kernel deltas; this
check was present in v1 and was not changed after observing the values.

Eighteen focused checks pass: rejected accounting/identity/exit inconsistencies,
strict property parsing, preservation of failed bytes, exclusive correction output,
no process launch during revalidation and exact version-change boundaries. Both
observed services are absent after cleanup. The development manifest binds original
intents, terminals, probe output and the separate correction; no raw record is lost.

## Remaining execution boundary

This verifies a fixed accounting source, not cumulative-budget enforcement. It does
not establish a hard cutoff, sampling/termination overshoot, durability after
operator crash, whole-turn aggregation, or accounting over provider-side computation.
An empty retired-cgroup property is not a measured zero task counter. It is not
claimed as retained access to `cpu.stat` after group retirement. Future execution
integration must avoid reading a vanished cgroup as zero consumption, retain final
CPU counters before releasing the unit, account for all computation calls, and fail
closed on missing/regressing counters. Any sampled guard needs an explicit overshoot
policy; CPUQuota is still a rate bound. Limits must remain fair for B2/B3/B4 and must
be prospectively selected using valid development evidence.

Existing executors, brokers, MCP adapters and study callers are unchanged. Complete
model-facing tools/rendering, capacity, immutable runtime, whole-turn budgets and
measurement remain open. No semantic output, automated annotation, method-key join,
real-pilot score, physical acquisition, alpha spending or P11 freeze occurs. Failed
combined support, unlaunched C and unanswered reopening remain preserved. P11 keeps
nineteen open conditions and confirmation/replication N=0. Required B0/B1/B3 versus B4
reporting remains prospective, with episode effects, intervals and Holm-corrected
p-values including inconclusive results; correction creates no confirmatory alpha.
