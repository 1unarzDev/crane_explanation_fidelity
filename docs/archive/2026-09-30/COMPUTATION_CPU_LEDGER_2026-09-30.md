# Computation CPU ledger candidate — 2026-09-30

## Serial broker scope

A [separate ledger v2](../analysis/evidence_calibration_computation_cpu_ledger_v2.py) and
[broker v7](../analysis/evidence_calibration_tool_broker_v7.py) charge actual service
CPU across computation calls in one serial broker lifetime. The ledger requires an
explicit typed total and per-call CPU budget. It is created in a fresh operator
namespace, bound to workspace identity/source, and never adopts an existing ledger.
Original brokers, executors, MCP adapters, installed-client observers and study
callers remain unchanged.

Before each computation, an exclusive fsynced reservation binds event, execution
path, tool-request hash, settled consumption and effective CPU budget. The effective
threshold is the smaller of per-call cap and remaining total. Remaining CPU below
the executor's 10 ms minimum is rejected; it is never rounded up. A pending reservation
closes admission until settlement. This API is serial; it is not a concurrent or
distributed coordinator.

Settlement checks matching v10 intent/terminal, workspace/unit identity, effective
budget, final CPU arithmetic, every sequential raw counter sample, monotonic numeric
consumption, quiescent terminal state and absent-service cleanup. Regular-file,
no-symlink and byte-bound checks prevent unsafe operator-record reads. Successful,
program-failed and technical-failed computations with valid accounting are all
charged their actual CPU, including overshoot. Failed work is never refunded and
consumption is not clamped to a requested threshold or total.

Missing/invalid accounting records an exclusive unknown disposition and closes all
further tool admission. Unknown spent/remaining totals are null; a separate field
reports only previously settled known consumption. Neither missing CPU nor an
unsettled reservation is represented as zero total use. Settlement persistence
failure leaves the reservation pending; a second settlement attempt is prohibited.
A retained event/session cannot be relaunched or adopted to clear the unknown state.
No result is delivered before settlement. Original executor results remain in their
records even when uncertain accounting prevents delivery.

Verified CPU exhaustion prohibits further computations; reads retain their exact
registered semantics because their host CPU is outside this service-tree counter.
Unknown accounting closes both reads and computations. This candidate does not
claim a read/whole-turn CPU budget. A future governed coordinator must bind exactly
one ledger to the intended turn/condition; creating fresh sibling brokers is not
established as an authorized budget reset.

## Actual development evidence

Forty-two focused checks pass across three invocations: twenty-five ledger checks,
fifteen broker-v6 checks, and two reservation-isolation/repair checks. They cover charge arithmetic, failed consumption/overshoot,
remaining-threshold adjustment, pending/unknown admission, no replay/adoption,
minimum threshold, corrupted identities/counters/samples, storage failure, explicit
types, bounded operator reads, exact inventories/lossless reads, prior resource
failures, staged B2 primitive parity and actual shared-total/unknown flows.

Two separately retained fixed flows are pre-bound in
`output/infrastructure/computation-cpu-ledger-development-v1/`:

1. A literal computation consumes 34.665 ms from a synthetic 310 ms total. The next
   four-descendant CPU workload receives the remaining 275.335 ms threshold, then
   returns null `CUMULATIVE_CPU_LIMIT`. Its full 301.728 ms consumption is charged.
   Total charged CPU is 336.393 ms, preserving 26.393 ms overshoot. Another computation
   is denied without launching a service. The full 4096-character Unicode read still
   succeeds. This is a sampled stop, not a hard total CPU cap.
2. An explicitly operator-injected audit-read corruption supplies the validator a
   copied terminal with final CPU removed. The original successful executor file is
   preserved unchanged. The broker withholds delivery, records unknown accounting,
   and denies later computation/read calls. This is a synthetic auditor fault, not
   an observed method/model failure or an actual missing original CPU counter.

Review finds that ledger v1's returned reservation shares its nested budget object
with pending internal state. Preserve v1/broker v6 and their fixed observations.
Separate ledger v2 returns a deep copy; broker v7 changes only its selector and
request schema. Two targeted checks prove caller mutation cannot alter retained/
pending budgets and verify the exact repair boundaries. V2/broker v7 repeats the
fixed flows in a distinct fresh root, `computation-cpu-ledger-development-v2/`:
34.572+317.280=351.852 ms is charged against 310 ms total, retaining 41.852 ms
overshoot. The subsequent computation is denied, full reads remain exact, and the
separately injected audit fault again closes all tool admission. These distinct
source-version transactions do not adopt or retry an old session. Both roots stay
preserved; larger overshoot is not discarded or treated as a method effect.

All six retained computation services across both versions are absent after cleanup. Client/source/
pre-call plan, broker requests, reservations, settlements, original execution files,
CPU samples and summaries are hash-bound in the development manifest. The injected
fault is isolated from ordinary execution; no study response or immutable cache is
modified. These flows produce no semantic explanation or statistical sample.

## Remaining gates

MCP and installed-client routing for broker v7 remain unintegrated. Host read/control/
monitor CPU, provider/reasoning/token costs and other tool routes are outside this
ledger. Whole-turn accounting, overshoot policy/bounds, full kernel/provider
confinement, immutable runtime/storage/distribution, power-loss durability and
end-to-end one-shot model execution remain open. Fsynced files and admission checks
do not prove directory/power-loss durability or multi-process exclusion. Synthetic
budgets are not selected scientific limits; B2/B3/B4 require fair prospectively
bound settings and valid development evidence before study adoption.

No semantic model/automated annotation call, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched C and unanswered reopening remain preserved. P11 retains nineteen open
conditions, no hash mismatches and confirmation/replication independent N=0. Required
B0/B1/B3 comparisons with B4 remain prospective, with episode effects, intervals and
Holm-corrected p-values including inconclusive results.
