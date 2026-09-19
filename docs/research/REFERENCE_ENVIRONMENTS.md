# Reference environments for CRANE

**Status:** source audit completed 2026-09-19. The audit itself did not execute upstream
simulators; CRANE-native implementation tests are recorded separately in `docs/EXPERIMENTS.md`.
**Purpose:** identify small, reproducible navigation environments that CRANE can use without confusing technical availability with permission to redistribute assets. This is an engineering review, not legal advice.

## Recommendation

Do not import a complete foreign simulator or a photorealistic third-party scene for the TRUSTMORE study. The lowest-risk path is to build small CRANE-native scenes from primitives or assets whose licenses explicitly cover the files being copied, and to use upstream environments in their native simulators only when they add a useful cross-simulator check.

For every scenario, retain one canonical geometry description and derive four explicitly versioned products from it:

1. visual geometry and materials;
2. simplified, deterministic collision geometry;
3. the Nav2 occupancy/costmap input;
4. evaluator-only truth (faults, hidden obstacle state, and expected propositions).

Hash the canonical input and every derived product. Record conversion code and parameters. A visual mesh must not silently become the experimental collision truth: separate colliders reduce physics instability and make discrepancies auditable. The robot-visible package must exclude evaluator-only truth.

### Triage

| Source | Technically useful now | Reuse classification | Smallest CRANE path |
|---|---|---|---|
| Unity Nav2/SLAM example | Unity scene/robot organization and a small TurtleBot3/Nav2 reference | Code/configuration is Apache-2.0; Warehouse art is **not cleared by the inspected sources** | Recreate the layout with CRANE primitives; optionally run the pinned upstream package without redistributing its art |
| Clearpath simulator | Native ROS 2 Jazzy/Gazebo Harmonic office and pipeline worlds | BSD-3-Clause repository; retain notices, but audit/confirm asset provenance before converting or rebundling art | Run the tagged upstream Gazebo package beside the same capture pipeline |
| F1TENTH maps | Compact occupancy-map reference cases | Official racetrack collection is GPL-3.0 with additional upstream provenance caveats; gym is MIT but map provenance is undocumented | Proceduralize original layouts; optionally evaluate against externally downloaded maps without redistributing them |
| PX4 x500 worlds | Small SDF worlds with walls, markers, and wind; useful geometry patterns | Pinned Gazebo resource repository and x500 model have BSD-3-Clause licenses | Translate simple, attributable SDF primitives; retain notices and CRANE's existing physics |
| AWSIM | Architecture and scene/lifecycle patterns | Code extensions are Apache-2.0; many assets are CC BY-NC; docs have an additional hosting restriction | Design reference only for this deadline |
| Flightmare | Rendering/physics separation and compact scene-selection pattern | Core repositories say MIT, but the shipped Industrial art is acknowledged Asset Store content | Design reference only unless each art asset's upstream terms are separately cleared |

## Unity Robotics Nav2/SLAM example

**Pinned revision:** [`a0c9846eaa04f4800d3521639990e74c3b287ceb`](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/tree/a0c9846eaa04f4800d3521639990e74c3b287ceb) (2021-10-01; no release tag found).

The example targets Unity 2020.3.11f1 and ROS 2 Galactic, with a TurtleBot3 Waffle Pi and Nav2/SLAM Toolbox—not CRANE's Unity 6 and ROS 2 Jazzy stack ([README](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/blob/a0c9846eaa04f4800d3521639990e74c3b287ceb/README.md), [Dockerfile](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/blob/a0c9846eaa04f4800d3521639990e74c3b287ceb/ros2_docker/Dockerfile)). Unity supplies simulated time, TF, and an explicitly perfect/instantaneous/noiseless 2-D lidar. The robot is URDF-imported and then manually adjusts colliders and adds the laser. `SimpleWarehouseScene` is generated from the Robotics Warehouse package; the ROS side is mostly standard Nav2 and SLAM Toolbox ([implementation explanation](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/blob/a0c9846eaa04f4800d3521639990e74c3b287ceb/readmes/explanation.md)). Its documented portable seam is useful: the configured TurtleBot prefab may be placed in another mostly flat scene whose floor and obstacles the lidar can detect ([custom visualization guide](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/blob/a0c9846eaa04f4800d3521639990e74c3b287ceb/readmes/custom_viz.md)).

The example repository is Apache-2.0 and lists TurtleBot3 (Apache-2.0) and FreeCam (MIT) in its [third-party notices](https://github.com/Unity-Technologies/Robotics-Nav2-SLAM-Example/blob/a0c9846eaa04f4800d3521639990e74c3b287ceb/Third%20Party%20Notices.md). However, its lockfile pins Robotics Warehouse to [`9fa61061d31b30686573bd2e0213f049738a8949`](https://github.com/Unity-Technologies/Robotics-Warehouse/tree/9fa61061d31b30686573bd2e0213f049738a8949), and that package has no license field in [`package.json`](https://github.com/Unity-Technologies/Robotics-Warehouse/blob/9fa61061d31b30686573bd2e0213f049738a8949/com.unity.robotics.warehouse/package.json) and no LICENSE/NOTICE file was found. The example's Apache license therefore must not be assumed to grant redistribution rights to Warehouse meshes or textures.

**Decision:** reuse concepts, ROS interfaces, and appropriately noticed example code. For an exact upstream experiment, consume the Warehouse dependency at its locked revision rather than copying it. For a distributable CRANE scene, rebuild a small warehouse-like arrangement from primitives. Porting the old project wholesale is not justified.

## Clearpath simulator

**Reproducible release:** tag [`2.9.4`](https://github.com/clearpathrobotics/clearpath_simulator/tree/ee098ad6f67b4e35d77841ed6f004b8f86cd77e4), commit `ee098ad6f67b4e35d77841ed6f004b8f86cd77e4` (2026-08-07). The audited `jazzy` branch head was `590a45118c599c08abdf3bd3d02d5fa7a8af9a49` (2026-08-25); prefer the tag unless a later fix is required.

This is a native ROS 2 Jazzy/Gazebo Harmonic option. It provides `office`, `pipeline`, `construction`, `orchard`, `solar_farm`, and `warehouse` launch choices. Office supplies narrow corridors, doors, meeting rooms, and a loading area; pipeline supplies uneven terrain, river/bridge, cave, solar, and pipeline features ([README](https://github.com/clearpathrobotics/clearpath_simulator/blob/ee098ad6f67b4e35d77841ed6f004b8f86cd77e4/README.md), [simulation launch](https://github.com/clearpathrobotics/clearpath_simulator/blob/ee098ad6f67b4e35d77841ed6f004b8f86cd77e4/clearpath_gz/launch/simulation.launch.py)). The launcher exposes installed world and mesh paths through `GZ_SIM_RESOURCE_PATH` and bridges `/clock` ([Gazebo launch](https://github.com/clearpathrobotics/clearpath_simulator/blob/ee098ad6f67b4e35d77841ed6f004b8f86cd77e4/clearpath_gz/launch/gz_sim.launch.py)).

The root [BSD-3-Clause license](https://github.com/clearpathrobotics/clearpath_simulator/blob/ee098ad6f67b4e35d77841ed6f004b8f86cd77e4/LICENSE) permits redistribution with notice/disclaimer and no endorsement; `package.xml` also declares BSD. The world-import commit credits Dave Niewinski with creating the meshes and records renamed earlier Clearpath worlds ([commit `adb42a6`](https://github.com/clearpathrobotics/clearpath_simulator/commit/adb42a66d18156ca525e267ce28b6ece27a942d9)). No asset-level provenance/third-party inventory was found, so the inspected source does not support stronger claims about every texture. Some source files also carry Apache-2.0 headers; preserve file-level notices.

**Decision/update:** native tagged Gazebo plus capture remains the cleanest cross-simulator check.
A narrow offline Unity proof was nevertheless completed for `pipeline`: local resources are hashed,
collision and visual roles are instantiated separately, DAE hierarchy is retained, STL is converted
deterministically to OBJ, and generated assets remain outside Git. This does not resolve native
Gazebo equivalence or asset-level provenance beyond the repository license; do not bundle the
generated assets without further confirmation.

## F1TENTH occupancy maps

**Racetrack collection:** tag `v1.0.0`, commit [`b95c4eff766f6367d66b310ea20cd2c9563712c0`](https://github.com/f1tenth/f1tenth_racetracks/tree/b95c4eff766f6367d66b310ea20cd2c9563712c0).
**Simulator:** audited head [`4fdb9c7e6fb7c701290f4dc18377d07c1681724f`](https://github.com/f1tenth/f1tenth_gym/tree/4fdb9c7e6fb7c701290f4dc18377d07c1681724f).

The official racetrack collection contains 23 track directories, generally with a grayscale occupancy PNG, ROS-style YAML, centerline CSV, raceline CSV, and DonkeySim waypoints ([format and provenance](https://github.com/f1tenth/f1tenth_racetracks/blob/b95c4eff766f6367d66b310ea20cd2c9563712c0/README.md)). A typical YAML records image, metres-per-pixel resolution, `[x,y,yaw]` origin, negate, and occupied/free thresholds ([Austin example](https://github.com/f1tenth/f1tenth_racetracks/blob/b95c4eff766f6367d66b310ea20cd2c9563712c0/Austin/Austin_map.yaml)). These products are not interchangeable: occupancy defines free/occupied space; a centerline is a planning reference, not collision truth.

The collection is [GPL-3.0](https://github.com/f1tenth/f1tenth_racetracks/blob/b95c4eff766f6367d66b310ea20cd2c9563712c0/LICENSE). Its README says it derives from TUMFTM's racetrack database, whose inspected revision `e59595d1f3573b30d1ded6a08984935b957688e0` is LGPL-3.0 and documents centerlines from OpenStreetMap and widths measured from satellite imagery ([upstream README](https://github.com/TUMFTM/racetrack-database/blob/e59595d1f3573b30d1ded6a08984935b957688e0/README.md), [license](https://github.com/TUMFTM/racetrack-database/blob/e59595d1f3573b30d1ded6a08984935b957688e0/LICENSE)). Asset-level OSM attribution is not recorded in the F1TENTH collection, and real-circuit layouts/names introduce further provenance questions. Popularity does not resolve them.

`f1tenth_gym` is [MIT licensed](https://github.com/f1tenth/f1tenth_gym/blob/4fdb9c7e6fb7c701290f4dc18377d07c1681724f/LICENSE) and bundles several binary maps, but no map-specific provenance was found. Its loader behavior is a useful executable specification: resolution is metres/pixel, origin x/y follows the ROS bottom-left convention, the image is vertically flipped, pixels at or below 128 are occupied, and pixels above 128 are free ([documentation](https://github.com/f1tenth/f1tenth_gym/blob/4fdb9c7e6fb7c701290f4dc18377d07c1681724f/docs/customized_usage.rst), [loader](https://github.com/f1tenth/f1tenth_gym/blob/4fdb9c7e6fb7c701290f4dc18377d07c1681724f/gym/f110_gym/envs/laser_models.py)).

**Decision:** use these as format/code and external-evaluation references. Do not commit or convert the GPL tracks into the permissively licensed CRANE repository without an explicit GPL/NOTICE decision and provenance review. Generate original procedural loop/corridor geometry instead. If an external evaluation downloads maps separately, pin and hash inputs and record YAML, coordinate convention, crop/scale/inflation, extrusion height, and start/goal.

## PX4 x500 worlds

**PX4-Autopilot revision:** [`c4e4ef98e9d75063bf3d53ebb2716221ee7505ae`](https://github.com/PX4/PX4-Autopilot/tree/c4e4ef98e9d75063bf3d53ebb2716221ee7505ae).
**Pinned Gazebo resources:** submodule commit [`bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9`](https://github.com/PX4/PX4-gazebo-models/tree/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9).

PX4's Gazebo resources provide compact test worlds for walls/obstacles, an ArUco marker, and wind. `walls.sdf` contains four static boxes with matching primitive box visual and collision dimensions ([source](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/worlds/walls.sdf)). This is a clean geometry reference, although CRANE should still author separate renderer and collider objects so visual changes cannot alter collision silently.

`aruco.sdf` is a ground plane plus the `arucotag` model ([world](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/worlds/aruco.sdf)); the tag is a 0.5 m textured plane with no collision ([model](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/models/arucotag/model.sdf)). A CRANE equivalent must remain a render-only landmark rather than becoming an obstacle. `windy.sdf` declares `(5,2,0)` world wind but only enables wind on the ground-plane link ([source](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/worlds/windy.sdf)). The x500 model does not supply evidence in these files of an aerodynamic wind plugin, so the launch command documented by PX4 must not be reported as proof of physically meaningful wind force on the vehicle ([PX4 Gazebo documentation](https://github.com/PX4/PX4-Autopilot/blob/c4e4ef98e9d75063bf3d53ebb2716221ee7505ae/docs/en/sim_gazebo_gz/index.md)). Use CRANE's existing validated `WindForce` and measure its effect instead.

The x500 base itself demonstrates explicit separation: a visual mesh is paired with five primitive box collisions, and rotors use STL visuals with thin box collisions ([model SDF](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/models/x500_base/model.sdf)). This is a useful pattern, not a reason to replace CRANE vehicle dynamics.

The pinned Gazebo repository is [BSD-3-Clause](https://github.com/PX4/PX4-gazebo-models/blob/bb0b9cf974acf4f1bcb5f5fcf80b88841562dea9/LICENSE), and `x500_base` carries a separate BSD-3-Clause Rudis Laboratories license. Retain repository- and model-level notices, copyright, disclaimer, and no-endorsement terms. External resources resolved by URI still require separate checking.

**Decision:** first reproduce the simple wall boxes in a small procedural Unity descriptor; optionally add a render-only ArUco landmark if vision questions matter. Convert Gazebo/ROS ENU metres with CRANE's established mapping, not ad hoc axes. Treat wind `(5,2,0)` only as a candidate scenario parameter and validate displacement. Do not import x500 physics or claim Gazebo equivalence.

## AWSIM

**Audited revision:** [`46a68528b330fbcb487f9d2f3e15126990edfe0b`](https://github.com/autowarefoundation/AWSIM/tree/46a68528b330fbcb487f9d2f3e15126990edfe0b) (2026-09-02). AWSIM transferred from TIER IV to the Autoware Foundation on 2026-05-07. Stable alternatives at audit time were `v2.0.1` (`9e55528131a1df8de703d997518251491cb4adf6`) and `v2.0.0` (`6d558af38106c9c45095ff125198059423042af8`).

AWSIM uses Unity 6000.0.61f1 with HDRP/URP 17.0.4, native ROS 2 communications, and Autoware vehicle/sensor interfaces. Its documented layering is Scene → UI → Usecase → Entity → Common, with scene classes controlling initialization/update order rather than broadly depending on Unity lifecycle callbacks ([architecture](https://github.com/autowarefoundation/AWSIM/blob/46a68528b330fbcb487f9d2f3e15126990edfe0b/docs/DeveloperGuide/Architecture/index.md), [directory guide](https://github.com/autowarefoundation/AWSIM/blob/46a68528b330fbcb487f9d2f3e15126990edfe0b/docs/DeveloperGuide/Directory/index.md)). Those are useful design references for deterministic scenario ownership.

The [license](https://github.com/autowarefoundation/AWSIM/blob/46a68528b330fbcb487f9d2f3e15126990edfe0b/LICENSE) is file-type dependent: AWSIM-specific `.cs`, `.compute`, and `.xml` extensions are Apache-2.0; listed asset formats including `.fbx`, `.pcd`, `.osm`, `.png`, `.anim`, `.unitypackage`, and `.x86_64` are CC BY-NC. It also prohibits public hosting of `/docs` outside the official site. The principal Shinjuku environment is separately downloaded/imported into `Assets/Awsim/Externals`, is excluded from the source repository, and is CC BY-NC 4.0 with an explicit noncommercial restriction ([setup](https://github.com/autowarefoundation/AWSIM/blob/46a68528b330fbcb487f9d2f3e15126990edfe0b/docs/DeveloperGuide/SetupUnityProject/index.md), [downloads](https://github.com/autowarefoundation/AWSIM/blob/46a68528b330fbcb487f9d2f3e15126990edfe0b/docs/Downloads/index.md)).

**Decision:** use AWSIM's architectural ideas and, if needed, individually verified Apache-2.0 code patterns. Do not copy Shinjuku or other CC BY-NC assets into CRANE without explicitly accepting and tracking attribution/noncommercial constraints. Do not republish AWSIM documentation. Full scene integration is too costly for the present study.

## Flightmare

**Core revision:** [`d4218aedac18cbe9364a0a0df10ab992c4b65e4f`](https://github.com/uzh-rpg/flightmare/tree/d4218aedac18cbe9364a0a0df10ab992c4b65e4f) (2023-05-15).
**Unity renderer revision:** [`203351ffca0bf10ea64193456b3505abe9bfef85`](https://github.com/uzh-rpg/flightmare_unity/tree/203351ffca0bf10ea64193456b3505abe9bfef85) (2021-04-14; no tag found).

Flightmare deliberately separates a Unity rendering engine from a C++ physics/dynamics engine and connects them through its rendering bridge. The core contains `flightlib`, `flightrender`, `flightrl`, and ROS 1 `flightros`; it is not ROS 2/Jazzy-native. Documentation exposes INDUSTRIAL, WAREHOUSE, GARAGE, and NATUREFOREST selectors, plus point-cloud export to PLY ([standalone guide](https://github.com/uzh-rpg/flightmare/blob/d4218aedac18cbe9364a0a0df10ab992c4b65e4f/docs/source/building_flightmare_binary/standalone.rst), [point-cloud guide](https://github.com/uzh-rpg/flightmare/blob/d4218aedac18cbe9364a0a0df10ab992c4b65e4f/docs/source/first_steps/pointcloud.rst)). The publicly inspected Unity repository itself uses Unity 2020.1.10f1 and contains only the `Industrial` environment directory plus associated scenes; therefore the four documented environment names should not be read as four independently redistributable art packages in that repository.

Both inspected repositories contain MIT license files. Nevertheless, the Unity renderer's own [README](https://github.com/uzh-rpg/flightmare_unity/blob/203351ffca0bf10ea64193456b3505abe9bfef85/README.md) says its shipped Industrial demo was created by Dmitrii Kutsenko and comes from the Unity Asset Store package “RPG/FPS Game Assets for PC/Mobile (Industrial Set v2.0).” The core documentation also invites users to add Asset Store scenes ([acknowledgments](https://github.com/uzh-rpg/flightmare/blob/d4218aedac18cbe9364a0a0df10ab992c4b65e4f/docs/source/getting_started/readme.rst)). A repository-level MIT file is not sufficient evidence that CRANE may relicense or redistribute third-party Asset Store art.

**Decision:** reuse the rendering/physics separation as a design reference and individually identified MIT bridge code if it saves work. Treat environment art as design-reference only until the underlying Asset Store terms and each asset's provenance are resolved. An old Unity 2020/ROS 1 bridge is not a sensible integration target for the submission deadline.

## Integration rules for the benchmark

1. **Prefer provenance over appearance.** A plain primitive scene with clear rights and stable collision is more valuable than an attractive scene whose redistribution or geometry is ambiguous.
2. **Pin immutable inputs.** Record repository URL, commit, file path, content hash, license/notice snapshot, and any external model URI.
3. **Make derivation executable.** Generate render, collision, and occupancy artifacts from canonical geometry with a checked-in command/configuration, and test their extents and transforms.
4. **Never infer sensed or consumed evidence from world geometry.** Evaluator truth may say an obstacle exists; an explanation may say the robot observed it only when the captured robot-visible record establishes that fact.
5. **Keep simulator comparisons narrow.** Clearpath can test whether capture/explanation behavior generalizes to a native Jazzy/Harmonic environment. F1TENTH/PX4/AWSIM/Flightmare should not displace CRANE episode collection unless a pilot exposes a concrete validity gap.
6. **Retain notices in artifacts.** Dataset manifests should name source and transformation without leaking evaluator-only labels into model-visible paths or metadata.

## Implemented first increment and next choice

The first increment implements a CRANE-native warehouse/office scene, a deterministic F1TENTH
PNG/YAML boundary-to-collider generator, the four pinned primitive boxes from PX4 `walls`, a
render-only ArUco landmark, and measured deterministic response to the pinned windy vector.
Camera tag detection and physical wind calibration remain unvalidated. The Clearpath pipeline
offline import has passed structural/contact validation; native Jazzy/Harmonic, ROS sensor, and
Nav2 route checks remain gated on value to the primary explanation study.

This choice strengthens explanation fidelity: the study can prove which geometry and hidden interventions existed while still restricting generated explanations to the evidence the robot actually received.
