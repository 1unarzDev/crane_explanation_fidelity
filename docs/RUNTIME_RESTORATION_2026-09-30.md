# Local runtime restoration candidate — 2026-09-30

`analysis/restore_evidence_calibration_runtime_snapshot.py` adds a separate development restoration
path for the hash-bound full `/usr` archive. Existing method sandboxes/brokers remain unchanged;
this path does not adopt a runtime or invoke a model/annotator.

## Restoration transaction

Before creating a destination, the controller verifies the complete archive against its original
content/metadata inventory and framing guard. It requires a fresh ignored infrastructure directory
and sufficient disk reserve. An immutable intent binds archive identity, trusted helper image,
source closure, restoration code, privileges/limits and unique labelled container identity.

The pinned helper image mounts the archive, inventory and exact verifier sources read-only.
Only the fresh destination is writable. GNU tar restores numeric owners, permissions and PAX
extended attributes, delaying directory restoration until children are created. The trusted helper
receives only the declared read/override, chown, owner and file-capability privileges needed for
restoration. Network is disabled, rootfs is read-only, no-new-privileges is set and process/memory/
CPU/time limits are explicit. These are operator-side restoration parameters, not method budgets.
No Docker socket, study data, evaluator reference or provider credential is mounted.

`analysis/verify_evidence_calibration_runtime_restoration.py` hashes the whole restored runtime
and compares its canonical identity against the original inventory. It separately compares every
member's nanosecond mtime and all extended-attribute bytes against the archive and checks each
hardlink's device/inode identity. A mismatch or partial tree is retained as failure without repair
or replacement. Container cleanup is restricted to this request's label; unknown cleanup remains
unknown. Existing namespaces cannot replay or resume this transaction.

Seven focused tests verify matching metadata and reject altered timestamps, xattrs, hardlinks,
bytes and modes, plus an actual container setgid-capability reproduction. These tests do not qualify a scientific runtime or increase experimental N.

## Scientific scope

Restoring an exact tree does not make the host or restored writable directory immutable. Runtime
mounting, loader/stdlib behavior, original staged tool and diagnostic-computation parity, kernel/
namespace assumptions, distribution and prospective scientific adoption remain separate gates.
Actual model-facing tools, lossless rendering, tokenizer/capacity, full budgets and durable model
execution still require binding. Privileges granted to this trusted restoration helper are not
granted to explanation methods.

No model/annotation call, method-key join, endpoint effect, physical allocation, alpha spending or
P11 freeze occurs. The combined support failure, unlaunched C and pending measurement reopening
remain retained. Confirmation/replication N remain zero.

## Retained full restoration failure and prospective repair

The first full restoration extracted the tree, but whole-inventory equality failed. A separate
read-only full-tree audit found exactly two differences: `bin/wall` and `bin/write` have mode
`0755` instead of registered `02755`. Their content, numeric owners and groups match; all other
inventory entries and root metadata match. The original failed terminal, staged verifier,
controller source, stderr, restored tree and difference audit remain retained and unchanged.

A minimal actual-container probe shows setgid loss without `FSETID` and preserved `02755` with
that capability. The later controller candidate adds `FSETID` only to the trusted restoration
helper. Another full restoration has not run; this repair does not override the failed transaction.
GNU tar also emitted two `hdrcharset` warnings, retained in stderr. Full xattr/timestamp/hardlink
verification stopped at inventory mismatch and remains uncompleted.
