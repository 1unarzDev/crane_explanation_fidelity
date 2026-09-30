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

## 2026-09-29 evidence-calibration handoff amendment

The earlier B2 continuation bullets above are historical: 57 valid B2 responses are already
retained. Do not regenerate them. The current model-backed work is atomic inventory extraction
and a synthetic source-context annotation canary. The managed shell now also mounts `.git` read-only,
so commits and pushes must be made from a normal writable host terminal after reviewing the shared
worktree. The repository files and local DVC cache stay in place.

The first 17 method-blind pilot atomization calls have valid records. Bank index 17,
`ax-6042b1c29021e662d8184d39e26738c5`, has unknown request disposition after the runner's
process handle disappeared. It is quarantined by
`manifests/study/evidence-calibration-b2-b4-pilot-atomization-v2-interruption-v1.json` and must
never be retried or called a model failure. The runner now writes durable intent files before each
future request; an intent without a terminal record is another stop condition, not a retry cue.

After local tests and a clean review of the worktree, sync the existing DVC roots and commit/push
the checkpoint from the normal host. The new DVC objects under `model_outputs` are currently local.
Then run transport preflight and the already-qualified non-study schema canary route as required by
the frozen jobs. With `READY_FOR_SCHEMA_CANARY` and an acceptable canary record, execute:

```bash
python analysis/run_evidence_calibration_source_context_canary.py
python analysis/run_evidence_calibration_pilot_atomization.py
python analysis/audit_evidence_calibration_pilot_atomization.py --allow-incomplete
python analysis/audit_evidence_calibration_pilot_inventory_triage.py
```

The source-context canary is synthetic and must pass both isolated Astra calls before any pilot
support annotation. The pilot extractor automatically skips the one ambiguous ID and can run only
the 96 still-uncalled responses. Even a completed extraction would leave a technical gap and
would not establish exhaustive inventory, qualified abstraction tags, a paired effect, or P11
readiness. Preserve every return and intent; do not quality-retry, replace the ambiguous ID, or
join the evaluator key during extraction. Push the resulting DVC objects and Git changes after the
jobs, then perform the separate per-response inventory and rubric/source measurement audits.

## 2026-09-29 separate assertion-role qualification

The assertion-role task is a separate measurement qualification. Its 24 synthetic cases, exact
prompt/schema, Astra-high no-tool configuration, and gates are frozen under
`evidence-calibration-claim-role-v1-freeze.json`; no role-model call has run in the managed shell.
After Git/DVC synchronization and a `READY_FOR_SCHEMA_CANARY` preflight on the normal host, run:

```bash
python analysis/audit_evidence_calibration_claim_role_freeze.py
python analysis/run_evidence_calibration_claim_role_qualification.py --mode canary
python analysis/run_evidence_calibration_claim_role_qualification.py --mode qualification
python analysis/audit_evidence_calibration_claim_role_qualification.py --allow-incomplete
```

The runner writes a durable intent before each call, reuses only an exact retained request, and
stops on a failed or interrupted call without retry. The canary is non-study. Two structurally
valid synthetic passes are only inputs to independent project semantic review against the frozen
construction reference; they do not qualify role labels automatically. A passing disposition and
prospective mechanistic/hedged endpoint mapping are required before any pilot role join or effect
analysis. The read-only audit reports uncalled slots, interrupted intents, retained failures, and
exact synthetic role/level candidate matches without granting qualification. Keep raw returns and
failures under the existing `model_outputs` DVC root and sync them
from the host. Neither masks nor prompts from retained B2/B4 responses are changed by this task.
