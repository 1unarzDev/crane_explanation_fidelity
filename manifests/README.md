# Manifests

- `workspace.lock.json`: exact top-level and nested repository commits.
- `data/`: inventories containing logical locations, SHA-256, byte size, and provenance.
- `checkpoints/`: validated-run records tying data manifests to component commits.

Manifest paths are relative to the umbrella root when local. External locations should use stable
object-store identifiers, not expiring signed URLs or developer home-directory paths.
