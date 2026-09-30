# Resource controls around the existing namespace — 2026-09-30

## Preserved failures and prospective repairs

A fixed operator observer wraps the unchanged v2 bubblewrap/prlimit command in a
fresh user systemd service. The first transaction fails before namespace launch:
`MemoryOOMGroup=yes` is unsupported by installed systemd 261.3. The installed
`systemd.service` manual states that `OOMPolicy=kill` sets `memory.oom.group=1`.
A separate v2 candidate removes only the redundant unsupported assignment. Its
namespace runs, but the original probe incorrectly expects only PATH and locale;
bubblewrap also supplies `PWD=/work`. A separate fixed inspection of the unchanged
v2 namespace confirms the complete three-value environment.

Both failed transactions and source versions remain preserved. A v3 candidate
changes only that probe expectation to require the exact PATH, locale and PWD
values. The exact two-step source diff is tested. No old transaction is relaunched,
rescored or rewritten. Unlaunched probes in each failed transaction stay unlaunched.
These are infrastructure failures, not model or annotation outcomes.

## Actual v3 evidence

The fixed operator [observer](../analysis/observe_evidence_calibration_cgroup_sandbox_v3.py)
uses a synthetic visible file, no physical episode or retained method answer.
Each fresh service command, source hash and workspace identity are written before
launch; output, systemd result and cleanup are retained separately. The registered
namespace command remains byte-for-byte equivalent after the service prefix.

- Synthetic visible reads and arithmetic work. Visible writes are denied; host
  home and sysfs are absent; the namespace environment matches exactly.
- Under `TasksMax=16`, thirteen child processes start and the next creation blocks.
  Children are killed and reaped; the service namespace also contains its launcher
  processes. The measured child count is not statistical N.
- A 128 MiB allocation under `MemoryMax=64 MiB`, zero swap and group OOM policy
  terminates with systemd `Result=oom-kill`, signal 9 and a recorded 64 MiB peak.
- An eight-second sleep under `RuntimeMaxSec=2s` terminates with `Result=timeout`,
  signal 15. The observed service runtime is 2.177 seconds, including termination;
  it is not an exact two-second total caller bound.

All four service units are absent after cleanup. Expected OOM/timeout nonzero exits
are retained resource-failure observations, never successful computation output.
Forty-two targeted tests pass across the version-diff/integration validators,
resource-observation checks and existing bounded local tools. Raw local records stay
in ignored `output/infrastructure/cgroup-sandbox-development-v1/`, `-v2/` and `-v3/`.
Hash-bound manifests preserve each disposition and the final evidence.

## Scope and remaining gates

Only finite operator-authored probes run. The observer uses `subprocess.run` to
capture these small fixed outputs; it is not the bounded arbitrary-code broker.
The v2 output limit in the Limits object is not enforced by this observer, because
it calls the command builder, not the v2 bounded capture runner. Existing broker,
MCP adapter, sandbox callers and host/runtime selection remain unchanged.

These observations establish task/memory/wall enforcement for the current service
and namespace composition. CPUQuota is a rate cap, not a cumulative CPU budget;
process-tree CPU accounting/limits, scratch capacity, arbitrary output containment,
durable provider/model execution, immutable restored-runtime adoption and complete
harness integration remain open. The two-second/64 MiB/16-task values are synthetic
probe settings, not study budgets. B2 primitive/source access is not narrowed.

No semantic method output, automated annotation, method-key join, endpoint scoring,
physical acquisition, alpha expenditure or P11 freeze occurs. Preserve failed
combined measurement, unlaunched C and pending measurement reopening. P11 keeps
nineteen open conditions; confirmation and replication independent N remain zero.
