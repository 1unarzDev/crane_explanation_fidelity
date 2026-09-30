# Service executor with namespace lifecycle audit — 2026-09-30

## Separate implementation candidate

[Executor v7](../analysis/evidence_calibration_local_tool_sandbox_v7.py) extends the
preserved v6 service/scratch candidate with a separate
[operator wrapper](../analysis/evidence_calibration_namespace_wrapper.py). The
wrapper reads a hash-bound namespace request outside the method workspace, opens
an exclusive status file, supplies bubblewrap's status descriptor and preserves
payload stdout/stderr for the existing bounded outer capture. It introduces no
shell or provider call. Request bytes have a fixed 16 MiB safety cap; this is not
model/tokenizer capacity certification or a selected scientific prompt budget.

Intent binds executor/wrapper hashes, exact namespace argv/request hash, workspace
identity and local/tree/scratch limits before launch. The helper runs in the same
service cgroup; its overhead is part of that service. Evidence/source/interpreter
access and the registered v6 namespace controls remain. Existing versions, broker,
MCP adapter and study callers remain unchanged and do not select v7.

After service cleanup, the executor reads at most 8193 status bytes from a regular
nofollow file and invokes the strict lifecycle audit. Completed results require
matching initial/final records and launcher exit. Empty, incomplete, corrupt or
oversized records suppress output as a technical failure. A child PID alone does
not certify setup. Status bytes/hashes remain separate operator audit material.
OOM, overflow, encoding, wall and cleanup failures keep their existing dispositions;
a lifecycle problem cannot turn them into successful partial evidence.

## Observed verification

31 targeted checks pass across two invocations: sixteen new integrated-executor
checks and fifteen lifecycle-audit checks. These include exact dollar/percent/Unicode
output, setup-looking program stderr, injected mount/exec failures, payload-visible
FD absence, empty/partial/corrupt/oversized status, wrapper request integrity and
path constraints, OOM/output/encoding failure, detached-wall cleanup and a staged
B2 primitive matching its existing deterministic reference. Synthetic limits are
probe settings, not frozen method budgets.

Distinct retained service transactions demonstrate literal-output success,
setup-looking program stderr with verified exit 7 and ordinary runtime-failure
status, and an operator-injected absent mount source with incomplete lifecycle,
technical-failure status and null result. Exact fault-injection client and resulting
argv bind before launch. All three services are absent after cleanup. Raw intent,
namespace requests/status, bounded audit bytes and terminals remain local in ignored
`output/infrastructure/service-lifecycle-development-v1/`. No prior failed record is
relaunched, rescored or overwritten.

## Limits of the signal and remaining gates

The final marker verifies a namespace payload exit; it does not attest every
prlimit/interpreter/tool initialization stage or establish semantic model failure.
Missing final status is not uniquely a mount error. The wrapper/host runtime still
requires immutable distribution and complete harness binding; these finite FD checks
are not a general security certification. Full broker/MCP/provider integration,
cumulative CPU/turn budgets, exact tokenizer/capacity and model-visible rendering
remain open. No generic historical failure receives a retrospective new method label.

No semantic model/automated annotation invocation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched C and pending measurement-reopening decision remain preserved. P11 keeps
nineteen open conditions and zero confirmation/replication independent N. Five-method
prospective effects/intervals/corrected p-values remain required, including unfavorable
and inconclusive results.
