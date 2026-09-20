# Data governance

Raw data is deliberately excluded from Git.

- `robot_visible/`: only evidence permitted to reach an explanation condition.
- `evaluator_only/`: fault injection, simulator truth, gold propositions, answerability, and human
  annotations. No model prompt, retrieval index, filename, or model-visible metadata may expose it.

Use opaque shared episode IDs to join the trees during evaluation. Store locations, SHA-256 hashes,
sizes, provenance, and collection configuration under `manifests/data/`. Payloads are tracked by
DVC and synchronized to a private Cloudflare R2 bucket; the `.dvc` pointer files are the only
payload-related files committed under these roots. See `docs/DATA_STORAGE.md`.
