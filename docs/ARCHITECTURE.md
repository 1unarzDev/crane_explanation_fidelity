# Architecture

## Reference-environment layers

Reference scenes separate authoritative `CanonicalGeometry` colliders and semantic IDs from robot
physics/ROS/sensors and from `VisualPresentation`. Renderer upgrades cannot silently change task
feasibility. Semantic IDs are provenance handles, not proof of sensing or controller consumption;
generated explanations still require robot-visible support.

Gazebo reference environments are converted offline. Hash-tracked generated assets and scenes are
excluded from Git; editor tooling constructs separate canonical collision and presentation trees
from a manifest. Runtime SDF loading is intentionally absent. Generated world semantics remain
evaluator-side unless a captured sensor/decision record makes them robot-visible.

## Trust boundary

The core transforms immutable episode evidence into explicitly supported propositions. A language
realizer may only express those propositions and explicit limitations. The final text—not merely
the internal plan—is checked. On failure, one bounded repair may be attempted by a future LLM
adapter; otherwise the deterministic checked answer is returned.

Decision-time evidence and later outcomes are physically separate fields. Changing an outcome
cannot change a decision rationale. Candidate state distinguishes selected, evaluated/rejected,
infeasible, known-not-considered, and unknown. `not_considered` is used only when recorded.

The method has two separate evidence planes:

- **runtime/physical evidence:** decisions, candidate states/scores, BT transitions, action
  results, unique action/recovery invocations, timestamps, poses, paths, observations, commands,
  and explicit completeness gaps;
- **source evidence:** the exact code, BT XML, policy, and configuration governing a runtime event,
  identified by repository/commit or package version, artifact content hash, file, symbol or XML
  locator, bounded source span, and relevant configuration keys.

A nearby topic sample is not automatically a consumed decision input. A plausible function found
in a repository is not automatically the function that governed an observed event. Both
relationships require retained provenance, and unresolved provenance remains explicit.

## Model boundary and replication arms

The evidence, reasoning, verification, and evaluation layers are provider-neutral. They exchange a
logical model-call request and a retained `crane-explain-model-call/v1` record; they do not depend
on a GPT- or Claude-specific SDK. A provider adapter owns only invocation concerns: model/settings,
schema delivery, raw response parsing, content-addressed caching, CLI/API identity, normalized
usage, cost availability, latency, and workspace-integrity attestations.

A model-backed condition composes four identities that must not be collapsed into the word
“model”:

1. model configuration (family/version, reasoning and sampling settings);
2. provider adapter (CLI/API translation and retained record);
3. agent harness (system framing, tools, repository access, permissions);
4. method condition (F, G, H, or another declared explanation procedure).

This decomposition permits another model family to reproduce the comparison without changing the
evidence schema or trust boundary. It does not imply that provider interfaces are equivalent. Each
arm records schema-delivery, sandbox/tool, network/delegation, workspace-isolation, parsing,
telemetry, and cost capabilities. A provider-specific adapter may strengthen operational isolation,
but it may not alter frozen prompts, evidence, condition semantics, or verification policy.

The current primary arm uses the Codex CLI adapter. The Claude-family adapter is a worked secondary
arm and emits the same normalized call schema. Because its F/H agent program differs, that arm
tests sensitivity to model family plus harness, not model weights alone. Future local/open-weight,
API, or CLI models fit through the same adapter contract and require a separately declared arm,
matched within-family model-strength control, disjoint artifact namespace, and explicit capability
profile. See `MODEL_FAMILY_REPLICATION.md`.

The hash-frozen primary runner still constructs its Codex caller directly. It is preserved as an
experimental artifact, not presented as the ideal reusable interface. The additive Claude runner
imports its frozen condition logic and substitutes a normalized caller. A future non-frozen runner
should inject the caller protocol; changing the frozen runner solely for code elegance would damage
reproducibility without changing the study.

## Evidence flow

1. CRANE/run harness supplies episode, run, tick, sensor/observation identity, and explicit client
   cancellation/deadline events.
2. The ROS observer records Nav2 action goal/feedback/result and BT status transitions, plus the
   exact BT XML/version. Final-study captures also retain an immutable runtime manifest containing
   the actual Nav2 parameter-file hash/Git object, harness hashes, container digest, installed Nav2
   package versions, checkout identities, player hashes, and effective scene/command/LiDAR launch
   settings. Intervention identity/timing and evaluator truth are explicitly excluded. A configured
   parameter still does not prove it caused a particular failure or that a controller consumed a
   nearby observation.
3. A deterministic runtime-presentation builder preserves accepted goal/result identity, exact BT
   transition IDs/UIDs/statuses/timestamps, feedback summaries, BT XML identity, limitations, and
   separately scoped completeness. Each field retains compact raw-record derivation provenance.
   Before F/G/H calls, a question-specific audit proves that F can derive every required unit from
   its raw capture and that G/H receive the same structured runtime value. Source links and checked
   plans are explicitly excluded as G's treatment, not mislabeled as shared runtime facts.
4. A provenance resolver follows runtime anchors to exact retained artifacts. It retrieves the
   defining node/symbol/configuration first, then directly relevant parents/callers only as needed;
   unrestricted repository search is a separately evaluated baseline.
5. The core validates identity, chronology, completeness, candidate, policy, artifact hash, source
   anchor, and runtime-to-source link invariants.
6. Reasoning constructs claims with evidence IDs, source-anchor IDs, derivation, temporal scope,
   assumptions, support status, and claim class.
7. A provider adapter invokes an optional realizer. The verifier checks final sentences against
   both evidence planes independently of the model provider. Unverified language falls back to
   templates.
8. Evaluation compares responses with evaluator-only truth stored outside all model-visible paths.

The source retrieval order is runtime event → exact source/configuration anchor → minimal
relevant span → directly relevant parent/caller/configuration → broader search only when the
bounded context is demonstrably insufficient. Every retrieved span is retained for audit.

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

The land harness requires populated Nav2 costmap evidence. Jazzy's per-source LaserScan height
limits are explicit, and bounded snapshots use the stock `GetCostmap` service because advertised
full-map topics did not deliver in the isolated fixture. Topic-message and service-snapshot counts
remain separate. A service snapshot is observable Nav2 state, not a specific controller-consumed
input.

## Evidence levels

1. recorded sequence;
2. reconstructed software execution mechanism from BT semantics plus transitions;
3. explicit-model causal inference;
4. controlled-intervention result.

The initial submission targets levels 1–2. Temporal succession is not physical causation.

Claims also carry an orthogonal semantic class:

- `OBSERVED`: direct runtime or physical evidence;
- `DERIVED`: deterministic calculation or ordering over evidence;
- `SOURCE_DEFINED`: exact running code/configuration establishes the stated behavior;
- `MECHANISM_SUPPORTED`: runtime evidence and source semantics jointly establish the mechanism;
- `HYPOTHESIS`: plausible but unestablished diagnosis;
- `INTERVENTION_SUPPORTED`: a controlled intervention demonstrates the stated effect.

The initial study targets the first four classes. A hypothesis must never be silently promoted to
a factual or causal explanation.

## Boundaries

- **CRANE:** simulation truth, episode identity, observations, action application, later outcomes.
- **Nav2:** planner/controller/behavior/BT execution. BT transitions show software mechanism.
- **ROS capture:** passive serialization only; it must not rewrite history or invent consumption.
- **Core:** schema, bounded provenance resolution, validation, checked reasoning, answerability,
  generation policy, and verification.
- **Model provider/adapter:** optional realization or extraction mechanism, never the trust
  boundary; provider capabilities and agent harness are retained experimental factors.
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
