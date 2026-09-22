# Environment Architecture

## Platform scope versus empirical scope

CRANE's environment architecture remains domain-general: it can host land, surface, underwater,
and aerial robots. The TRUSTMORE 2026 empirical scope is deliberately narrower. The confirmatory
study uses land/Nav2, ecological development prioritizes warehouse/proving-ground land navigation,
and RoboBoat is the intended surface-domain demonstration if its parallel workstream qualifies it.
Aerial and underwater validation are `DEFERRED_POST_SUBMISSION`.

Architecture generality is an implementation capability, not a paper claim that all supported
domains have been empirically validated.

## Authoritative layers

```text
CanonicalGeometry
  authoritative collision, traversability, semantic IDs, evaluator truth
        |
        +--> Robotics/Simulation
        |      physics, joints, sensors, TF, ROS, autonomy
        |
        +--> VisualPresentation
               meshes, materials, lighting, props, optional debug overlays
```

Interactive and headless modes must instantiate the same canonical layout and scenario identity
where practical. Presentation objects must not change collision, clearance, spawn validity, or
route feasibility. Imported reference worlds retain separate visual and collision roles rather
than collapsing into an opaque render-mesh collider.

## Scenario contract

Every reproducible scenario should declare:

- schema/generator version, world ID, robot/platform ID, seed, and configuration hash;
- start/goal and route identity;
- canonical obstacle set and initial enabled state;
- deterministic dynamic insertion/removal schedule;
- approximate route length, available alternatives, relevant semantic objects, expected challenge,
  and broad expected outcome;
- robot-visible and evaluator-only output roots;
- compatible interactive and headless launch modes.

Stable semantic IDs identify obstacles, aisles, gates, walls, landmarks, and route regions for
evaluation and playback. They do not by themselves license a natural-language claim that the robot
observed or reasoned about the object.

## Runtime and explanation boundary

Robotics/Simulation publishes observations, odometry/TF, commands, action results, and BT
transitions. The evidence pipeline records their identities and completeness separately from
evaluator truth. Delivered topic data is not described as internally consumed unless explicit
provenance establishes consumption. Temporal succession is not promoted to physical cause.

Ecological Nav2 capture retains an ordered, bounded BT transition stream with stable record IDs.
A BT node UID identifies a node instance, not an attempt. A recovery invocation ID is derived only
from a configured recovery leaf's observed `IDLE -> RUNNING` edge and is closed by its subsequent
status transition. Nav2 feedback recovery counts, BT leaf invocations, and whole-history
completeness remain separate. Because `BehaviorTreeLog` has no publisher sequence number, even an
observed start/end pair does not by itself prove an exact whole-episode count.

The ecological export boundary accepts the existing QA/capture artifacts and one opaque episode
ID, verifies their exact manifest/configuration/BT-policy/question-contract hashes, and creates a
new root containing physically separate `robot_visible/` and `evaluator_only/` directories. The
robot-visible plane contains runtime records and hashes but no scenario name, semantic obstacle
identity, expected outcome, evaluator truth, or input source path. A content-free top-level
manifest binds both files by SHA-256 without merging their contents.

Scenario identity is necessary but not sufficient for ecological admission. Each development
contract also declares observable runtime prerequisites: accepted terminal status, minimum
recorded recovery-invocation and trajectory inventories, required BT node observations where
applicable, predeclared signed-lateral/direction-change route thresholds where applicable, and
zero-drop bounds. Export fails before creating an output root when the intended mechanism did not
occur, even if the environment/configuration hashes match. The checked trajectory metrics are
also carried into robot-visible evidence so the explanation layer can describe the recorded shape
without access to evaluator-only obstacle identities.

The frozen F/G/H study remains isolated from new ecological scenarios. Warehouse/proving-ground
work may reuse generic runtime capture and validation infrastructure, but it must not alter frozen
questions, prompts, split, inclusion rules, model configuration, annotation guide, or stopping
rules.

The separate ecological explanation contract binds qualified environment mechanisms to prospective
questions, required robot-visible evidence planes, supported claim classes, and mandatory
withholding boundaries. Its manifest/configuration hashes prevent scenario drift, while its
evidence-plane validator prevents evaluator-only geometry, schedules, and expected outcomes from
silently becoming explanation inputs. Environment qualification selects mechanisms; it is not an
answer-fidelity result, independent sample count, or amendment to the frozen study.

## Interactive inspection

Interactive cameras, semantic/collider overlays, LiDAR or camera-frustum displays, path and
trajectory views, costmap/TF views, and Nav2/action/recovery status are presentation/debug clients.
They are optional in headless execution and may read canonical/runtime state without becoming
simulation authority. Their absence cannot change physics or navigation behavior.

## Ownership boundary

The parallel RoboBoat workstream owns the RoboBoat environment, vehicle, sensors, physics, Nav2
configuration, and docking behavior. Environment-platform changes must not modify those assets.
Any unavoidable generic shared change requires an isolated commit and a RoboBoat non-regression
when practical.
