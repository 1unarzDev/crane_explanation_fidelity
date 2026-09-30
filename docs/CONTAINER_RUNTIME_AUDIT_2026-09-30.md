# Read-only container audit of the existing runtime — 2026-09-30

A pinned public Python image now provides a trusted audit helper that can inspect all of the
existing host `/usr` mount. This resolves the content-inspection obstacle recorded in the prior
[runtime audit](RUNTIME_TREE_AUDIT_2026-09-30.md), while preserving both that failure and the
registered method runtime. No sandbox/broker caller switches to the container image.

## Helper identity and privilege boundary

The public `python:3.14.7-slim` lookup selected the `linux/amd64` image digest
`sha256:7bf6c3111fe094f8ee1a1cbcdc63c4cfb345b0e3df42d5aa9a90b3b4b022ab6d`.
Execution uses only that digest with `--pull=never`; image ID, repository digests and rootfs layers
are retained. The helper interpreter reports Python 3.14.7, matching the host patch version.
The image is used for auditing only; its libraries do not replace the methods' host libraries.

`analysis/observe_evidence_calibration_container_runtime_audit.py` stages exact static local Python
module dependencies, records their hashes, and invokes the unchanged full-tree inventory function.
It mounts only those source files and the host runtime, both read-only. There are no repository
recordings, study configurations, evaluator references, provider credentials or Docker socket
mounts. Network is disabled; image rootfs is read-only; all capabilities are dropped except
`DAC_READ_SEARCH`. The helper has no-new-privileges, 32-process, 1 GiB and two-CPU constraints.
Those limits and the 900-second controller timeout are audit parameters, not scientific budgets.

The read/search capability is restricted to this trusted operator-side audit helper. It is not
added to a model tool, explanation process or existing sandbox. It permits reading files whose
permission bits deny ordinary readers; it does not grant discretionary write override, and the
host mount remains read-only. File modes, bytes and method permissions remain unchanged.

An immutable intent binds the image, staged code, command code, controller version, limits and
unique labelled container name before launch. Runtime errors/partial inventories remain failures.
Cleanup removes only a container carrying this invocation's label; a daemon-inspection error is
not silently treated as proof of absence. Existing observation namespaces cannot be adopted or
replayed. This is a non-study audit transaction, not a top-level model-call executor.

## Retained development sequence and complete observation

1. The prior ordinary host scan failed on root-owned mode-0700 `cupsd`; non-interactive sudo
   required a password. Those records remain unchanged.
2. A container without capabilities read `cupsd`, but its whole-tree audit then failed on
   root/group execute-only mode-04110 `lib/dbus-daemon-launch-helper`. Preserve that terminal,
   stderr and null full-runtime result. Its container was removed.
3. A targeted read/search-capability probe hashed the second protected binary without changing
   permissions. The separately declared capability-bearing audit then completed the entire tree.

The completed observation contains **285,548 regular files, 19,047 directories and 92,448 symlinks**,
with **14,956,824,852 regular-file bytes**. Its canonical inventory identity is
`87244600302de9b8157ca8d05c292f805ceb97584e56c814e9c24cd7ac7da814`.
The full inventory, raw stderr and prior failed probes are retained locally outside Git under
ignored `output/infrastructure/runtime-inspection-2026-09-30/`; original `/tmp` observations are
unchanged. The repository stores hashes, counts and sanitized provenance. The audit container is absent.
No file or unreadable-content category was omitted to obtain completion.

Four focused checks cover exact static source staging, actual hashing of a mode-zero fixture
without changing its mode, immutable image/read-only/network configuration, and daemon-inspection
failure remaining unknown rather than becoming verified absence. The broader targeted suite also
retains the original unprivileged runtime failure/verification and installed-client checks.

## What this does and does not resolve

The current live host runtime now has a complete content/metadata observation. Earlier statements
that no complete digest existed describe the prior state; this dated record prospectively
supersedes that inspection status. The original host and container failures remain part of the
record. The explanation methods retain the full existing runtime and primitive computation access.

The host is still mutable Arch Linux rolling. The scan's fingerprint checks are not an atomic
snapshot, and the observation does not ensure the tree remains unchanged afterward. An immutable,
reproducible runtime and prospective checks remain necessary before scientific execution. The
helper image's immutability does not make the mounted host tree immutable. Kernel/namespace and
full provider harness binding, exact model-visible tools, lossless rendering, tokenizer/capacity,
complete budgets and durable one-shot model execution also remain open.

No model-backed explanation, annotation, method-key join, endpoint effect, fresh physical
configuration, alpha spending or P11 freeze occurred. The combined support failure and unlaunched
C remain retained; the measurement reopening proposal still awaits explicit adoption. P11 keeps
nineteen open conditions and confirmation/replication independent N=0. This is reproducibility
infrastructure for the existing contributions, not an additional scientific contribution.
