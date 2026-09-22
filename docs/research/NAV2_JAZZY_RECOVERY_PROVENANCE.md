# Nav2 Jazzy recovery provenance: retained episode e019

**Status:** primary-source and retained-artifact audit, 2026-09-19.  
**Scope:** `land-nav-20260919-e019-worker-0`, the first retained recovery-followed-by-success
development episode. This note establishes software execution semantics; it does not establish a
physical cause for the controller failure.

## Bottom line

The strongest supported reconstruction is:

> For the accepted NavigateToPose goal, `FollowPath` returned `FAILURE`. The recorded
> `WouldAControllerRecoveryHelp` condition then returned `SUCCESS`, the BT entered one `Wait`
> action, and that action returned `SUCCESS`. NavigateToPose feedback increased its recovery count
> from zero to one. The tree replanned, started `FollowPath` again, and the same goal later returned
> `succeeded`.

This is a level-2 reconstructed software mechanism. Nav2 1.3.12 source establishes how those node
statuses and the feedback count are produced. It does **not** license “the mobility hold caused the
failure,” “an obstacle caused the failure,” or a counterfactual about what would have happened
without the intervention. The hold and release are evaluator-only truth.

## Retained episode anchors

| Anchor | Retained value |
|---|---|
| Run / episode | `land-nav-20260919-e019` / `land-nav-20260919-e019-worker-0` |
| NavigateToPose goal ID | `4fe6db797c914a98b7f200228b073a87` |
| Goal | frame `odom`, position approximately `(3.0, 0.0, 0.0)` |
| Terminal result | status `succeeded` / action status code 4; Nav2 error code 0 |
| BT XML | [`packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml`](../../packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml), SHA-256 `14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520` |
| Captured XML | `data/robot_visible/dev/land-nav-20260919-e019/capture/behavior_tree.xml`, same SHA-256 |
| Event stream | `data/robot_visible/dev/land-nav-20260919-e019/capture/events.jsonl`, SHA-256 `43e32d83c59926dd722b6ce171ebbb0e6d481e1d5c46a9db9a96754c167913ea` |
| Capture manifest | `data/robot_visible/dev/land-nav-20260919-e019/capture/manifest.json`, SHA-256 `0a9ce4a8facda7c54a242b8d4a340ecf65109bc5e92720a3e2c0478a780aaf87` |
| Predeclaration | [`research/explanation_fidelity/experiment_configs/development/land-nav-20260919-e019.json`](../../research/explanation_fidelity/experiment_configs/development/land-nav-20260919-e019.json) |
| CRANE checkout recorded for run | `2581497eb25968b5624ad95b940dacd988b03e44`; clean checkout, but the player manifest did not embed a source commit |
| ROS capture checkout | `crane_explain_ros` `9ab4f320bdccee468de77ce4b17762853d3ccf93` |
| Runtime identity | ROS 2 Jazzy; Nav2 Debian packages 1.3.12; default image name `lunarzdev/astro:cuda` |

The capture contains one accepted goal and matching result, 22 published BT transitions, 2,051
feedback records, two action-status records, both capture boundaries, and six harness events.
Feedback values occur 955 times at recovery count 0 and 1,096 times at count 1; repeated feedback
messages are not additional attempts.

## Exact runtime package/source mapping

The currently retained local image is
`lunarzdev/astro@sha256:9c286b78dcc1ecf0a159f624f642cf831d463370ce264f00fdd6f6c30ce50053`.
Inspection of that immutable image reports:

| Debian package | Installed version |
|---|---|
| `ros-jazzy-nav2-behavior-tree` | `1.3.12-1noble.20260615.162300` |
| `ros-jazzy-nav2-behaviors` | `1.3.12-1noble.20260615.170333` |
| `ros-jazzy-nav2-bt-navigator` | `1.3.12-1noble.20260615.165211` |
| `ros-jazzy-nav2-controller` | `1.3.12-1noble.20260615.165600` |
| `ros-jazzy-nav2-msgs` | `1.3.12-1noble.20260615.145957` |
| `ros-jazzy-nav2-navfn-planner` | `1.3.12-1noble.20260615.170058` |
| `ros-jazzy-nav2-regulated-pure-pursuit-controller` | `1.3.12-1noble.20260615.170110` |
| `ros-jazzy-behaviortree-cpp` | `4.9.0-1noble.20260615.161133` |

Nav2 release `1.3.12` is source tag
[`6be3614013ec586051b86c97b919b293281490fe`](https://github.com/ros-navigation/navigation2/tree/6be3614013ec586051b86c97b919b293281490fe).
BehaviorTree.CPP release `4.9.0` is source tag
[`3ff6a32ba0497a08519c77a1436e3b81eff1bcd6`](https://github.com/BehaviorTree/BehaviorTree.CPP/tree/3ff6a32ba0497a08519c77a1436e3b81eff1bcd6).
The installed `bt_service_node.hpp`, `clear_costmap_service.hpp`, `tree_node.h`, and
`abstract_logger.h` headers byte-match those two pinned source trees.
The ROS release repository tag `release/jazzy/nav2_bt_navigator/1.3.12-1` resolves to
`1340f75b723f3040dd69f30571a7394cf7417f0b`. The historical Bloom track records upstream
`navigation2`, `release_tag: :{version}`, and no source patches
([track](https://github.com/ros2-gbp/navigation2-release/blob/7c21ef75e554cfa6093eab9272075fe6edcc9dd9/tracks.yaml));
the contemporaneous rosdistro update records Navigation2 `1.3.12-1`
([pinned Jazzy distribution entry](https://github.com/ros/rosdistro/blob/6c1c611499e19e0dece59ff21c1dffdba8905058/jazzy/distribution.yaml)).
Jazzy has since advanced, so the installed Debian versions above—not today's rosdistro head—are
authoritative for this episode.

The installed message definitions byte-match tag 1.3.12:

| Interface | SHA-256 | Primary source |
|---|---|---|
| `BehaviorTreeLog.msg` | `dfdec41db311f6a3de4cdba3cd8b0c7a17c7763159afb477fbd6cd417f2747a1` | [source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/msg/BehaviorTreeLog.msg) |
| `BehaviorTreeStatusChange.msg` | `b2e78d4d03efab173eff5786d9a6485ad69878e371e20654d5f67c363638e7a5` | [source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/msg/BehaviorTreeStatusChange.msg) |
| `NavigateToPose.action` | `656fdf8f14c825b0fe6419d8a647793ea78564442c9ca2a026238bbf7f7e8f91` | [source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/action/NavigateToPose.action) |
| `FollowPath.action` | `8c29c7286c5ee0616d19d15d1eec1aefb810a292e7c956499349b294232078ad` | [source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/action/FollowPath.action) |

The local stock `navigate_to_pose_w_replanning_and_recovery.xml` has SHA-256
`5895b63840d54c6d7eee3d3b3f3ee177680af9e58a14cbf61c4df39fe5db2a90`, but **was not the tree used**.
The fixture passed the retained custom XML through `default_nav_to_pose_bt_xml`; the captured copy
and hash above are the authoritative tree.

## Configuration provenance

At CRANE commit `2581497e`, the following files have the same hashes as the present checkout:

| File | SHA-256 | Role |
|---|---|---|
| `nav2_land_fixture.yaml` | `3851544a099b4d3ed48e54ffd6140c51971d8e9f902a6ff78048a4a71bccf0c3` | Planner, controller, progress/goal checker, costmaps, behavior server, BT navigator |
| `nav2_land_progress_recovery.xml` | `14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520` | Exact bounded BT |
| `run_nav2_controller_fixture.sh` | `92d5bb03d9750bbd9298cb6fd0690e8f6a1739e566f2e3f53d217145f545df03` | Launches servers, sets custom BT parameter, runs fixture |
| `nav2_follow_path_fixture.py` | `204f10d4429beabc3034d37d096386677a7806925ebefdfb1febeb2ec8687a1a` | Sends goal and records goal/result boundaries |

Material parameters in `nav2_land_fixture.yaml` are:

- `SimpleProgressChecker`: movement radius 0.10 m, allowance 10.0 s;
- `SimpleGoalChecker`: 0.55 m position and 0.35 rad yaw tolerance;
- `FollowPath`: `RegulatedPurePursuitController`, desired speed 0.8 m/s, rotate-to-heading off,
  reversing allowed;
- planner `GridBased`: `NavfnPlanner`, A* enabled, tolerance 0.5 m;
- local/global obstacle inputs: `/scan`, `ObstacleLayer` plus `InflationLayer`;
- behavior plugin `wait`: `nav2_behaviors::Wait`;
- BT navigator: `NavigateToPoseNavigator`, 10 ms loop, error-code blackboard keys
  `compute_path_error_code` and `follow_path_error_code`.

The retained controller log independently confirms the loaded plugin types and reports “Failed to
make progress,” “Running wait,” “wait completed successfully,” and finally “Goal succeeded.”

## Source-grounded event semantics

### 1. Progress failure and `FollowPath FAILURE`

`SimpleProgressChecker::check()` resets its baseline after movement greater than the configured
radius and otherwise returns false after the configured allowance. `ControllerServer` converts
that false result into `FailedToMakeProgress`, terminates the FollowPath action with error 105
(`FAILED_TO_MAKE_PROGRESS`), and publishes zero velocity
([progress checker](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_controller/plugins/simple_progress_checker.cpp),
[controller server](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_controller/src/controller_server.cpp),
[FollowPath interface](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/action/FollowPath.action)).
`FollowPathAction::on_aborted()` writes the action result's error code to the XML-bound
`follow_path_error_code` output and returns BT `FAILURE`
([source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/plugins/action/follow_path_action.cpp)).

Therefore the recorded `FollowPath RUNNING→FAILURE`, together with error 105 in the controller
log/result path, establishes a controller-progress failure. It does not establish why the robot
did not progress physically.

### 2. Recovery eligibility and bounded retry

`WouldAControllerRecoveryHelp` returns success when the bound error code is among `UNKNOWN`,
`PATIENCE_EXCEEDED`, `FAILED_TO_MAKE_PROGRESS`, or `NO_VALID_CONTROL`
([source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/plugins/condition/would_a_controller_recovery_help_condition.cpp)).
Its recorded `IDLE→SUCCESS` therefore means error 105 was eligible for this configured controller
recovery branch; it is not an independent diagnosis or causal classifier.

`RecoveryNode::tick()` requires exactly two children. When the primary child fails and retry budget
remains, it halts that child and ticks the recovery child. A successful recovery increments the
node's internal retry counter and runs the primary child again; failed or exhausted recovery ends
the node in failure
([source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/plugins/control/recovery_node.cpp)).
The retained XML has `number_of_retries="2"`; this is a maximum retry budget, not evidence that two
attempts occurred.

### 3. What the recovery count counts

`WaitAction::on_tick()` calls `increment_recovery_count()` when the BT action first starts. The
base action node invokes `on_tick()` only when the node is not already active, so repeated BT ticks
while one Wait goal is running do not increment it repeatedly
([Wait BT plugin](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/plugins/action/wait_action.cpp),
[base action node](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/bt_action_node.hpp)).
The behavior-server `Wait` sets an end time and succeeds after that duration
([behavior plugin](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behaviors/plugins/wait.cpp)).

`NavigateToPoseNavigator::onLoop()` reads blackboard key `number_recoveries` into feedback field
`number_of_recoveries`
([source](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_bt_navigator/src/navigators/navigate_to_pose.cpp)).
The same navigator resets that blackboard counter when initializing an accepted goal. The value is
a count of recovery **leaf invocations**, not outer RecoveryNode cycles: Wait, Spin, BackUp,
AssistedTeleop, and each costmap-clear leaf increment it. A local+global clear sequence can add two.
Thus this custom tree's 0→1 feedback change and one unique `Wait IDLE→RUNNING→SUCCESS` support
exactly one recorded Wait recovery action for the bracketed goal. They are distinct from the
fixture's `goalAttempts: 1` and from `RecoveryNode`'s private retry counter. Reports should name the
unit rather than silently generalizing Nav2's field to platform-independent “recovery attempts.”

### 3a. A direct `ClearEntireCostmap IDLE→SUCCESS` is a completed action invocation

In this pinned release, `ClearEntireCostmap` is registered as an `Action` and its implementation
inherits `BtServiceNode`, which in turn inherits BehaviorTree.CPP `ActionNodeBase`; it is not a
condition guard
([Nav2 node model](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/nav2_tree_nodes.xml),
[plugin declaration](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/plugins/action/clear_costmap_service.hpp)).
On the first tick of an activation, `BtServiceNode::tick()` calls `on_tick()`, sends one asynchronous
service request, and checks its future. `ClearEntireCostmapService::on_tick()` increments
`number_recoveries` once. If the response arrives within that same call, `check_future()` returns
`SUCCESS`; otherwise it returns `RUNNING` until a later tick completes or times out
([service-node implementation](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/bt_service_node.hpp),
[clear plugin](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/plugins/action/clear_costmap_service.cpp)).
BehaviorTree.CPP applies the tick's returned state only after `tick()` returns and emits a status
callback only when the state changes. Therefore a fast completion is correctly logged as the
single transition `IDLE→SUCCESS`, without an invented `RUNNING` edge
([tick/status implementation](https://github.com/BehaviorTree/BehaviorTree.CPP/blob/3ff6a32ba0497a08519c77a1436e3b81eff1bcd6/src/tree_node.cpp)).
Nav2's own pinned unit test confirms that one tree tick can return `SUCCESS` while changing the
recovery count from zero to one
([test](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/test/plugins/action/test_clear_costmap_service.cpp)).

For the exact loaded XML, which contains no completion-overriding precondition on this leaf, one
unique `IDLE→SUCCESS` event for its UID establishes **one recorded, successfully completed
ClearEntireCostmap service invocation** and one recovery-counter increment. It does not by itself
establish that exactly one invocation occurred in the whole episode: the ROS log may be incomplete,
and replayed/duplicated captured records must first be deduplicated. Nor does service success prove
that map content changed, that an obstacle was removed, or that the clear caused later navigation
success. A later genuine invocation of the same tree node requires an intervening reset to `IDLE`;
control nodes reset completed children,
whereas a running child's halt invokes its halt method before resetting it
([control-node reset semantics](https://github.com/BehaviorTree/BehaviorTree.CPP/blob/3ff6a32ba0497a08519c77a1436e3b81eff1bcd6/src/control_node.cpp)).
For `BtServiceNode`, halt clears its local `request_sent_` state and resets the BT status, but does
not prove cancellation or reversal of the already-dispatched ROS service side effect. Thus
`SUCCESS→IDLE` is an activation boundary, not another invocation and not evidence that the costmap
clear was undone.

The same `IDLE→SUCCESS` shape is also normal for synchronous condition guards. BehaviorTree.CPP
defines conditions as side-effect-free synchronous checks that must not return `RUNNING`
([condition contract](https://github.com/BehaviorTree/BehaviorTree.CPP/blob/3ff6a32ba0497a08519c77a1436e3b81eff1bcd6/include/behaviortree_cpp/condition_node.h)).
`BehaviorTreeLog` carries only node name, UID, and old/new status, not node type or registration ID
([Nav2 logger](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/ros_topic_logger.hpp)).
Capture must therefore classify leaves from the exact retained XML plus the pinned plugin
registry/model, never from transition shape or a suggestive node name. A condition success records
that its guard evaluated true; a known `ClearEntireCostmap` action success records a completed
service invocation. This is an allowlisted, exact-plugin inference rather than a generic rule for
all `IDLE→SUCCESS` transitions: BehaviorTree.CPP preconditions or injected callbacks can substitute
a terminal result without running the leaf, and nonstandard direct calls can escape the usual
reset-delimited control flow
([execution path](https://github.com/BehaviorTree/BehaviorTree.CPP/blob/3ff6a32ba0497a08519c77a1436e3b81eff1bcd6/src/tree_node.cpp)).

**Capture recommendation.** Open an invocation for a source-verified recovery `Action` on either
`IDLE→RUNNING` or direct `IDLE→SUCCESS`; close the latter immediately and close the former on its
terminal edge. Admit direct completion only for an allowlisted concrete plugin in the exact loaded
tree, after checking that no completion-overriding precondition/callback applies. Key identity by
accepted goal, loaded-tree identity, node UID, and activation ordinal. Treat `*→IDLE` only as
reset/halt evidence. Deduplicate exact repeated captured events,
require an intervening reset before accepting another activation for the same UID, and retain the
NavigateToPose recovery-count sequence as an independent cross-check. Say “one invocation is
recorded” unless terminal bracketing and transport/capture completeness justify “exactly one
occurred.”

### 4. Meaning and completeness of `BehaviorTreeLog`

`RosTopicLogger` registers as a BehaviorTree.CPP status-change logger. Each event contains the BT
node name, per-tree UID, previous/current status, and an internal BT timestamp; the enclosing
message timestamp comes from the ROS clock. It publishes on `behavior_tree_log` with QoS depth 10
([logger](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/ros_topic_logger.hpp),
[interfaces](https://github.com/ros-navigation/navigation2/tree/6be3614013ec586051b86c97b919b293281490fe/nav2_msgs/msg)).
UIDs identify node instances within that loaded tree; they are not stable identifiers across tree
loads, XML changes, processes, or episodes.

The action server flushes the topic logger in its `on_loop` callback. `BehaviorTreeEngine::run()`
calls that callback only while the tick result remains RUNNING or IDLE. There is no explicit logger
flush after `run()` returns in the audited implementation
([BT action server](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/include/nav2_behavior_tree/bt_action_server_impl.hpp),
[engine](https://github.com/ros-navigation/navigation2/blob/6be3614013ec586051b86c97b919b293281490fe/nav2_behavior_tree/src/behavior_tree_engine.cpp)).
Cancellation returns before the loop callback as well. Buffered terminal/halt transitions may be
dropped when the logger is replaced, or emitted with a later goal if the same logger/tree is
reused. This explains why e019's topic trace ends after the second `FollowPath` enters RUNNING even though
the action result and navigator log later say success: terminal-tick transitions can remain
unpublished. Whole-BT transition history is therefore incomplete. The result is not contradicted.

## Recorded e019 transition chain

The relevant published transitions, in order, are:

1. `NavigateRecovery`, `NavigateAttempt`, and `ComputePathToPose`: IDLE→RUNNING;
2. `ComputePathToPose`: RUNNING→SUCCESS;
3. `FollowPath`: IDLE→RUNNING, then RUNNING→FAILURE;
4. `NavigateAttempt`: RUNNING→FAILURE and reset;
5. `ProgressRecovery`: IDLE→RUNNING;
6. `WouldAControllerRecoveryHelp`: IDLE→SUCCESS;
7. `Wait`: IDLE→RUNNING, then RUNNING→SUCCESS;
8. `ProgressRecovery`: RUNNING→SUCCESS and reset;
9. `NavigateAttempt` and `ComputePathToPose`: IDLE→RUNNING;
10. `ComputePathToPose`: RUNNING→SUCCESS;
11. `FollowPath`: IDLE→RUNNING.

The separate action result then establishes terminal success for the same goal ID. The source-level
flush behavior above prevents inferring that missing final BT transitions mean the nodes did not
succeed.

## Unresolved provenance gaps

1. **Exact episode image digest is not sealed in the e019 manifest.** The launcher uses image name
   `lunarzdev/astro:cuda`, and the retained local image currently resolves to digest `9c286b78…`;
   contemporaneous project documentation also records that digest. The episode's removed
   controller container cannot now be inspected, so identity with that digest is strongly
   supported but not cryptographically proven from the e019 artifact alone.
2. **The runtime parameter file path/hash is not recorded in the capture manifest.** The
   predeclaration names the custom BT but not `nav2_land_fixture.yaml`. The file at the recorded
   CRANE commit matches the current hash, and the controller log/plugin behavior matches it, but a
   retained launch argv/environment snapshot would be stronger.
3. **Installed source-to-binary identity is release-mapped, not binary-rebuilt.** Installed package
   versions, ROS release tags, and byte-identical installed interfaces map to source tag 1.3.12.
   No reproducible rebuild comparison of the shared libraries was retained.
4. **BT topic delivery is not lossless evidence.** QoS depth is 10, capture/DDS can lose samples,
   and the implementation can omit final-tick transitions. Exact recovery count is justified here
   jointly by the accepted/terminal goal brackets, monotonic feedback 0→1, exact retained tree, and
   the single unique Wait entry—not by assuming the BT topic is complete.
5. **Controller inputs are observable, not proven consumed.** Delivered odometry, scans, and
   costmap snapshots do not prove which precise sample influenced an internal controller step.
6. **Physical cause remains evaluator-only.** The scheduled mobility hold/release is retained
   outside robot-visible evidence and was not tested through a controlled counterfactual replay.

## Required fix for future final episodes

Retain an immutable runtime manifest beside each capture containing image digest, `dpkg-query`
versions, hashes of the parameter file and BT XML, complete launch argv/environment overrides,
plugin load log, and action/BT topic QoS. Keep the terminal action result authoritative for task
status, mark whole-BT transitions incomplete under Nav2 1.3.12, and continue deriving exact recovery
counts only from the joint evidence rule above.
