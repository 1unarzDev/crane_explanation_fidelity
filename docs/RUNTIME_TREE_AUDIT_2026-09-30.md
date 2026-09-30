# Full local runtime identity audit — 2026-09-30

The existing local tool sandbox exposes `/usr` read-only. Entry-point hashes identify bubblewrap,
Python and prlimit, but do not identify every library, executable, stdlib module or other file
available under that mount. `analysis/audit_evidence_calibration_runtime_tree.py` adds a separate
offline identity/verification candidate. Existing sandboxes, brokers and callers remain unchanged;
no scientific runtime is selected or frozen.

## Identity and fail-closed verification

The inventory includes root/directory permissions and numeric owners; every regular file's size
and SHA-256; each symlink's literal target/metadata; and empty directories. It rejects special
files, a symlink root and unreadable content. Paths are relative and every parent must be a declared
directory. A canonical hash binds the entire typed inventory. Verification recomputes contents and
metadata, detecting changed bytes even if size and mtime are restored. Timestamps and inodes are
transient consistency checks, rather than part of the content identity.

Traversal and file hashing use anchored directory descriptors and `O_NOFOLLOW`. Symlinks are
recorded without reading their targets. Reads use 1 MiB chunks. Before/after descriptor and path
fingerprints reject ordinary concurrent mutation. A second metadata scan rejects changes to
previously hashed entries before the first scan completes. This is not an atomic snapshot: it
cannot rule out every transient mutation, privileged manipulation or changes after the observation.
A read-only, immutable runtime and prospective execution checks remain necessary for a study.

The CLI accepts a fresh `/tmp` output name and scans the registered `/usr` root. It retains an
intent before reading, writes a full inventory only on completion, and records a terminal failure
on exception. It refuses an existing output or intent instead of adopting/replaying it. A failed
scan cannot become a partial full-runtime identity. Raw inventories stay outside Git because a
host tree may contain paths beyond the paper's public environment specification.

## Actual host observation: failed, retained

The attempted whole-tree scan stopped before completion with
`PermissionError: [Errno 13] Permission denied: 'cupsd'`. The inspected `/usr/bin/cupsd` and
`/usr/sbin/cupsd` paths have mode `0700` and owner/group `0/0`. A non-interactive privileged read
also failed with `sudo: a password is required`. No permissions, authentication, binaries or
provider settings were changed. The original intent/failure and initial source hash remain
retained; no full inventory or runtime content digest was produced.

The later audit candidate adds the exact relative file path to permission errors and tests this
behavior with an unprivileged synthetic file. It does not skip or substitute unknown bytes. The
host identifies as Arch Linux, rolling; this OS label is descriptive and cannot substitute for an
immutable content identity. The current environment therefore has an explicit unresolved runtime
inspection prerequisite, rather than a verified complete runtime binding.

For subsequent study execution, a prospectively declared runtime must be completely inspectable
and reproducible. A separately constructed immutable image may satisfy that requirement, but its
contents, permissions, dependency behavior, kernel/namespace assumptions and method parity still
need validation and binding. This audit does not build an image or choose a replacement environment.
It does not imply that unreadable `cupsd` is needed for primitive diagnosis; it demonstrates why
hashing entry points is not proof of the full currently exposed tree.

## Verification and scientific boundary

Twelve synthetic checks cover deterministic identity, exact file/byte totals, changed contents,
permissions, additions/removals, symlink targets, empty-directory removal, special files/root links,
concurrent changes, record hash/path tampering, unreadable files and a directory-to-symlink race.
No physical episode, explanation response or evaluator artifact is read by these tests. They are
infrastructure evidence and do not increase experimental N.

P11 keeps nineteen open conditions. Provider/model-facing tools, lossless rendering, exact-route
capacity, full runtime, complete budgets and durable model execution remain open. The combined
support canary failure, unlaunched C and pending measurement reopening decision are unchanged.
No model/annotation call, method-key join, endpoint effect, physical allocation or alpha expenditure
occurs; confirmation/replication independent N remain zero.
