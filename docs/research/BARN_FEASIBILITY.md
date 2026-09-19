# BARN Challenge 2026 integration feasibility

**Audit date:** 2026-09-19
**Decision:** **NO-GO for direct integration into the CRANE final-study pipeline before the core CRANE pilot and study freeze.** **GO for reusing BARN's scenario-sampling ideas immediately.** Reconsider a standalone BARN external-validity pilot only after the CRANE/Nav2 capture path is healthy, with a hard one-day timebox and explicit stop conditions below.

This is a primary-source audit of the [official ICRA BARN Challenge 2026 page](https://people.cs.gmu.edu/~xiao/Research/BARN_Challenge/BARN_Challenge26.html) and its linked ROS 2 evaluator, [`Saadmaghani/The-Barn-Challenge-Ros2`](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2), inspected at commit [`d6c575b51e477bd524d634e12cffeb34036fcd1e`](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/tree/d6c575b51e477bd524d634e12cffeb34036fcd1e). No BARN simulation was run during this audit.

## Executive answer

A clean, standalone, single-world smoke run may be achievable in one day on a compatible Ubuntu/Jazzy machine that already has Singularity 4.3 or can install the Clearpath dependencies. A scientifically usable integration with this project's capture, truth separation, episode validation, and paired explanation benchmark is **not plausibly under one day**.

The distro-level fit is favorable: both projects use ROS 2 Jazzy, Nav2, `NavigateToPose`, and `ros_gz`. The integration-level fit is poor:

- BARN is a separate Gazebo Harmonic/Jackal simulator, not a CRANE/Unity scenario package. Running it adds a second simulator and robot embodiment rather than expanding CRANE's scenario library.
- The provided runner judges success from pose proximity and collision/timeout state, not from the `NavigateToPose` terminal result. It therefore cannot be adopted as evaluator truth without reconciliation.
- The public batch and report scripts contain internal inconsistencies that must be corrected and regression-tested before collection.
- The repository declares itself under work, has no repository license, leaves the ROS package license as `TODO`, does not pin apt/rosdep dependencies, and omits the advertised DynaBARN worlds.
- BARN offers environment difficulty and navigation outcome diversity, but it does not provide the decision-time rationale, fault labels, balanced recovery mechanisms, false-premise questions, or evaluator-only causal truth required for RQ1--RQ4.

The likely paper value of one day spent integrating it is lower than one day spent collecting independent CRANE/Nav2 episodes or validating the verifier. BARN is best treated as a post-freeze external navigation stress test if schedule permits.

## What BARN 2026 actually standardizes

The official page describes 300 pregenerated BARN environments plus a generator, with 50 hidden evaluation environments drawn from the same distribution. The task is to drive a standardized Clearpath Jackal from a predefined start to a goal as quickly as possible without collision, using standardized 2D LiDAR input and onboard motion commands. The official evaluation averages 10 trials in each of 50 test environments and scores successful runs by optimal time divided by actual time clipped to `[2×OT, 8×OT]`; collision or failure to reach the goal scores zero. The page also describes physical finals and DynaBARN/dynamic-obstacle bonuses. See the official page's “The Challenge” and “Competition Rules” sections.

The organizers' final [BARN Challenge 2026 report](https://people.cs.gmu.edu/~xiao/papers/barn26_report.pdf) clarifies the executed protocol and supersedes stale prospective text on the web page: 2026 focused exclusively on static constrained environments; the public set was 300 `5 m × 5 m` cellular-automata worlds, with 50 unseen evaluation worlds and 10 trials per world. DynaBARN scores were optional, not part of final ranking.

The official page links separate [ROS 1](https://github.com/Daffan/the-barn-challenge) and [ROS 2](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2) evaluation pipelines. Some legacy prose on the 2026 page still describes Ubuntu 18.04/ROS Melodic and prior physical locations; for ROS 2 feasibility, the linked ROS 2 repository is the authoritative implementation inspected here.

### ROS, Gazebo, Nav2, and robot assumptions

| Layer | Verified ROS 2 evaluator assumption | Relevance here |
|---|---|---|
| OS/ROS | Only ROS 2 Jazzy is supported by the README; the container starts from the floating `ros:jazzy` image ([README](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md#L24-L56), [Singularity definition](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/Singularityfile.def#L1-L24)). | Same ROS distro, but BARN does not pin the exact Jazzy/Nav2/Clearpath package versions used to produce its results. |
| Simulator | Gazebo Harmonic-format SDF worlds launched through `ros_gz_sim`; the repository includes a script explicitly described as converting Gazebo Classic worlds to Harmonic and adds physics, sensors, contact, and touch plugins ([patcher](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/gz_harmonic_world_patcher.py), [launch](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/BARN_runner.launch.py#L54-L99)). | `astro_dock` already lists `ros-jazzy-ros-gz`, but CRANE itself is Unity/PhysX. The physics, collision sensor, coordinate system, reset, and clock are different experimental platforms. |
| Robot | Clearpath J100 Jackal, root namespace `/`, entity name `robot`, `base_link`, and `/platform/odom/filtered`; robot spawning uses `clearpath_gz` ([robot config](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/robot.yaml), [hard-coded entity assumptions](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/gazebo_simulation.py#L15-L70)). | CRANE's fixture uses a different vehicle, topics, dimensions, and command bridge. BARN is an external embodiment, not a drop-in world set. |
| Sensors | The robot file declares front/rear Hokuyo 2D lidars and a Velodyne 3D lidar; Nav2 rewrites obstacle sources to the front 2D scan remapped to `/front/scan` ([robot config](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/robot.yaml), [launch remap](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/BARN_runner.launch.py#L101-L122), [Nav2 config](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/nav2.yaml#L130-L207)). | CRANE's current full fixture consumes point clouds and `/crane/odom`; information parity cannot be assumed across platforms. |
| Navigation | Mapless odom-frame Nav2 with NavFn, MPPI, local/global obstacle costmaps, smoother, recovery behaviors, velocity smoother, BT navigator, and lifecycle manager ([Nav2 config](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/nav2.yaml), [bringup](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/nav2_bringup.launch.py#L109-L248)). | Passive `BehaviorTreeLog` and action capture should conceptually apply, but controller, costmap, robot footprint, progress thresholds, and action timeouts differ from CRANE. |
| Goal | The launch sends a `NavigateToPose` goal in `odom`, 10 m forward for static worlds, via a timed `ros2 action send_goal` process ([launch](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/BARN_runner.launch.py#L124-L183)). | Existing passive action/BT capture can observe the graph, but the harness does not own or retain a structured action result. |
| Trial end | Collision is a Gazebo touch-plugin Boolean; timeout defaults to 100 simulated seconds; “success” is entry within 1 m of the runner's goal coordinate ([runner](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/barn_runner.py#L64-L113)). | These must be recorded as harness/evaluator events and must not be conflated with Nav2 action success, BT failure, cancellation, or controller consumption. |

The supplied Nav2 parameters use a Jackal footprint of approximately `0.508 × 0.432 m`, matching the official page's `508 × 430 × 250 mm` description. The default MPPI limit in the public config is only `0.5 m/s`, despite the official metric defining optimal time using a `2 m/s` maximum; that is acceptable for competition scoring but makes absolute time comparisons with CRANE meaningless without careful normalization.

## Installation and runtime burden

### Nominal upstream path

The README asks the user to create a new workspace, clone the repository, run unrestricted `rosdep install`, and build with `colcon --symlink-install`. Its package manifest depends on Clearpath packages (`clearpath_common`, `clearpath_config`, `clearpath_msgs`, `clearpath_simulator`), `ros_gz_interfaces`, and `nav2_bringup` ([package manifest](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/package.xml)).

The alternative is a Singularity 4.3 image. The definition uses `ros:jazzy`, installs `ros-jazzy-ros-gz`, invokes `rosdep`, and builds the workspace. The README says 4.3 was tested and lower versions were not. Building requires Singularity and sudo ([README](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md#L58-L90)).

### Burden and reproducibility risks

- The current host audit found neither ROS/colcon/rosdep nor Singularity/Apptainer installed. `astro_dock` contains Jazzy, Nav2, and `ros_gz` dependencies, but its checked package list does not include the Clearpath packages ([local pinned environment package list](../../packages/astro_dock/.devcontainer/apt-packages.txt)). A new container build or a separate Singularity installation is therefore required.
- The supplied wrapper starts Singularity with `--network=none` ([wrapper](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/singularity_run.sh)). A passive ROS/DDS observer outside that container cannot simply join the graph; the observer must be installed/built into the image, or BARN must run in a separately controlled container topology with an explicit ROS domain and network configuration.
- The Singularity instructions mistakenly tell users to clone the ROS 1 `Daffan/the-barn-challenge` repository rather than the ROS 2 repository containing the shown definition ([README lines 64--72](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md#L64-L73)). This is recoverable but evidence that the path is not turnkey.
- Dependencies are resolved live from a floating base image and rosdep/apt; no image digest, Debian version lock, vcs lock, or generated dependency manifest is retained. That conflicts with this project's pinned-environment and artifact-audit goals.
- The repository has no top-level license in GitHub metadata or the tree, and `package.xml` declares `<license>TODO</license>` ([manifest](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/package.xml#L16-L22)). It may be inspected and cited, but code/world redistribution or vendoring is not cleared by the repository.
- The repository includes 300 static SDF worlds and 300 path arrays. Its README says DynaBARN is absent even though launch branches for indices 300--359 remain in the code ([README update](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md#L12-L22), [world selection](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/BARN_runner.launch.py#L42-L52)). Dynamic-obstacle integration will fail for missing world files unless sourced and validated separately.
- A full public test as described upstream is 50 worlds × 10 trials × up to 100 simulated seconds, plus process startup and 10-second sleeps. Even if automation were correct and simulation ran at real time, worst-case trial time alone is roughly 13.9 hours, before startup overhead. This cannot be a one-day integration-and-study task.
- Most importantly, the final organizer report records that 17 teams entered simulation, five with ROS 2, but only **one of the five ROS 2 submissions** could be evaluated by the standard ROS 2 pipeline; 11 of 12 ROS 1 submissions were evaluable. The authors characterize ROS 1 as the more mature/reliable BARN platform. This is direct empirical evidence that the new Jazzy path was not reliably turnkey in the 2026 competition, not merely a hypothetical integration risk.

## Evaluator defects that block direct adoption

These are not cosmetic; they can corrupt explanation labels or study accounting.

1. **BARN “success” is not Nav2 action success.** The runner stops successfully when Euclidean distance to its coordinate is ≤1 m, whereas Nav2's configured goal tolerance is 0.25 m. It does not read the action terminal state or result. A trial can therefore be labeled BARN-success while `NavigateToPose` is still active, later fails, or never reports success. Conversely, a Nav2 result and a Gazebo collision event have distinct semantics. Preserve both and define the evaluator rule before use ([runner termination](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/barn_runner.py#L89-L113), [goal tolerance](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/nav2.yaml#L38-L42)).
2. **A non-moving robot can hang before timeout accounting begins.** The runner waits without a deadline until displacement from the initial pose exceeds 0.1 m; its 100-second deadline begins afterward. Lifecycle/goal delivery failures can therefore produce an unbounded invalid run rather than a timeout ([runner lines 68--88](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/barn_runner.py#L64-L89)).
3. **The public test loop does not run the claimed 50 worlds.** It iterates `i={7..49}`, yielding 43 indices from 42 to 294, while its comment and README claim indices `0, 6, …, 294` ([test script](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/test.sh), [README claim](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md#L118-L132)).
4. **The report script recomputes a different score.** The live runner and official 2026 page use a lower clip of `2×OT`; `report_test.py` uses `4×OT` despite an internally contradictory comment. It also expects all 50 public indices, including the seven skipped by `test.sh` ([runner scoring](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/barn_runner.py#L121-L153), [report script](https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/report_test.py#L53-L72)).
5. **Trial output is too thin for explanation research.** Each line records only world index, succeeded/collided/timeout flags, elapsed time, and score. It lacks episode/run IDs, action goal/result, recoveries, BT transitions, exact BT XML, configuration hashes, reset quality, sensor identities, and invalid-run reasons. The existing `crane_explain_ros` observer can add some fields, but launch integration and artifact joining still have to be implemented and tested.

No final-study BARN data should be collected until these are fixed or explicitly wrapped, tested, and frozen. Upstream competition scores must not be silently recomputed with a locally changed evaluator.

## What is reusable without integration

BARN's strongest contribution to this project is scenario methodology, not its navigation score:

- **Large static geometry pool:** select independent world IDs rather than treating repeated questions/trials as independent samples.
- **Difficulty stratification:** use retained shortest-path/path-length metadata to stratify scenario sampling before outcomes are known. Do not select only worlds that generate desired failures.
- **Held-out scenario generation:** BARN's public-versus-hidden same-distribution protocol is a useful model for sealing CRANE scenario families and prompts.
- **Repeated trials:** repeat a bounded number of trials per scenario to measure stochastic outcome stability, while clustering inference at scenario/episode level.
- **Separate outcome axes:** retain collision, harness deadline, action result, recovery mechanism/count, and completion time as different fields rather than one failure label.
- **Fair paired replay:** capture each episode once, then derive prose and structured evidence presentations from the same retained trace. BARN itself compares navigation systems, so this pairing must be added for RQ1--RQ4.
- **Geometry stress diversity:** constrained passages can help produce progress/controller failures and recovery sequences. They do not establish why a failure occurred; geometry metadata remains evaluator-only unless the robot actually observed/consumed it.

These ideas can be implemented in CRANE without importing Gazebo, Jackal, Clearpath packages, or BARN world assets.

## Research fit and incompatibilities

### Potential value

- BARN is a recognized navigation benchmark with challenging constrained spaces, enabling a narrow external-validity check that the passive Nav2 evidence/capture and verifier are not tailored only to CRANE.
- Its stock Jazzy BT navigator should expose the same class of BT transition and action evidence targeted by the observer, subject to verifying the installed Nav2 version and topic behavior in the built container.
- Natural successes, collisions, timeouts, planning difficulties, progress failures, and recovery sequences could expand mechanism diversity.

### Why it is not a substitute for the central benchmark

- BARN evaluates navigation performance, not explanation trustworthiness. It has no gold supported propositions, question set, material-error labels, answerability labels, evidence-completeness interventions, or model-visible/evaluator-only split.
- A collision or later timeout does not prove that a prior plan/decision was wrong, nor does a narrow passage prove a causal attribution.
- Its goal is fixed and no task-alternative decision policy is recorded, so it does not directly exercise Dock/Slalom-style contrastive decisions or candidate status.
- The default configuration changes the controller from CRANE's Regulated Pure Pursuit to MPPI, the footprint from a large CRANE vehicle to Jackal, the observation from point cloud to 2D scan, and the simulator from Unity/PhysX to Gazebo Harmonic. Any effect cannot be attributed solely to scenario geometry.
- BARN does not select or retain an explicit BT XML in its config. Nav2 will resolve its installed default tree, so capture must copy/hash that resolved XML and record the exact Nav2 package version; citing the repository config alone is insufficient provenance.
- Importing BARN worlds into Unity would require a conversion and equivalence study for geometry, scale, materials, collision contacts, sensor placement, robot footprint, start/goal coordinates, and physics. That is clearly beyond one day and risks changing CRANE physics solely to accommodate an external benchmark.

For RQ1, BARN could eventually supply shared episodes from which A/B/C/D/E presentations are derived, but it adds no unique representation comparison. For RQ2, it can stress final-text verification after annotations exist. For RQ3/RQ4, naturally insufficient traces are useful only if omission/contradiction is deliberately controlled and answerability is annotated. Those additions, not simulator startup, dominate the scientific integration effort.

## One-day gate and stop conditions

If the core CRANE pilot is healthy and an external BARN check is still desired, run a separate one-day spike; do not modify CRANE or the sealed main study.

### Minimum acceptance within the timebox

By hour 2:

- resolve redistribution/license constraints sufficiently for local-only evaluation;
- build a digest-pinned separate image or isolated workspace without altering the pinned CRANE image;
- record exact package versions, image digest, repository commit, and world hash.

By hour 4:

- complete one headless static-world run twice from a clean reset;
- bound the pre-movement wait externally;
- capture Gazebo collision, harness timeout, Nav2 goal/feedback/result/status, `BehaviorTreeLog`, recovery count, BT XML/hash, and configuration hashes;
- demonstrate that episode IDs join all artifacts and that `/clock` reset does not contaminate the next run.

By hour 6:

- reconcile and test BARN proximity outcome versus Nav2 terminal outcome;
- patch or wrap the skipped-world and score inconsistencies without changing official score semantics;
- validate at least one success and one genuine non-success, or stop if the selected pilot worlds do not yield mechanism diversity.

By hour 8:

- produce robot-visible and evaluator-only artifacts that pass the same governance/validation checks as CRANE;
- document any exclusions and estimate real-time throughput for a powered independent-episode target.

### Immediate stop conditions

Stop and retain this **NO-GO** if any of the following occurs:

- Clearpath/Gazebo dependencies cannot be reproducibly built by hour 2;
- the observer cannot receive BT/action evidence in the isolated BARN graph by hour 4;
- episode reset or action-versus-harness status cannot be made unambiguous by hour 6;
- using the assets would require redistribution without a resolved license;
- a useful sample would consume more than one day of engineering before collection starts;
- the work would delay CRANE pilot collection, study freeze, annotation, or power planning.

## Final recommendation

**Do not integrate BARN directly now.** Adopt its difficulty-stratified, scenario-level split and repeated-trial principles in the CRANE benchmark. Record BARN as a high-quality deferred external stress-test candidate. If the core study is ahead of schedule, attempt only the isolated smoke/capture spike above; success there authorizes a small external-validity appendix, not migration of the primary experiment.

Status:

- **RESEARCHED:** official 2026 protocol and ROS 2 repository source/configuration.
- **NOT_RUN:** BARN build, Gazebo trial, Nav2/BT capture, reset validation, or throughput measurement.
- **NO-GO:** direct integration under the current one-day bound.
- **GO:** methodological reuse with no simulator/code import.

## Primary sources

- Official challenge page: <https://people.cs.gmu.edu/~xiao/Research/BARN_Challenge/BARN_Challenge26.html>
- Official ICRA 2026 competition listing: <https://2026.ieee-icra.org/program/competitions/#thebarnchallenge>
- Final organizer report: <https://people.cs.gmu.edu/~xiao/papers/barn26_report.pdf>
- Officially linked ROS 2 evaluator, audited commit: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/tree/d6c575b51e477bd524d634e12cffeb34036fcd1e>
- ROS 2 evaluator README: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/README.md>
- Container definition: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/Singularityfile.def>
- BARN/Nav2 launch: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/BARN_runner.launch.py>
- Nav2 bringup/config: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/launch/nav2_bringup.launch.py>, <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/nav2.yaml>
- Robot config and simulator bridge: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/config/robot.yaml>, <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/gazebo_simulation.py>
- Runner/evaluation scripts: <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/jackal_helper/scripts/barn_runner.py>, <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/test.sh>, <https://github.com/Saadmaghani/The-Barn-Challenge-Ros2/blob/d6c575b51e477bd524d634e12cffeb34036fcd1e/report_test.py>
