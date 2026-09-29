# Evidence-calibration automated-agent annotation runbook

Status: **qualified prospective automated-annotation configuration; empirical B2/B4 dry run is not complete**. The 2026-09-29 v4 qualification disposition and amendment v2 supersede the older Luna candidate below. See `manifests/study/evidence-calibration-agent-qualification-disposition-v1.json` for the hash-bound active configuration.

This runbook applies only to annotation not yet generated for the prospective evidence-calibration study. The earlier two-human development plan remains retained in its original pilot declaration; the prospective replacement is recorded by `evidence-calibration-agent-annotation-amendment-v1.json`. No historical output is relabeled.

Every return under this runbook is an **automated annotation** and every reported effect is **agent-assessed**. These outputs are never described as human annotations, human validation, or inter-human agreement.

## Roles and isolation

- Agent A and Agent B are separate, blinded provider invocations with different logical request identities and retained call records. Each receives one form and no other return.
- Agent C is invoked only for disagreements. It receives the original blinded form and disagreement-only handoff, not annotator identities, agreed decisions, the evaluator join key, or method identity.
- The qualified configuration is `gpt-6-astra` at high reasoning effort through the login-backed ephemeral Codex CLI, with the v2 structured schemas, no tools, and no quality-driven retry.
- One model family creates correlated-error risk. Separate invocations measure repeatability; they do not create independent human raters or robot episodes.
- Quantities, units, intervals, thresholds, hashes, identities, mask relations, and endpoint logic remain deterministically checked. Agents evaluate semantic attachment, evidential scope, abstraction level, limitations, and false-premise handling.

## Labels and fields

Use exactly `SUPPORTED_BY_VISIBLE_EVIDENCE`, `CONTRADICTED_BY_VISIBLE_EVIDENCE`, `INSUFFICIENT_VISIBLE_EVIDENCE`, `PHYSICALLY_TRUE_BUT_UNSUPPORTED`, or `UNINTERPRETABLE` for every atomic statement. Absence from a compact inventory is not unsupportedness when the permitted packet contains support. Physical truth never repairs missing robot-visible support.

For each required unit, record whether it is communicated and its exact response span when true. Select the deepest level actually asserted. Score every required limitation independently. On applicable nominal/success questions, distinguish explicit false-premise rejection from acceptance, partial handling, and uninterpretable handling.

## Qualification before primary use

Luna v12 remains qualified only for its frozen complete-supported-diagnostic endpoint. It does not automatically validate this five-way taxonomy, highest-level score, or `PHYSICALLY_TRUE_BUT_UNSUPPORTED` distinction.

Before primary scoring, freeze and run a bounded exact-task qualification: use development cases for debugging, then two isolated passes over fresh held-out cases. Protect physical truth versus visible support, unsupported versus contradicted specificity, useful partial diagnosis versus over-abstention, recovery chronology versus outcome causation, false premises, valid extra facts, prompt injection, and method blinding. Predeclare accuracy and false-acceptance/rejection gates. Retain any failed qualification without lowering gates or retrying poor returns.

The active qualification is frozen at
`research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v4-freeze.json`.
The v4 suite and its qualified result are hash-bound by the disposition above. Two isolated passes
passed every held-out gate. The v1/v2 pre-inference failures and invalid v3 reference remain retained.

Qualification permits prospective agent-assessed scoring on the declared task. It does not make
the inspected B2/B4 pilot a fresh confirmation sample. Deterministically checkable quantities and
endpoint operations remain code-scored.

## Execution

Model calls must run from a normal network-enabled host terminal. The managed Codex shell exports
`CODEX_SANDBOX_NETWORK_DISABLED=1`; changing DNS, credentials, authentication, or bubblewrap flags
inside it cannot enable outbound sockets. Follow `docs/MODEL_JOB_HOST_RUNBOOK.md` and proceed only
after `analysis/audit_b2_transport_readiness.py` reports `READY_FOR_SCHEMA_CANARY`.

Build packets with `analysis/build_agent_atomic_claim_annotation_packets.py`, then run:

```bash
python analysis/run_evidence_calibration_agent_annotation.py \
  --packet /path/to/blinded-agent-packet.json \
  --output-root /path/to/immutable-output-directory
```

The qualified Astra route uses the existing ChatGPT-login-backed
`codex exec --ephemeral --sandbox read-only` transport and the exact v2 schemas bound in the
qualification disposition. It never writes credentials into artifacts.

Each request has one immutable cache identity. Failed or invalid returns are retained and not quality-retried. Agreement is agent-pass repeatability, not effectiveness or accuracy. Agent C can select only a supplied value and must justify it. Original disagreements remain retained.

The completed qualification was run from the host with:

```bash
python analysis/run_evidence_calibration_agent_qualification.py \
  --suite research/explanation_fidelity/qualification/evidence-calibration-agent-exact-task-v4.json \
  --freeze research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-agent-exact-task-v4-freeze.json \
  --output-root model_outputs/automated_annotations/evidence-calibration-agent-exact-task-v4
```

## P11 acceptance gate

Before P11: exact-task held-out qualification must pass; A/B identities and caches must be separate; malformed returns must fail closed; C must be distinct and disagreement-only; all artifacts must remain hash-audited; the method key must remain unopened through finalization; and method-specific judge-error sensitivity must be disclosed. Passing qualifies only the declared automated measurement, not human validity or trust.
