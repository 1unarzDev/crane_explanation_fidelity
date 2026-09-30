# Namespace scratch capacity candidate — 2026-09-30

## Actual prior boundary and retained failure

A fixed inspection of preserved service executor v4 observes writable regular-file
surfaces at `/`, `/tmp`, `/dev` and `/dev/shm`, each reporting tmpfs capacity
16721104896 bytes. Group memory limits constrain charged memory, but that does not
register filesystem scratch capacity. The inspection writes/deletes only one byte
on each private surface; no host filesystem or evidence file changes.

A separate v5 candidate supplies explicit page-aligned temporary/shared-memory
limits, read-only root/device backing mounts and disabled nested user namespaces.
Its first actual namespace launch fails because bubblewrap requires explicit
`--unshare-user` for `--disable-userns`; implicit `--unshare-all` does not satisfy
that option check. The source, stderr, nonzero return and one-shot transaction remain
preserved. This is a namespace startup failure, not a model failure or evidence of
valid method computation. The executor's retained generic runtime-failure envelope
is not retrospectively relabelled as a successful computation.

A [separate v6 candidate](../analysis/evidence_calibration_local_tool_sandbox_v6.py)
adds only explicit user-namespace creation. Tested exact diffs preserve v5 and v4.
Registered runtime/source/workspace bindings and interpreter arguments remain as
before; evidence and source access are not narrowed. Root/device backing mounts
become read-only; `/tmp` and `/dev/shm` remain usable with separate explicit caps.
No existing broker/MCP/study caller selects this candidate.

## Mechanical observations and expectation correction

With synthetic 1 MiB caps per scratch mount, v6 observes exact capacities, successful
scratch writes and EROFS for regular-file writes at root/device backing mounts.
Each scratch mount accepts exactly 1048576 bytes before ENOSPC. `/dev/null` still
accepts writes. Nested user-namespace creation returns -1 with ENOSPC.

The first validator assumed EPERM for namespace denial and fails that mechanical
expectation. Preserve its source transaction and a separate expectation-failure
record. A distinct validation record binds the unchanged terminal bytes and the
actual namespace-denial errno; no executor edit, transaction relaunch, semantic
reassessment or endpoint change occurs. The test now checks the observed ENOSPC
result rather than misidentifying a denial as a successful namespace creation.

Twelve scratch tests pass across two targeted invocations, including actual capacity
exhaustion, namespace denial, device/literal arithmetic, unchanged source/interpreter
access, invalid limits and the exact v5-to-v6 repair. Nineteen preserved service-v4
checks also passed during integration. A staged B2 primitive on an existing development
fixture still matches its deterministic reference under the bounded scratch candidate.
These are deterministic regression checks, not new method explanations or statistical N.

Raw one-shot inspection/startup/exhaustion records stay in ignored infrastructure
output. The manifest binds all three local roots: `scratch-boundary-inspection-v1`,
`bounded-scratch-development-v1` (failed startup), and `bounded-scratch-development-v2`
(successful mounts, unchanged exhaustion return and separate validation resolution).
Every observed service is absent after cleanup; no failed record is overwritten.

## Remaining scope and governance

The caps bound allocation on the registered writable tmpfs filesystems. They do not
certify every kernel-memory mechanism, metadata/inode quota, cumulative CPU budget,
whole-turn output/token limits or full security confinement. Root/device backing
mounts still report large underlying capacity but deny regular data writes. Pseudo
files/devices are not generic filesystem scratch. Complete harness/runtime binding
and failure-origin classification remain open; a generic nonzero namespace-launch
exit cannot by itself identify a model/program failure.

Synthetic capacities are probe parameters, not frozen study budgets. Future adoption
must bind exactly the same primitive computation surface and fair limits for B2/B3/B4,
validate diagnostic workloads and retain resource failures. Provider/model-facing
rendering, exact capacity, immutable restored runtime and qualified measurement remain
open. No old method caller, prompt, contract or immutable output is changed.

No semantic model/automated annotation call, method-key join, real-pilot score, physical
acquisition, alpha spending or P11 freeze occurs. Preserve failed combined support,
unlaunched C and pending measurement reopening. P11 keeps nineteen open conditions,
zero confirmation/replication N and all prospective five-method reporting requirements.
