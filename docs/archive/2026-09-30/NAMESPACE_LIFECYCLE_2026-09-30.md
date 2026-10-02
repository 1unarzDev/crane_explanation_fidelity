# Namespace lifecycle status seam — 2026-09-30

## Current classification gap

Preserved service executors distinguish OOM/time/transport failures from ordinary
nonzero exits, but a bubblewrap mount/exec failure can still share the ordinary
runtime-failure envelope. Parsing stderr wording would allow a program to imitate
a setup error. A separate fixed operator probe inspects bubblewrap's structured
`--json-status-fd` channel before any caller adoption or retrospective relabeling.

## Retained first observation and prospective correction

The first [observer](../analysis/observe_evidence_calibration_namespace_status.py)
expects no status record on mount setup failure. Actual bubblewrap emits a child/
namespace record before setup completes, then no exit record. Preserve that failed
expectation, exact source and transaction. The descriptor-visibility probe remains
unlaunched in that transaction. Initial child identity alone cannot prove payload
execution or validate an ordinary program failure.

A separate [observer v2](../analysis/observe_evidence_calibration_namespace_status_v2.py)
prospectively expects an incomplete lifecycle on the registered mount failure and
adds a missing-executable probe. All five fresh fixed probes pass:

- Normal output has an initial record and matching final exit=0 record.
- A program emits setup-looking stderr and exits 7; the structured final record
  still identifies a completed payload exit rather than interpreting its text.
- Missing mount source and missing executable each emit an initial record without
  a final exit record, nonzero launcher return and no payload stdout.
- The status file descriptor is not visible through any PID/fd entry available
  inside the payload namespace. This is a finite descriptor-exposure check, not a
  general isolation proof.

Raw status bytes, commands, return streams and one-shot intents/terminals stay in
ignored `output/infrastructure/namespace-status-development-v1/` and `-v2/` roots.
Neither old observation or executor is rewritten. Fixed probes invoke the exact v6
namespace builder directly with prlimit and a subprocess timeout; they do not
exercise a complete service wrapper or arbitrary-code output/capture harness.

## Mechanical lifecycle audit

A separate [auditor](../analysis/audit_evidence_calibration_namespace_lifecycle.py)
requires bounded UTF-8 JSON records, unique keys, valid integer child/namespace IDs,
exact exit shape and a matching launcher exit. It rejects corrupt, truncated,
nonfinite, boolean, oversized and mismatched records. Empty status remains unverified;
one initial record remains incomplete; only a matching final exit is verified.
None of these dispositions attributes a semantic/model failure.

Fifteen focused tests pass. A distinct hash-bound audit of the five unchanged v2
status files verifies completed normal/program/descriptor exits and incomplete
mount/exec lifecycles. This is mechanical inspection, not method-response rescoring.
The final exit marker also does not certify every intermediate interpreter/tool
startup stage. An absent exit marker is not uniquely a mount failure: interruption
and other infrastructure failures require their own retained dispositions.

## Remaining implementation and scientific boundary

A prospective service wrapper must open/retain the separate status descriptor,
preserve primitive argv/output and resource controls, prevent payload access, bind
code/requests and fail closed on incomplete or corrupt lifecycle records. Existing
executors/brokers/MCP/study callers do not select this seam. No old generic failure
is silently reclassified as a model result or retroactively counted as a valid call.
Full failure-origin handling, immutable runtime, cumulative CPU/turn budgets,
model-visible tool rendering/capacity and valid automated measurement remain open.

No semantic model/automated annotation invocation, method-key join, real-pilot score,
physical acquisition, alpha spending or P11 freeze occurs. Failed combined support,
unlaunched C and pending measurement reopening remain preserved. P11 retains nineteen
open conditions and zero confirmation/replication independent N. Five-method episode
comparisons and inconclusive/unfavorable reporting remain required.
