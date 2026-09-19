# Architecture

## Trust boundary

The core transforms immutable episode evidence into explicitly supported propositions. A language
realizer may only express those propositions and explicit limitations. The final text—not merely
the internal plan—is checked. On failure, one bounded repair may be attempted by a future LLM
adapter; otherwise the deterministic checked answer is returned.

Decision-time evidence and later outcomes are physically separate fields. Changing an outcome
cannot change a decision rationale. Candidate state distinguishes selected, evaluated/rejected,
infeasible, known-not-considered, and unknown. `not_considered` is used only when recorded.

## Evidence flow

1. CRANE/run harness supplies episode, run, tick, sensor/observation identity, and explicit client
   cancellation/deadline events.
2. The ROS observer records Nav2 action goal/feedback/result and BT status transitions, plus the
   exact BT XML/version. It does not infer internal consumption from nearby topic values.
3. The core validates identity, chronology, completeness, candidate, and policy invariants.
4. Reasoning constructs claims with evidence IDs, derivation, temporal scope, assumptions, support
   status, and evidence level.
5. A realizer emits language; the verifier checks final sentences. Unverified language falls back
   to templates.
6. Evaluation compares responses with evaluator-only truth stored outside all model-visible paths.

The validated CRANE aquatic fixture must retain a real windowed Vulkan render loop: HDRP water
queries are not valid under `-batchmode` or `-nographics`. The `train-gpu` profile disables
spectator cameras but retains a task sensor camera, so the window is not a presentation view and a
short 0.5 m goal may appear nearly stationary. Primary high-throughput land collection should use
the non-aquatic `train-cpu` path rather than weakening aquatic physics or sensors.

The land vertical slice uses the existing PhysX `AckermannRoverDynamics`, a fixed-step stamped ROS
command adapter, authoritative odometry/TF, and a runtime-mounted 2D laser in a deterministic
corridor. `run_land_nav2_fixture.sh` explicitly selects `Land Vehicle Validation`, `train-cpu`,
`-batchmode`, and `-nographics`. It does not grant Ackermann vehicles an unphysical turn-in-place;
recovery behavior must respect that embodiment. Corridor parameters written by the runtime
bootstrap are evaluator-only and must never enter explanation prompts.

## Evidence levels

1. recorded sequence;
2. reconstructed software execution mechanism from BT semantics plus transitions;
3. explicit-model causal inference;
4. controlled-intervention result.

The initial submission targets levels 1–2. Temporal succession is not physical causation.

## Boundaries

- **CRANE:** simulation truth, episode identity, observations, action application, later outcomes.
- **Nav2:** planner/controller/behavior/BT execution. BT transitions show software mechanism.
- **ROS capture:** passive serialization only; it must not rewrite history or invent consumption.
- **Core:** schema, validation, checked reasoning, answerability, generation policy, verification.
- **LLM:** optional realization/extraction component, never the trust boundary.
- **Evaluator truth:** fault injection and gold propositions, inaccessible to explanation methods.

## Reproducibility workspace

The umbrella repository owns documentation, locks, configs, analysis, paper sources, and global
scripts. `packages/astro_dock` and `packages/crane_ml` are Git submodules, so every umbrella commit
pins their exact Git objects. `scripts/setup_workspace.sh` fetches astro_dock's nested dependencies
and checks out separately pinned explanation packages under `packages/astro_dock/src`.

Raw artifacts are never Git inputs. Robot-visible and evaluator-only files occupy separate ignored
directory trees. Committed manifests contain only paths, hashes, sizes, provenance, and run-level
metadata. A validated-run checkpoint refuses dirty components or staged governed data before
committing updated locks and submodule pointers.

## Why no C++ BT hook

The locally installed Jazzy packages (`nav2_msgs` and `nav2_bt_navigator` 1.3.12) expose
`BehaviorTreeLog` and `NavigateToPose` feedback/result. The installed `RosTopicLogger` publishes
node name, UID, previous status, and current status on `behavior_tree_log`; feedback exposes
navigation time, ETA, recovery count, and distance remaining. The static BT XML supplies control
semantics. This is enough to pilot levels 1–2 without changing Nav2.

A narrow hook is reconsidered only after a documented pilot evidence gap blocks a primary RQ,
cannot be observed elsewhere, cannot be handled by narrowing the claim, and is worth more than
additional independent episodes.
