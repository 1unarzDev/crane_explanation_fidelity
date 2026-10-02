# Service-backed bounded computation candidate — 2026-09-30

## Candidate implementation and retained defect

The preserved v2 sandbox and broker remain unchanged. A separate service-backed
candidate wraps the exact v2 namespace/prlimit command in a user systemd service.
It combines kernel process-tree memory/tasks/CPU-rate settings with selector-based
bounded stdout/stderr capture, outer wall checks, service wall termination and
explicit stop/reset/absence checks. Detached descendants remain in the controlled
service cgroup. Each invocation writes an exclusive intent before launch and a
terminal afterward. Existing event directories cannot be reused.

An initial fixed arithmetic transaction passed. Its exact pre-disposition-guard
source snapshot remains in ignored output. Before further probes, the candidate
added fail-closed treatment for nonzero exits with missing service disposition.
The final v3 then passed finite Unicode, output-flood, OOM and detached-wall probes.
A later literal-argument probe found a real fidelity defect: systemd expanded a
braced environment expression and collapsed doubled dollar characters in the
Python code argument. The returned text and original v3 executor remain preserved;
that transaction is not rewritten as a passing literal-fidelity result. It used
only fixed synthetic text, no study code or credential expression.

A [separate v4 executor](../analysis/evidence_calibration_local_tool_sandbox_v4.py)
changes only `--expand-environment=no`. Exact diff tests and an actual literal-dollar,
percent, Unicode and newline test verify unchanged argument text. The retained v3
must not be adopted for arbitrary primitive computation. No existing method caller,
broker, MCP adapter or study configuration migrates to either candidate.

## Actual bounded behavior

- Exact outputs, including combined stdout/stderr at the byte boundary, are retained.
- Overflow keeps at most the explicit byte cap plus one detection byte observed;
  captured partial bytes are audit-only, with no successful result.
- Invalid UTF-8 retains original bytes in base64 and fails without lossy decoding.
- Kernel group OOM is distinguished through the service result and becomes a
  technical failure. Ordinary nonzero program exits remain tool runtime failures.
- Outer/service wall failure stops the service cgroup and removes detached children.
- Cleanup must finish with the unit absent. Unverified cleanup suppresses completed
  output. Missing service disposition cannot be treated as a program failure.
- Intent and terminal record commands, workspace identity, explicit local/tree limits,
  source hash, bounded output audit, service state and cleanup. No event replay occurs.

51 targeted tests pass: 17 service-v3 checks, 19 repaired-v4 checks and 15 existing
bounded-tool checks. The tests include real service/namespace output, OOM and detached
wall behavior plus explicit disposition/cleanup failure injection. Separate retained
v4 probes verify exact literal text, stderr overflow, group OOM and detached-wall
termination. Every observed service is absent after cleanup. Earlier v3 probe records
and the failed literal result remain in `output/infrastructure/service-capture-development-v1/`;
fresh v4 records remain in `output/infrastructure/service-capture-development-v2/`.

## Remaining scope

CPUQuota is a rate cap, not a cumulative CPU budget. Scratch storage, total tool/read
output over a model turn, exact tokenizer/provider capacity and complete model/tool/
reasoning/output budgets remain open. Service stop/control checks add bounded waits
beyond the execution wall limit; no exact end-to-end wall bound is claimed. No full
security certification or general runtime-equivalence claim follows from these probes.
The candidate uses the existing live `/usr`; immutable restored-runtime adoption,
complete kernel/provider/harness binding and model-facing renderer checks remain open.
Scientific prompts, episode masks and B2 primitive/source parity are not changed.

These are offline computation checks, not natural-language method outputs or a valid
comparative pilot. No automated annotation, method-key join, real-pilot endpoint
score, physical acquisition, alpha spending or P11 freeze occurs. Failed combined
measurement/unlaunched C and pending reopening remain unchanged. P11 retains nineteen
open conditions, confirmation/replication N=0 and the full prospective five-method
reporting requirements.
