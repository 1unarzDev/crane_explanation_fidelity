# Decision Log

## 2026-09-19 — reconstruct PX4 primitives without importing simulator dynamics

- Decision: reproduce pinned `walls.sdf` box geometry and semantics in CRANE while retaining
  CRANE's validated multirotor physics and explicit ENU-to-Unity coordinate conversion.
- Evidence: the source world uses four matching primitive visual/collision boxes; no mesh or
  runtime SDF support is needed. The source ground collision is an infinite plane, represented by
  a documented 100 m benchmark envelope matching its visual extent.
- RQ impact: semantic walls can support auditable evidence references without implying that the
  robot observed them.
- Risk: x500-class shape/identity does not establish PX4 SITL or Gazebo dynamics equivalence.
- Revisit: add ArUco only for a concrete perception question and validate upstream wind through
  measured CRANE behavior rather than configuration presence.

## 2026-09-19 — reference environments separate canonical collision from visuals

- Decision: add recognizable platforms incrementally, beginning with a CRANE-native TurtleBot3
  warehouse, while separating canonical collision, simulation semantics, and presentation.
- Evidence: Unity's Nav2/SLAM example is Apache-2.0, but its pinned Robotics Warehouse dependency
  has no inspected license file. CRANE primitives retain the reproducible layout pattern without
  importing unclear assets.
- RQ impact: stable semantic IDs make obstacle/corridor references auditable without treating
  evaluator truth as robot-visible evidence.
- Risk: the differential base matches Waffle dimensions and remains PhysX-driven, but does not
  establish hardware-dynamics equivalence.
- Revisit: import higher-fidelity assets only with explicit terms and invariant collision geometry.

## 2026-09-19 — strict template verification as initial trust boundary

- Decision: accept only final sentences exactly licensed by a checked plan; reject arbitrary extra
  clauses and fall back to deterministic realization.
- Evidence: no independently validated proposition extractor exists in the repository yet.
- Alternatives: regex fact checks alone; LLM self-check; permissive semantic similarity.
- RQ impact: provides a conservative D/E implementation and measurable coverage cost for RQ2/RQ4.
- Validity risk: exact matching understates achievable LLM coverage and favors templates.
- Revisit: after independent verifier evaluation on held-out external and CRANE propositions.

## 2026-09-19 — passive Nav2 observer, no native hook

- Decision: use Jazzy `BehaviorTreeLog`, `NavigateToPose`, exact BT XML, and harness events.
- Evidence: local package/interface/header inspection confirms required level-1/2 fields.
- Alternatives: BehaviorTree.CPP/C++ blackboard hook; parsing console logs.
- RQ impact: faster auditable capture with no simulator/navigation behavior changes.
- Validity risk: transient blackboard values and exact internal sensor consumption remain unknown.
- Revisit: only under the five evidence-gap criteria in `ARCHITECTURE.md` after pilot.

## 2026-09-19 — prioritize independent episodes over broad integrations

- Decision: external benchmarks are gated to roughly one day and only after CRANE capture health.
- Evidence: deadline is October 4; primary inference depends on independent scenario instances.
- RQ impact: maximizes power and reduces risk that many paraphrases masquerade as sample size.
- Validity risk: narrower external generalization evidence.

## 2026-09-19 — treat Nav2 lifecycle readiness as capture quality, not robot failure

- Decision: pilot/final runs must distinguish action-server startup rejection from a navigation
  failure and record the startup margin/readiness procedure. The locally validated temporary
  setting is `CRANE_FIXTURE_DELAY=15`; it is not yet a frozen collection rule.
- Evidence: default-delay run timed out after two inactive-server rejections and only ~8.15 s of
  accepted execution; changing only the pre-fixture delay produced terminal success.
- Alternatives: call the timeout a mission failure; increase the action deadline; patch Nav2.
- RQ impact: prevents infrastructure startup from contaminating failure labels and recovery counts.
- Validity risk: a fixed delay can conceal host-load variation; explicit lifecycle readiness is
  preferable before final collection.

## 2026-09-19 — unified umbrella with pinned component boundaries

- Decision: use this repository as the umbrella root; pin astro_dock and CRANE as Git submodules,
  and install the exact explanation-package revisions into astro_dock through one setup script.
- Evidence: prior sibling checkouts embedded developer-specific paths and could drift independently.
- Alternatives: monorepo import; sibling repositories plus prose setup instructions; raw-data LFS.
- RQ impact: strengthens reproducibility and makes representation/verification comparisons traceable
  to exact simulator, ROS, evidence-core, and capture revisions.
- Validity risk: the nested core pin intentionally targets the last pre-umbrella core commit; later
  core updates require an explicit lock change and must not recursively initialize umbrella
  submodules inside astro_dock.

## 2026-09-19 — component source exists only in the pinned nested checkout

- Decision: the umbrella does not track a second copy of `crane_explain` source, tests, or Python
  packaging metadata. Setup installs the locked component revision only at
  `packages/astro_dock/src/crane_explain`.
- Evidence: retaining the pre-refactor root `src/`, `tests/`, and `pyproject.toml` duplicated the
  component and allowed umbrella code to diverge from the recorded nested pin.
- Alternatives: keep an umbrella-local editable copy; add `crane_explain` as another top-level
  submodule; copy files during setup.
- RQ impact: removes ambiguous code provenance from every benchmark and experimental run.
- Validity risk: core changes must be committed to the component repository first, then deliberately
  advanced in `manifests/workspace.lock.json`.

## 2026-09-19 — batch recorder fsync without dropping evidence

- Decision: flush each JSONL record, call `fsync` every 100 records, and always `fsync` on close.
- Evidence: per-record `fsync` captured 871 records but reduced the CRANE pilot to RTF 0.848 and
  invalidated it; the bounded-sync rerun captured 881 records at RTF 1.00055 and passed all quality
  gates with zero stale/failed observations.
- Alternatives: drop/downsample feedback; accept invalid runs; keep per-record barriers.
- RQ impact: retains full action evidence without perturbing the robot run enough to fail its
  collection validity gate.
- Validity risk: a process/host crash can lose up to the current buffered interval even though each
  line is flushed to the OS; completeness checks remain mandatory.

## 2026-09-19 — land is the powered primary benchmark

- Decision: request a minimal deterministic non-aquatic land corridor generator for the powered
  study; keep aquatic CRANE as ecological validation.
- Evidence: Nav2 capture is working, while aquatic HDRP requires a real windowed Vulkan loop and is
  less suitable for high-throughput collection. The first success question was too trivial to
  distinguish methods.
- Alternatives: scale only the Roboboat scene; implement multiple competition domains immediately;
  force aquatic simulation into unsupported headless modes.
- RQ impact: prioritizes independent C/D/F navigation motifs and statistical power for RQ1–RQ4.
- Validity risk: primary claims may be land-specific; surface/other-domain results must be labeled
  ecological or exploratory unless independently powered.

## 2026-09-19 — do not make direct BARN integration the primary path

- Decision: reuse BARN's generated-world and held-out sampling methodology now; defer its separate
  Gazebo/Jackal runtime to an optional, isolated one-day smoke after local land capture is healthy.
- Evidence: the audited ROS 2 harness has action/proximity outcome ambiguity and batch/report
  inconsistencies; the BARN 2026 organizer report says only one of five ROS 2 submissions was
  evaluable by the standard pipeline. See `docs/research/BARN_FEASIBILITY.md`.
- Alternatives: rebuild and repair BARN immediately; import BARN worlds into Unity; ignore BARN.
- RQ impact: preserves collection time while retaining scenario diversity/split principles.
- Validity risk: the primary study lacks a standardized external land embodiment unless the later
  smoke passes its frozen stop gates; report this limitation rather than implying BARN validation.

## 2026-09-19 — terminal explanations preserve client/BT/physical distinctions

- Decision: checked terminal plans report recorded action status and explicit harness deadline or
  cancellation as separate propositions, followed by an explicit causal limitation.
- Evidence: p01 involved a client deadline while p03 succeeded; neither record licenses a physical
  failure cause, and a successful terminal result does not prove every intermediate BT branch
  succeeded.
- Alternatives: collapse all non-success into navigation failure; answer only recovery counts.
- RQ impact: directly expands terminal-failure and misleading-premise coverage for RQ2–RQ4.
- Validity risk: richer software-mechanism explanations still require parsing exact BT transitions;
  terminal status alone remains level-1 evidence.

## 2026-09-19 — preserve Ackermann constraints in the headless land fixture

- Decision: use the existing PhysX Ackermann rover with a stamped, fixed-step ROS adapter; do not
  emulate Nav2 spin commands by rotating the transform or by inventing lateral actuation.
- Evidence: the first land smoke moved under wheel physics but later stopped when the controller
  requested near-zero linear velocity; an Ackermann rover cannot physically turn in place.
- Alternatives: reuse the aquatic holonomic controller; force a minimum crawl; directly manipulate
  pose; replace the rover with differential drive.
- RQ impact: execution explanations remain grounded in the actual embodiment, and recovery
  failures caused by incompatible behaviors can be represented honestly.
- Validity risk: stock recovery trees containing Spin may be structurally incompatible. Before
  powered collection, either configure an Ackermann-valid recovery tree and record its exact XML,
  or treat incompatibility as a deliberately scoped mechanism—not a generic navigation failure.

## 2026-09-19 — require populated costmap evidence through stock introspection

- Decision: land runs must observe at least one populated costmap. Record full-map topic deliveries
  and bounded `/local_costmap/get_costmap` snapshots separately; use the service snapshots for the
  validity gate while the topic path remains silent.
- Evidence: the initial configuration omitted the LaserScan source height limit and returned an
  all-zero map. Adding the Jazzy per-source `max_obstacle_height` populated the internal local and
  global obstacle layers (548 and 389 lethal cells in the discriminating probe). Neither
  transient-local nor volatile subscribers received the advertised full-map topic, including with
  `always_send_full_costmap=true`; the stock service returned populated snapshots reliably.
- RQ impact: obstacle/recovery pilots can require observable navigation-state evidence without a
  C++ hook. Recorded provenance explicitly does not claim controller consumption.
- Validity risk: service polling observes current Nav2 state, not the controller's exact sampled
  map. Claims must remain at that scope.
