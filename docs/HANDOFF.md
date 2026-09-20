# Context-Free Agent Handoff

Copy the prompt below into a new agent session. It is deliberately self-contained enough for an
agent with no conversation history, while deferring canonical scientific details to versioned
repository documents.

---

You are taking over the TRUSTMORE 2026 CRANE explanation-fidelity project. Work from your local
checkout of the umbrella Git repository whose `origin` is
`https://github.com/1unarzDev/crane_explanation_fidelity.git`. Resolve paths from the repository
root rather than assuming any developer's absolute path. The hard paper deadline is
October 4, 2026 AoE. The scientific objective is trustworthy natural-language explanation of robot
navigation decisions and failures: captured evidence → supported propositions → language →
final-text verification. The primary failure mode is fluent but unsupported language.

Before acting, read these files in order:

1. `README.md`
2. `docs/STUDY_DESIGN.md`
3. `docs/ANNOTATION_GUIDE.md`
4. `docs/EXPERIMENTS.md`
5. `docs/DECISIONS.md`
6. `docs/ARCHITECTURE.md`
7. `docs/BENCHMARK.md`
7a. `docs/CLAUDE_REPLICATION_ARM.md` and
    `manifests/study/provenance-claude-replication-arm-v1.json` plus its amendments
7b. `docs/ANNOTATION_WORKFLOW.md`, the operational companion to the frozen annotation guide
8. `manifests/study/provenance-study-freeze-v1.json` and every adjacent amendment
9. `research/explanation_fidelity/experiment_configs/frozen/provenance-study-v1.json` and every
   adjacent amendment
10. `research/explanation_fidelity/dataset_splits/provenance-final-v1.json`
11. `manifests/workspace.lock.json`

Then inspect `git status`, `git log -5`, submodule/nested-repository heads, and the current remote
state. Preserve all existing work. Raw data and model outputs are ignored and must never be added to
Git; only hash/provenance manifests are committed. Keep `data/robot_visible/` and
`data/evaluator_only/` physically separate, and never expose evaluator-only truth to a model.

Current frozen study:

- Primary comparison: F versus G.
- F: raw robot-visible evidence plus exact repository checkout, given to a generic coding agent.
- G: structured runtime evidence plus exact runtime/source anchors, followed by checked planning,
  generation, final verification, and deterministic fallback where needed.
- H: structured runtime evidence plus unrestricted repository agent; this is a strong control.
- Frozen questions: “Why did the autonomy software enter recovery?” and “Did a physical obstacle
  cause the navigation failure?”
- Frozen model: `gpt-5.6-luna`, low reasoning, one call per condition/question, no retries or
  resampling. This is the primary arm and is unchanged.
- A **secondary Claude replication arm** re-runs F/G/H over the same nine retained episodes with a
  Claude model, because the sandboxed Codex CLI session that made the sealed calls is unavailable on
  later hosts. It is separately reported, physically separated in every namespace, adds no
  independent episodes, and never amends the freeze. Read `docs/CLAUDE_REPLICATION_ARM.md` before
  touching it.
- Collection target: 40 included independent episodes minimum, 50 target, 60 preferred, balanced
  between recovery-success and terminal-abort families.
- Do not inspect or annotate sealed answers for scoring until blinded dual-annotator packaging is
  ready. A–E entries inside F/G/H envelopes are deterministic smoke outputs, not final model
  evaluations. A–E final evaluation remains `NOT_RUN`.

Current sealed state as of the end of September 19, 2026:

- `pn-0001` through `pn-0009` were each captured once, passed the frozen inclusion validator, were
  checkpointed, and have pushed data and model-artifact manifests.
- Recovery-success: `pn-0001`, `pn-0003`, `pn-0005`, `pn-0007`, `pn-0009`.
- Terminal-abort: `pn-0002`, `pn-0004`, `pn-0006`, `pn-0008`.
- Exclusions: zero. Sealed F/G/H calls retained: 54 total. No sealed annotation or effect estimate
  exists.
- Latest expected umbrella commits: capture checkpoint `30587db`, followed by a closeout commit
  containing the `pn-0009` model manifest, experiment log, and this handoff. Confirm rather than
  assuming hashes.
- The user asked to close the current work session, so do not start `pn-0010` merely because this
  handoff exists. Resume collection only when the user explicitly asks. When resumed, `pn-0010` is
  the next frozen row; never skip or rerun rows to obtain favorable outcomes.

Five transparent freeze amendments correct operational issues discovered before or during early
collection. The most recent fixes the exact pinned fixture variable
`CRANE_EXPECTED_NAV_STATUS`. Do not hide or rewrite amendment history. `pn-0002` and `pn-0004` were
validly retained without rerun because the defect affected only an evaluator-side outer expected
status, not their captured dynamics or terminal result.

Before any resumed collection, run the established CPU-only checks:

```bash
export PYTHONPATH=packages/astro_dock/src/crane_explain/src:packages/astro_dock/src/crane_explain_ros
python -m pytest -q tests packages/astro_dock/src/crane_explain/tests
scripts/check_data_governance.sh
```

Also run the analysis-side suite, which now includes the freeze-integrity check:

```bash
PYTHONPATH=packages/astro_dock/src/crane_explain/src:analysis python -m pytest -q analysis
```

`analysis/test_freeze_integrity.py` verifies all 32 hash-frozen files against the base freeze plus
its five amendments, applied in amendment order. Never edit a frozen file — including
`docs/STUDY_DESIGN.md`, `docs/ANNOTATION_GUIDE.md`, the prompts, and
`analysis/run_provenance_agent_pilot.py` — without writing an amendment that records the new hash.
Extend by addition instead; the Claude arm is the worked example.

**Capture requires Linux.** New episodes need a Linux x86_64 Unity player at
`packages/crane_ml/Builds/CRANE-Worker/CRANE.x86_64` and the pinned CUDA ROS image under a running
Docker daemon. On a host without those — an arm64 macOS machine, for instance — collection is
BLOCKED and no amount of retrying will change that. The model arms, the annotation workflow, and
the analysis code all run fine on such a host, because every sealed capture is retained locally.

Do not treat a blanket host-shell `python -m pytest -q` as the project test command: it traverses
ROS packages whose ament dependencies require the Jazzy environment. Use the documented ROS/colcon
environment for ROS package tests.

If collection is explicitly resumed, execute exactly one next frozen row with
`scripts/run_frozen_provenance_episode.py EPISODE`, retain the first outcome, derive the two cases,
build both F/G/H parity packets and Nav2 provenance, and run
`analysis/validate_frozen_provenance_episode.py` before any model call. If included, run
`scripts/checkpoint_validated_run.sh` and push the capture manifest commit first. Then make exactly
six sealed calls (F/G/H × two questions) with the frozen model/configuration, build
`manifests/model_outputs/EPISODE-provenance-v1.json`, update `docs/EXPERIMENTS.md`, commit, and push.
The previous episode entries and script `--help` output provide exact argument patterns. Never rerun
an episode, retry a call, or weaken a gate to obtain a cleaner result.

The next high-value work after collection is not more infrastructure. Build a blinded response
packaging and dual-annotation workflow based on `docs/ANNOTATION_GUIDE.md`, without exposing
condition labels or evaluator-only intervention identity. Only then score sealed responses and run
the prespecified episode-clustered analysis. Continue collection toward 40 only when authorized;
the current sample of nine is far below the frozen minimum and cannot support the primary claim.

Important scientific constraints:

- Configuration presence does not prove a configured mechanism caused an observed failure.
- Topic delivery does not prove controller consumption.
- Temporal order does not establish physical causation.
- Goal attempts, feedback publications, RecoveryNode cycles, and duplicate messages are not unique
  recovery attempts; use unique invocation IDs.
- A later failure does not rewrite decision-time evidence.
- Prefer partial supported answers or abstention over unsupported specificity.
- Do not add a C++ BT hook unless a documented paper-critical evidence gap survives narrowing the
  claim and cannot be filled through existing ROS/action/introspection interfaces.
- H matching or beating G, templates beating LLM realization, or a null/negative result are valid
  scientific outcomes.

At the end of your session, report statuses using `IMPLEMENTED`, `TESTED`, `NOT_RUN`, `BLOCKED`, or
`DEFERRED`; list changed files, tests, data/sample count, exclusions, unresolved validity threats,
and the next smallest executable task. The largest current threat is sample size: nine included
episodes versus a frozen minimum of 40. Other open limitations are unproven Unity-player
source-to-binary identity, A–E final model evaluation not run, and no sealed annotations,
statistics, figures, or manuscript results.

---
