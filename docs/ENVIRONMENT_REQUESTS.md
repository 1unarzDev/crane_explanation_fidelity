# Environment Requests

These contracts let environment work proceed in parallel without exposing evaluator truth to the
explanation system. Build the smallest geometry that satisfies each contract. Do not add visual
detail, new perception stacks, or competition semantics unless the contract requires them.

Implementation checkpoint (2026-09-19): the smallest headless corridor, deterministic walls,
optional blocker windows, TurtleBot3 differential and Ackermann bodies, evaluator-only geometry,
LiDAR, odometry, TF, populated Nav2 costmaps, and deterministic mobility hold/release are
implemented. e019 validates one recovery-success path; existing e004/e009 validate terminal
recovery exhaustion. Multi-seed reset/determinism and paired final-collection variants remain open.

## REQUIRED — generated land corridor navigation

- **Scientific purpose:** high-throughput primary benchmark for software-level recovery,
  termination, evidence sufficiency, and selective explanation. This is the powered study; it is
  not a claim about a new navigation policy.
- **RQs:** RQ1–RQ4. It primarily exercises execution recovery (motif C), terminal failure (D), and
  evidence insufficiency (F).
- **Robot embodiment:** the validated CRANE TurtleBot3 Waffle-class differential body for the
  powered corridor study. Retain Ackermann/F1TENTH as embodiment-specific stress tests rather than
  mixing their controller/plant behavior into the primary family.
- **Current CRANE substrate:** **IMPLEMENTED/DEVELOPMENT-TESTED.** The existing TurtleBot3 scene
  retains its differential dynamics, ROS bridge, LiDAR, semantic identity, and reference geometry;
  corridor runs replace only the environment root. The graphics-free fixture records odometry/TF,
  stamped commands, LaserScan, populated costmaps, evaluator-only interventions, and exact BT/action
  evidence. e015 validates unblocked success and e019 validates one recovery followed by success.
  Reset reproducibility, collision-contact truth, and powered independent-seed collection remain
  incomplete, so this is not yet the final-collection contract.
- **Runtime:** non-aquatic `train-cpu`, graphics-free when supported. Do not use the aquatic
  `Roboboat Course` as the high-throughput primary environment: its HDRP water requires a real
  windowed Vulkan loop.
- **Autonomy stack:** stock pinned Nav2 planner, controller, BT navigator, recovery behaviors, and
  lifecycle manager. Do not change the navigation algorithm for this study.
- **Decision/failure explained:** why Nav2 entered recovery, replanned, succeeded, was canceled by
  the client deadline, or terminated with a planner/controller/progress failure. Physical obstacle
  causation is evaluator-only unless an explicit consumed-input link is implemented.

### Minimal geometry and controlled variation

Create a deterministic rectangular course generator with:

1. a fixed family of start/goal pairs;
2. a straight or gently turning corridor;
3. parameterized corridor width;
4. one optional blocking obstacle controlled through a ROS service or episode configuration;
5. deterministic obstacle lateral position and size from a recorded seed;
6. enough free space for an unblocked success condition;
7. variants that yield success, replan/recovery then success, and terminal stuck/no-path outcomes.

The first implementation need not resemble an official competition course. Use primitive
colliders and stable materials. Do not implement cameras, semantic detection, manipulation,
payloads, or water.

### Independent and controlled variables

- **Manipulated:** seed; start/goal member; corridor width; blocker absent/present; blocker
  insertion time; blocker clearance; recovery budget where already configurable in Nav2; client
  deadline; evidence mask applied after capture.
- **Controlled:** robot model/mass; controller and planner parameters; BT XML; physics step; sensor
  rates; map resolution; start/goal within each paired variant; software/image/component commits.
- **Paired variants:** same seed/start/goal with blocker absent versus present; same blocker with
  sufficient versus insufficient clearance; recovery succeeds versus budget/deadline exhausted;
  full versus deliberately truncated recovery history; relevant evidence omitted versus unrelated
  telemetry omitted.
- Do not label these variants counterfactuals unless both interventions are actually executed.

### Evidence boundary

Robot-visible evidence may contain only:

- LiDAR messages and their stable observation identities;
- odometry and TF identities, labeled as delivered unless consumption is proven;
- Nav2 `BehaviorTreeLog` transitions;
- NavigateToPose goal, feedback, result/error, and status;
- exact BT XML and hashes of Nav2/configuration files;
- planner/controller/behavior observable results;
- explicit harness deadline/cancel/blocker-command events;
- opaque episode, run, seed, tick, action, and recovery-attempt identifiers.

Evaluator-only truth must be written under a physically separate output root and must contain:

- obstacle geometry and insertion state/time;
- collision contacts;
- exact start/goal and success region;
- injected fault identity;
- ground-truth termination classification;
- expected answerability and gold propositions.

Never place `blocked`, `fault`, `collision`, scenario outcome, or gold labels in robot-visible
filenames, topic names, opaque IDs, prompts, or retrieval metadata. The recorder must not mount the
evaluator-only root.

### Predicates and transitions

- **Success:** NavigateToPose returns success and evaluator truth confirms the robot entered the
  goal tolerance without collision.
- **Planning failure:** planner observable result/BT transition reports failure; do not infer the
  physical cause from that event alone.
- **Controller/progress failure:** controller/progress observable result/BT transition reports
  failure with a unique action identity.
- **Recoverable failure:** a failed planning/controller branch is followed, according to the exact
  BT semantics, by an eligible recovery transition and later task success.
- **Terminal failure:** NavigateToPose returns an abort/error after the configured recovery path is
  exhausted.
- **Client deadline:** the harness publishes a deadline and cancel event; label it distinctly from
  BT/task timeout and mission failure.

### Reset and determinism

- One command must reset robot pose/velocity, obstacle state, Nav2 costmaps, episode counters, and
  random generator state without leaving prior commands in queues.
- The reset response must return opaque episode ID, seed, initial tick, and configuration hash.
- Repeating a seed/configuration three times must reproduce obstacle geometry and start/goal.
  Trajectory equality is not required, but nondeterminism must be measured.
- A new episode must reject stale or cross-episode commands and expose those rejection counts.

### Required telemetry and IDs

- Monotonic simulation tick and ROS timestamp at episode start/end and fault intervention.
- Unique NavigateToPose goal ID and unique recovery-action attempt IDs where observable.
- Planner/controller/behavior node name and BT UID/status transition.
- Observation sequence/acquisition tick for LiDAR and odometry.
- Configuration, map, BT XML, simulator build, and component Git hashes.
- Capture completeness marker and explicit dropped/invalid message counts.

### Supported questions

- What occurred immediately before recovery?
- Why did the software enter the recovery branch?
- How many distinct recovery attempts are recorded, and is the history complete?
- Why did the task terminate?
- Did the client cancel the task or did Nav2 abort it?
- What robot-visible evidence preceded replanning?
- Does the evidence establish the physical reason the planner/controller failed?
- What can still be said when recovery history or relevant observations are omitted?

The system must decline or qualify:

- “The obstacle caused the failure” without a supported consumed-input or intervention link;
- “another route would have succeeded” without actual re-execution/model evidence;
- “both retries failed” when two unique attempts are not recorded;
- any claim that delivered LiDAR/odometry was consumed internally merely because it was nearby in
  time.

### Fault-injection API

Provide a ROS service/action or launch configuration supporting: `reset(seed, variant)`,
`set_blocker(enabled, tick_or_time)`, and `query_episode_identity()`. Commands and acknowledgements
must carry episode ID and simulation tick. The robot-visible stream records only that an authorized
environment intervention occurred when such visibility is part of the scenario; detailed geometry
and intended fault class remain evaluator-only.

Current increment: CRANE accepts `--crane-land-blocker-remove-after SECONDS` for a blocker created
by the existing land corridor bootstrap. The boundary is measured from the scene's deterministic
fixed simulation clock, not goal acceptance. The configured offset, scheduled simulation time,
actual removal time, geometry, and semantic ID are written only to the evaluator-owned truth file;
the collider and renderer are deactivated as one authoritative object. Corridor walls and the
blocker now carry stable semantic IDs. This is **IMPLEMENTED / RUNTIME-TESTED**. The first timed
removal pilot (e011) removed the blocker at the recorded simulation time and captured two Wait
recoveries, but the Ackermann rover still timed out; it is retained as negative calibration rather
than recovery-success evidence. A later headless TurtleBot3 differential smoke (e015) passed the
action, sensor, costmap, transport, and capture gates. Recovery-followed-by-success remains
**NOT_OBSERVED** on that platform: e016 removed a partial blocker at its predeclared simulation
time but timed out with zero recovery entries because FollowPath remained active until the client
deadline. A stronger e017 window then activated and removed a full-width blocker at both recorded
boundaries, but produced the same zero-recovery timeout. Do not keep tuning intervention timing to
force the desired branch; diagnose or replace the controller/plant failure mechanism first. This is
a narrow launch-config seam, not yet the requested reset/service API.

### Collection target and acceptance

- **Importance:** REQUIRED.
- **Pilot:** at least 3 independent seeds for each of success, recovery-success, and terminal
  failure, plus incomplete-evidence derivatives. These are development data only.
- **Final target:** TBD from pilot paired discordance and clustered power simulation; design for at
  least 40 independent seeds per major outcome family without rebuilding the scene.
- **Smallest acceptable implementation:** primitive corridor, one blocker, deterministic reset,
  LiDAR/odom/TF, Nav2 integration, separated truth outputs, and the three outcome families above.
- **Acceptance gate:** ten sequential reset/runs with correct opaque IDs, no truth leakage, no stale
  cross-episode actions, complete BT/action capture, and reproducible seed/config hashes.

## HIGH — surface docking choice and execution

Deferred until land collection is healthy. Implement only a small set of marina-slip choices with
an explicit recorded scoring/guard rule, followed by Nav2 execution. This scenario supports
contrastive selection and ecological validation; it must not reuse the synthetic Dock/Slalom
policy or call those artificial options RoboBoat tasks. A full contract will be frozen after the
land pilot identifies which contrastive evidence fields are actually needed.

## OPTIONAL — underwater or aerial stress test

Do not begin until the required land acceptance gate passes and the primary power target is on
schedule. Prefer one controlled branch motif (role indicator or confidence threshold) over a
complete competition task. These runs are descriptive robustness stress tests unless their
independent sample size becomes adequate.
