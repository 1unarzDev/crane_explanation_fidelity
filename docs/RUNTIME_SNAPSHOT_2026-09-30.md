# Exact local runtime archive candidate — 2026-09-30

`analysis/build_evidence_calibration_runtime_snapshot.py` preserves the complete inventoried host
`/usr` tree in a separately verified archive. It uses the pinned trusted read-only audit helper
and the existing inventory identity; no method caller or runtime changes. This is a development
artifact, with scientific adoption, restoration and execution checks still open.

## Bound export and verification

The request binds the expected inventory/raw hash, helper image/layers, exact staged source closure,
export code, resource limits and unique labelled container. The host runtime, audit source and
expected inventory are read-only mounts; network is absent. Only the trusted helper carries
`DAC_READ_SEARCH`. Output streams into a fresh ignored disk directory, avoiding a whole archive
in memory or `/tmp` tmpfs. A computed archive-byte budget and free-space reserve precede launch.

Export checks every expected path and permission/owner metadata, reads regular files through
anchored no-follow descriptors, and checks every content hash. Hardlinks preserve shared identity;
symlink targets remain literal. Source nanosecond mtimes and extended attributes are retained in
PAX headers. Empty directories and root metadata are included. Fingerprint checks reject ordinary
changes during export; the earlier scan's canonical digest does not include timestamps or xattrs,
so those are additionally bound by the completed archive digest. No live path category is omitted.

A separate streaming verification reads every archive member, checks content/metadata against the
expected inventory, and rejects omissions, duplicates, outside-root entries and unvalidated
hardlink targets. The final verifier also requires zero-block termination, rejects nonzero trailing
material and guards against concurrent archive modification. It binds the complete archive's
SHA-256, member count and recorded extended-attribute identity. It does not extract the archive or
claim that an extraction tool has preserved those attributes.

The exporter ran with an earlier verifier before the final end-framing guard was added. Its staged
source hashes and completed terminal remain unchanged. A separate one-shot strict verification
binds the final verifier and confirms the same finished archive, rather than rewriting that terminal
or rerunning export. Partial/failed artifacts remain retained under their original namespaces.

## Actual development artifact

The archive matches inventory identity
`87244600302de9b8157ca8d05c292f805ceb97584e56c814e9c24cd7ac7da814` and contains all **397,044**
expected members. It is **15,589,560,320 bytes**, with SHA-256
`2169ee2f7b4cb82f159e5a4427769c33ef3d4e79ee64ff03e674584b0815fb5d`.
Seven entries carry extended attributes. The source-file inventory has 285548 regular-file paths,
19047 directory paths and 92448 symlink paths; the archive adds the runtime root entry.

Raw archive, original intent/terminal, staged sources, stderr and strict verification remain in
ignored `output/infrastructure/runtime-snapshot-development-v1/`. These host artifacts are local
only and have not been published or uploaded to a shared data remote. Git retains sanitized
provenance and hashes. The labelled exporter container is absent; no unknown container is adopted.

Eleven focused tests exercise exact round-trip inventory verification, deterministic repeated
export for unchanged fixtures, hardlinks, symlinks, permissions, nanosecond mtimes, binary xattrs,
changed contents/extra paths, archive omission/duplication/path escape/byte or mode tampering,
output limits, truncated terminators and nonzero trailing data. They use synthetic trees only.

## Remaining scientific/runtime boundary

This archive fixes a recoverable content artifact locally; it does not make the live Arch host
immutable, establish an atomic source snapshot or prove restoration and execution equivalence.
Prospective restoration must preserve permissions, owners, hardlinks, xattrs and required loader
layout, verify complete content, and exercise the original inventory tool/diagnostic primitives.
Distribution/provenance review, kernel/namespace assumptions and binding of the actual enclosing
harness remain separate. No old freeze is rewritten and no selected study runtime follows.

Actual model-facing tools, lossless renderer output, exact-route tokenizer/capacity, complete
budgets, durable one-shot model execution and qualified measurement remain open. The combined
support failure and unlaunched C are preserved; measurement reopening awaits explicit adoption.
P11 remains closed with nineteen open conditions and confirmation/replication N=0. No model call,
annotation, key join, endpoint effect, physical allocation or alpha expenditure occurs.
