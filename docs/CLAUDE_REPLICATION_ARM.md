# Secondary Claude replication arm

This document governs the Claude-family replication of the F/G/H provenance comparison. It is a
**secondary, separately reported arm**. It does not amend, replace, reinterpret, or extend the
frozen study, and it does not add a single independent episode to the sample.

The authoritative machine-readable declaration is
`manifests/study/provenance-claude-replication-arm-v1.json`, written and committed before the arm's
first model call. Where this document and that manifest differ, the manifest governs.

## Why the arm exists

The sealed study's 54 retained model calls were made from a sandboxed Codex CLI session against
`gpt-5.6-luna` at low reasoning. That session is not available on the current host, and neither is
the capture stack: new episodes need a Linux x86_64 Unity player and the pinned CUDA ROS image, and
the working host is arm64 macOS with no player build and no running Docker daemon.

What *is* present is everything the model arm needs. All nine sealed captures, their provenance
bundles, parity audits, and runtime presentations are retained, and `packages/crane_ml` is checked
out at the pinned commit `c559932a5ebef00bfa7752511799fd904e5c9dbe`. So the model arm can be re-run
against a different model family over byte-identical evidence without recapturing anything.

That makes a real question answerable: does the F/G/H contrast survive a change of model family and
agent harness? RQ4 claims a method effect, not a model effect. An effect that appears only under
one vendor's model is a weaker claim than one that reproduces, and either outcome is worth
reporting.

## What stays frozen

Every hash-frozen artifact is byte-unchanged, including `docs/STUDY_DESIGN.md`,
`docs/ANNOTATION_GUIDE.md`, all five prompt files, and `analysis/run_provenance_agent_pilot.py`.
The arm extends the repository by **addition only**:

- `analysis/claude_cli_caller.py` — the Claude Code CLI adapter.
- `analysis/run_provenance_claude_arm.py` — a sibling of the frozen runner that imports its shared
  logic instead of editing it.
- `scripts/run_claude_arm_batch.py` — the batch driver.
- `analysis/summarize_claude_arm_model_strength.py` — the arm's model-strength selection rule.

`analysis/test_freeze_integrity.py` checks all 32 frozen hashes against the base freeze plus its
five amendments, applied in amendment order, so an edit to a frozen file fails the suite instead of
passing unnoticed. Note that alphabetical globbing does **not** produce amendment order:
`-amendment-N.json` sorts before `.json`, so a naive glob lets the base freeze overwrite the
corrections and reports three false mismatches.

Because `docs/STUDY_DESIGN.md` is frozen, the arm is documented here and in the ledger rather than
by editing that file. Its "Model-strength control" section continues to describe the frozen Luna
selection, which remains accurate for the primary study.

## Data separation

No Claude artifact shares a path, filename, cache, manifest, annotation file, or analysis result
with the frozen Luna arm.

| Artifact | Frozen Luna arm | Claude arm |
| --- | --- | --- |
| Sealed results | `model_outputs/final/` | `model_outputs/replication-claude/` |
| Sealed cache | `model_cache/final-provenance-v1/` | `model_cache/claude-replication-v1/` |
| Model manifests | `pn-XXXX-provenance-v1.json` | `pn-XXXX-provenance-claude-v1.json` |
| Control results | `model_outputs/dev/provenance-model-strength-luna-v1/` | `model_outputs/dev/provenance-model-strength-claude-v1/` |
| Control cache | `model_cache/provenance-model-strength-luna-v1/` | `model_cache/provenance-model-strength-claude-v1/` |
| Result envelope | `crane-explain-provenance-agent-pilot/v1` | `crane-explain-provenance-claude-arm/v1` |

Result envelopes additionally carry `arm`, `adapter`, and a `status` drawn from a disjoint
vocabulary (`CLAUDE_ARM_*` rather than `SEALED_TEST`), so a Claude result cannot be mistaken for a
frozen one even in isolation.

The batch driver refuses to run unless the retained runtime-presentation and parity-audit hashes
for an episode match the corresponding frozen Luna result exactly. The two arms are therefore
guaranteed to have been shown the same evidence, and this is checked rather than asserted.

## Adapter differences

These are real differences, not cosmetic ones, and they are recorded in every retained request.
Schema delivery is deliberately *not* among them: the Claude Code CLI's `--json-schema` flag is the
direct analogue of the Codex CLI's `--output-schema`, so the frozen prompt text reaches the model
byte-unchanged in both arms. An earlier adapter revision appended the schema to the prompt instead,
which both altered a hash-pinned prompt and failed outright when a model answered in prose;
`manifests/study/provenance-claude-replication-arm-v1-amendment-1.json` records that correction,
and the 16 calls made under it are retained but excluded from every summary.

1. **Read-only enforcement.** The Codex CLI enforces a read-only filesystem sandbox. The Claude
   Code CLI exposes no equivalent flag. The adapter therefore denies every mutating, network, and
   delegation tool (`Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `Task`, and others),
   runs only inside a throwaway extraction of the pinned checkout, and hashes the entire workspace
   before and after each call. A call whose workspace hashes changed is retained and raised, never
   scored. This is a weaker guarantee than a kernel sandbox and is listed as a validity threat.
2. **Agent harness.** F and H are "a generic read-only coding agent", and the two arms use
   different agent programs: `codex exec` versus the Claude Code CLI, which carries its own system
   prompt and a `Read`/`Glob`/`Grep`/`Bash` tool surface. Model family and agent harness are
   therefore **confounded** in this arm. A difference between arms cannot be attributed to model
   weights alone.
3. **Cost reporting.** The Claude Code CLI reports provider monetary cost; the Codex ChatGPT-login
   path did not. Cost is reported for this arm and remains unavailable for the Luna arm, so no
   cross-arm cost comparison is made.

## G is largely deterministic, so the arm mostly tests F and H

Condition G makes one realization call and replaces it with the deterministic checked template
whenever a single final sentence is not exactly licensed by the checked plan. In the frozen Luna
development control, seven of eight G responses fell back to the template. The template is a pure
function of the checked plan, and the plan is a pure function of the same retained evidence, so
those seven G responses are **byte-identical across arms** — verified for e019 `failure-cause`,
where the Luna and Claude texts match exactly.

Two consequences follow, and both should be stated wherever arm results are reported:

- A cross-arm difference in G reflects only how often the realization call passed verification, not
  differences in the answers G ultimately gave.
- The arm's real content is the F and H contrast. That is the right place to look for whether the
  RQ4 effect is model-family dependent, and it also sharpens the harness confound noted above,
  since F and H are precisely the conditions where the agent program differs.

Where a G response is byte-identical to its Luna counterpart, it is scored identically. Scoring the
same text two different ways would silently change the rubric between arms.

## Observed answer-format difference

Under the frozen prompt and the same `{"answer": string}` schema, the Claude models frequently fill
`answer` with a serialized JSON object — nested keys such as `observed_runtime_evidence` and
`evidence_not_present` — where the Luna arm produced prose. Both satisfy the schema, and the
frozen prompt says only "Give a concise, substantive answer as JSON matching the supplied schema",
so this is a model-behavior difference and not an adapter defect. It is recorded rather than
prompt-tuned away, because tuning the prompt to equalize style is exactly the post-hoc adjustment
the freeze forbids.

It has one practical consequence: **do not pool the two arms into a single blinded packet.** Answer
format would identify the arm at a glance and defeat the blinding. The packager supports pooling,
and the key keeps pooled arms separable, but per-arm packets are the default for this reason.

## Model-strength control

The frozen study forbids giving G a stronger model than its baselines, and selected Luna over Sol
under a predeclared four-episode rule. The Claude arm repeats that procedure rather than skipping
it.

The control is predeclared in
`research/explanation_fidelity/experiment_configs/development/provenance-model-strength-claude-20260920-v1.json`.
It compares `claude-sonnet-5` against `claude-haiku-4-5-20251001`, both at low effort, over the same
four **development** episodes the frozen control used (e019, e021, e037, e038), two questions and
three conditions each: 24 calls per setting. No sealed episode is used for selection, and the
selected setting is fixed before the first sealed Claude call and not revisited afterwards.

The four eligibility margins are the frozen ones, evaluated strictly within the Claude arm: at most
one additional material-error response out of eight per condition against the best tested Claude
setting; aggregate specificity within 10 points; at most one additional unsupported source
attribution or causal overclaim across all 24 responses; and substantive coverage at least 0.875
per condition. Among eligible settings the least expensive is chosen, now on reported monetary cost
rather than on tier and tokens. If the lower tier is ineligible, `claude-sonnet-5` is retained.

### Outcome: the lower tier was rejected

| setting | F errors /8 | G | H | aggregate specificity | cost | input tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `claude-haiku-4-5` | 7 | 0 | 1 | 117/156 | $2.42 | 8.75M |
| `claude-sonnet-5` | 1 | 0 | 0 | 135/156 | $1.77 | 2.08M |

Substantive coverage was 1.0 for every condition in both settings. Haiku failed the per-condition
margin outright, so **`claude-sonnet-5` at low effort is the arm's model**, fixed before the first
sealed Claude call.

Two things are worth stating plainly. First, Haiku's errors were concentrated almost entirely in
**F**, the strong repository-agent baseline. Using it would have inflated the very F-versus-G
contrast this arm exists to examine — which is precisely the confound the model-strength control
exists to prevent, and the reason the arm does not simply adopt the cheaper tier. Second, the lower
tier was not in fact cheaper here: its F agent consumed 8.75M input tokens against 2.08M, so it was
slower and costlier as well as less accurate. No cost comparison is made against the Luna arm,
whose provider cost was never reported.

Haiku's failures are the ones the guide names: `SimpleProgressChecker` given as a confirmed root
cause from a parameter file with no controller error payload; guard SUCCESS read as a diagnosis;
"PROBABLE, HIGH confidence" on physical cause; and a wrong duration (~20 ms for a recorded 10.02 s
FollowPath interval). Sonnet's single error is an opening figure contradicting its own timeline.

Because all sixteen G responses are byte-identical to the frozen arm's, the control discriminated
between settings only through F and H. Annotation was unblinded, single-annotator, development-only
and performed by an automated session; that is weaker than the blinded dual annotation the sealed
analysis requires, and is recorded as a limitation rather than presented as equivalent.

## What this arm can and cannot claim

**Can:** whether the direction and rough magnitude of the F/G/H contrast on these nine retained
episodes reproduce under a different model family and agent harness; descriptive sensitivity of the
primary comparison to model family; resource evidence for the Claude family on identical inputs.

**Cannot:**

- Any increase in independent sample size. These are the same nine episodes. The two arms are not
  eighteen clusters and must never be pooled as independent observations.
- Any equivalence, superiority, or inferiority claim between model families. Single-sample, no
  power analysis, and the harness confound above.
- Any replacement of the frozen primary result. If the arms disagree, both are reported.
- Any relief from the frozen 40-episode minimum, which is unmet at nine included episodes.

## Sealed-answer discipline

Claude-arm sealed answers obey the same rule as the Luna arm: retained and hashed, but not
inspected or scored until the blinded dual-annotation workflow runs. Development control responses
may be annotated, unblinded and by a single annotator, exactly as the frozen control was.

## Reproducing the arm

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e 'packages/astro_dock/src/crane_explain[dev]'

# development model-strength control, one setting at a time
scripts/run_claude_arm_batch.py --batch development \
  --model claude-haiku-4-5-20251001 \
  --output-root model_outputs/dev/provenance-model-strength-claude-v1/haiku \
  --cache research/explanation_fidelity/model_cache/provenance-model-strength-claude-v1

# sealed replication over the nine retained episodes, using the selected model
scripts/run_claude_arm_batch.py --batch sealed --model SELECTED_MODEL \
  --episodes pn-0001 pn-0002 pn-0003 pn-0004 pn-0005 pn-0006 pn-0007 pn-0008 pn-0009 \
  --output-root model_outputs/replication-claude \
  --cache research/explanation_fidelity/model_cache/claude-replication-v1
```

Calls are content-addressed, so an interrupted batch resumes without resampling. Existing result
files are skipped rather than overwritten; no episode is ever rerun to obtain a cleaner outcome.
