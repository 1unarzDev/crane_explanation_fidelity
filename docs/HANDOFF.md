# Project handoff: Claude replication evidence

This is a time-sensitive execution handoff for the next research agent. It is not an instruction
file loaded automatically by Claude Code. Read it explicitly after cloning the repository.

## Objective and deadline

Advance this repository toward a statistically defensible TRUSTMORE 2026 submission by October 4,
2026 AoE. The research claim concerns evidence-checked natural-language explanations of robot
navigation decisions and failures, not framework breadth. Fluent but unsupported explanation is
the principal failure mode.

The immediate assigned workstream is to gather the already-predeclared Claude-family replication
evidence. Do not redesign the study, recapture the selected episodes, or inspect sealed answer text
while running this arm.

## Start here

Read these files completely, in order:

1. `CONTEXT.md`
2. `README.md`
3. `docs/MODEL_FAMILY_REPLICATION.md`
4. `docs/STUDY_DESIGN.md`
5. `docs/ANNOTATION_GUIDE.md`
6. `docs/ANNOTATION_WORKFLOW.md`
7. `docs/DATA_STORAGE.md`
8. the newest entries in `docs/EXPERIMENTS.md` and `docs/DECISIONS.md`
9. `manifests/study/provenance-claude-replication-arm-v1.json` and both amendments

The model-family replication document is provider-neutral; Claude is its first worked arm. Keep
model configuration, provider adapter, agent harness, and study condition separate in code and
claims. Do not make the architecture Claude-specific.

## Restore the authoritative workspace

Clone with submodules, initialize nested package dependencies, then restore governed artifacts from
the private DVC remote. The Git checkout alone does not contain captures, model outputs, or caches.

```bash
git clone --recurse-submodules https://github.com/1unarzDev/crane_explanation_fidelity.git
cd crane_explanation_fidelity
scripts/setup_workspace.sh

uv tool install --python 3.13 dvc --with dvc-s3
cp .env.example .env
# Obtain separate, revocable R2 credentials from the repository owner and fill .env locally.
# Never print, commit, or paste .env or .dvc/config.local.
scripts/configure_dvc_r2.sh
scripts/dvc_r2_sync.sh status
scripts/dvc_r2_sync.sh pull
```

On the existing project machine, `.env` and `.dvc/config.local` may already be provisioned. Still
run guarded `status` and `pull`. The snapshot pushed before this handoff contains the governed data,
primary outputs, and caches through `pn-0021`; `status` reported the cache and remote in sync.

Verify the pinned workspace before model execution:

```bash
git status --short
git submodule status
claude --version
PYTHONPATH=packages/astro_dock/src/crane_explain/src:packages/astro_dock/src/crane_explain_ros:analysis \
  python -m pytest -q analysis tests packages/astro_dock/src/crane_explain/tests
```

Do not advance submodule pointers, frozen prompts, the annotation guide, primary runner, split, or
study manifests. Stop and diagnose any dirty tracked file you did not create; never overwrite
another session's work.

If `claude --version` fails or the selected model is not authenticated, record the sealed arm as
`BLOCKED` and preserve every existing artifact. Do not silently substitute a different model,
provider, model alias, effort, or interactive agent response for the declared CLI calls.

## Authoritative current state

- Primary sealed collection: **21 included independent episodes**, comprising 11
  recovery-followed-by-success and 10 terminal-recovery-abort instances; zero exclusions.
- Primary model execution: **126 one-shot Luna-low calls** across F/G/H; no retry or resampling.
- Completed episode range: `pn-0001` through `pn-0021`. The next unstarted primary row is
  `pn-0022`; do not rerun or replace any earlier row.
- No sealed primary or Claude answer has been annotated. No sealed effect estimate exists.
- The historical 54-row primary packet lacks its evaluator-only key and is unusable. Never
  reconstruct that key; generate a fresh packet/key pair together when annotation begins.
- The selected Claude configuration is `claude-sonnet-5` at low effort. The predeclared
  development control and model selection are complete.
- The selected sealed Claude replication over `pn-0001` through `pn-0009` is **COLLECTED and
  NOT_ANNOTATED** as of 2026-09-20: 18 envelopes, 54 physical calls, manifest built and hashes
  verified, published through DVC. It reuses episodes and therefore contributes **zero** new
  independent clusters.
- DVC snapshot commit: `fe7cc9b` or a descendant. There are now **seven** governed pointers;
  `data/evaluator_only/annotation_keys` was added so a blinded packet cannot outlive its key.
- Pinned `crane_ml` commit: `c559932a5ebef00bfa7752511799fd904e5c9dbe`.

## Immediate execution: sealed Claude replication

The declared arm is fixed to nine episodes. Do not extend it to `pn-0010+` without a prospective,
scientifically justified amendment written before any additional call. Run the existing resumable
batch exactly once:

```bash
scripts/run_claude_arm_batch.py \
  --batch sealed \
  --model claude-sonnet-5 \
  --reasoning-effort low \
  --episodes pn-0001 pn-0002 pn-0003 pn-0004 pn-0005 pn-0006 pn-0007 pn-0008 pn-0009 \
  --output-root model_outputs/replication-claude \
  --cache research/explanation_fidelity/model_cache/claude-replication-v1
```

Expected complete batch shape: 18 result envelopes, two questions per episode, each containing one
physical call for F, G, and H: **54 physical calls total**. Existing outputs are skipped and cache
keys are content-addressed, so an interrupted batch may be resumed with the identical command. Do
not delete outputs, retry a failed logical call for cleaner language, or resample any successful
call.

The batch driver refuses evidence whose runtime-presentation or parity-audit hash differs from the
primary result. Every accepted result must report:

- `status = CLAUDE_ARM_SECONDARY_REPLICATION`;
- `single_sample_no_retry = true`;
- `evaluator_truth_available_to_methods = false`;
- `read_only_workspace_verified = true`;
- accepted information parity;
- the selected model and low effort;
- the pinned repository commit.

Do not open or summarize `outputs[].text`, raw provider responses, or cache response bodies during
collection. Operational inspection may cover file existence, schema, hashes, call counts, usage,
cost, workspace-integrity flags, parity flags, and G verifier/fallback metadata.

## Manifest, DVC publication, and Git checkpoint

After all 18 envelopes exist, build one arm-level artifact manifest:

```bash
python analysis/build_provenance_model_manifest.py \
  --output-root model_outputs/replication-claude \
  --cache-root research/explanation_fidelity/model_cache/claude-replication-v1 \
  --manifest manifests/model_outputs/provenance-claude-replication-arm-v1.json \
  --status CLAUDE_ARM_SECONDARY_REPLICATION
```

Verify all manifest hashes independently, run the full focused test command above, and update
`README.md`, `docs/EXPERIMENTS.md`, `docs/ANNOTATION_WORKFLOW.md`, and
`docs/MODEL_FAMILY_REPLICATION.md` with operational facts only. Preserve `NOT_ANNOTATED` and do not
calculate a sealed effect from unreviewed text.

Publish the new outputs and cache through DVC before committing their pointers:

```bash
scripts/update_dvc_tracking.sh
scripts/dvc_r2_sync.sh status
scripts/dvc_r2_sync.sh push
scripts/dvc_r2_sync.sh status   # must report cache and remote in sync
```

Then stage only the intended documentation, Claude arm manifest, and seven DVC pointer files. Never
stage raw governed payloads or credentials. Commit and push the umbrella repository. Check
`git diff --cached --name-status` immediately before every commit.

## Package evidence for independent annotation

Build a Claude-only blinded packet because response formatting can reveal the provider/harness:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src:analysis \
python analysis/build_blinded_annotation_packet.py \
  --arm claude=model_outputs/replication-claude \
  --packet model_outputs/annotation_packets/sealed-claude-v1/packet.jsonl \
  --key data/evaluator_only/annotation_keys/sealed-claude-v1.json
```

The packet should contain 54 model-condition responses; A--E smoke outputs are excluded by
default. Verify the packet/key hash relationship and leakage checks without reading response text.
Push both governed roots through DVC and commit refreshed pointers after the guarded upload.

This execution agent must **not** annotate the packet it generated or inspect the key while acting
as an annotator. Arrange two independent blinded annotation passes and a distinct adjudicator using
`docs/ANNOTATION_WORKFLOW.md`. Analyze by arm after adjudication; never pool primary and Claude
responses as independent episodes. If independent annotators are unavailable, record annotation as
`BLOCKED` or `NOT_RUN` and hand off the packet rather than substituting self-scoring.

## Completed on 2026-09-20

The assigned workstream is done. The sealed Claude arm holds 18 envelopes and 54 one-shot calls,
its manifest is built and independently re-hashed, and outputs, cache, packet, and key are pushed
to R2 with cache and remote reported in sync. The blinded packet
`model_outputs/annotation_packets/sealed-claude-v1/packet.jsonl` holds 54 model-condition responses
and matches its evaluator-only key by hash. **Annotation is `NOT_RUN` and is handed off**: the agent
that generated this packet must not annotate it.

Three operational facts corrected during execution, each recorded in `docs/DECISIONS.md` or an
amendment:

1. A condition-H call had cached a provider 429 spend-limit error as if it were an answer, which
   made that call permanently unrepeatable. The adapter now keeps answerless calls out of the answer
   cache and retains them under `_retained_failed_calls/`. See arm amendment 3.
2. A `dvc pull` can complete while leaving governed roots partly materialized. Refreshing pointers
   against that workspace silently *removed* the primary arm's `pn-0010`--`pn-0021` outputs and 72
   cache records from the snapshot. **Before running `update_dvc_tracking.sh`, confirm every
   governed root is fully checked out, and read the pointer diff for falling `nfiles`.** A pointer
   refresh after a collection run should only ever add files.
3. `data/evaluator_only/annotation_keys` was covered by no pointer and is now a governed root. The
   `sealed-luna-v1` key is present and matches its packet by hash, so the earlier "key not present"
   note is outdated; that packet still covers only 54 responses over nine episodes, so a fresh
   full-arm primary packet is still required.

## Scientific boundaries that must survive the handoff

- Configuration proves configured software semantics, not observed physical cause.
- Topic delivery does not prove controller consumption.
- Repeated messages are not unique recovery attempts; use unique invocation IDs.
- `goalAttempts` is not a recovery count.
- A node `FAILURE` is not automatically mission failure.
- Harness cancellation/deadline is not a BT timeout.
- Recorded-state replay is not counterfactual re-execution.
- A later failure does not retroactively change decision-time rationale.
- Conditions must receive evidence-matched information; evaluator-only intervention truth never
  reaches prompts, retrieval, filenames, or model-visible metadata.
- G's deterministic template fallback is part of the frozen method. Retain verification failures;
  do not prompt-tune them away.
- Claude-versus-primary differences conflate model family and agent harness. Report them only as a
  secondary sensitivity analysis, not a causal model-family comparison.

## After the Claude arm

The largest primary-study threat remains sample size: 21 episodes versus the frozen minimum of 40,
target 50, preferred 60. Once the requested Claude evidence is safely retained and packaged,
another batch of frozen independent episodes has higher expected paper value than architecture
work. Resume at `pn-0022` only if directed to continue primary collection, using the established
capture -> answer-blind inclusion -> evidence checkpoint/push -> one-shot calls -> manifest/push
order.

At every checkpoint report implemented work, empirical verification, independent episode counts,
development-only estimates separately from sealed results, exclusions, evidence/provenance gaps,
remaining validity threats, blocked work, and the next smallest executable action. Never claim a
run, annotation, DVC upload, or analysis that was not actually completed and verified.
