# Model-job host execution runbook

Status: **required operational boundary for B2/Sol and Luna calls**.

The model runners and immutable caches remain in `/home/lunarz/crane_explain`. The managed Codex
shell exports `CODEX_SANDBOX_NETWORK_DISABLED=1`; outbound sockets are unavailable there. DNS,
API-key, login, and bubblewrap changes cannot restore network access inside that parent sandbox.
`bwrap --share-net` only inherits the parent's network namespace.

Run model transport and jobs from a normal network-enabled host terminal. Do not copy the
repository, change request identities, delete retained failures, or create replacement caches.

## Preflight

```bash
cd /home/lunarz/crane_explain

test "${CODEX_SANDBOX_NETWORK_DISABLED:-0}" != 1
getent ahosts example.com
getent ahosts codex.lunarz.dev
python analysis/audit_b2_transport_readiness.py
```

Do not launch a model job unless the final command reports exactly
`READY_FOR_SCHEMA_CANARY`. A managed-shell result of `RUN_FROM_NETWORK_ENABLED_HOST` is expected and
is not a DNS or credential defect.

## Authentication

For Luna and direct Codex-LB structured requests, export the existing credential in the host shell:

```bash
export CODEX_LB_API_KEY='...'
```

For the historical Sol/Codex CLI transport, verify the existing ChatGPT login:

```bash
codex login status
```

Never print, commit, copy into a packet, or persist either credential in a call record.

## Execution invariants

- Sol/B2 uses the existing `codex exec --ephemeral --sandbox read-only` caller and the historical
  ChatGPT-login-backed provider configuration.
- Luna uses the existing isolated structured-output caller, `CODEX_LB_API_KEY`, no tools, and a
  separate immutable cache for every pass.
- The three retained failed B2 logical requests remain retired. Resume only the 57 never-launched
  request identities after the schema canary passes.
- Do not retry an invalid or poor answer, select among accidental duplicates, change prompts,
  models, reasoning settings, schemas, evidence, or tool access, or open comparative outcomes.
- Write to the existing job-local caches and output roots. A successful cached request is never
  regenerated; a retained failure remains visible under its declared disposition.
- Confirmation stays prohibited until the development pilot, exact-task agent-annotation
  qualification, and all P11 gates pass.

## Return-to-coordinator checklist

After host execution, retain the preflight manifest and report only: audit status, schema-canary
status, logical request IDs attempted, cache keys, valid/failed counts, and artifact hashes. Do not
report an arbitrary interim B2-versus-B4 outcome preview.
