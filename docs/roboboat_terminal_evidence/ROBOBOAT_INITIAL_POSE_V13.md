# Requested physical start diversity: development v13

This remains development. Confirmation is unfrozen; no method pair, confirmation or replication observation is scored. The v12 clock-repaired collection remains the live qualified collection version, unchanged by this work.

## Configuration and software extension

The v2 population varied routes/goals but retained a fixed physical start. A separate copy at `/home/lunarz/worktrees/roboboat-start-pose-v13/crane_ml` adds only two C# files (initializer and tests), with their Unity metadata. All 2,580 parent source/configuration bindings remain unchanged. The explicit option `--crane-roboboat-start-pose x,y,yaw` accepts finite ROS odom positions in metres and canonical yaw in radians. No option means no pose application. The override is restricted to the RoboBoat course and requires exactly one active boat controller and a supported root physics body.

It initializes a level planar heading, retains the scene's vertical position, sets root transform and physics pose before Start/physics, and clears initial root momentum. This intentionally changes initial configuration; it is not a physics-equivalence claim. It does not alter water, controller, sensor or navigation source code. Descendant local geometry is retained in the actual-course test. Any future collection on it belongs to the revised v13 platform and requires separately declared technical admission and operational qualification.

The original test caught an immediate scene-transform readback mismatch with `TeleportRoot` alone. Original source and failed NUnit report remain. The corrected implementation explicitly sets the transform as well as teleporting the physics root. All 17 initial-pose tests and all 68 EditMode tests pass, covering invariant negative-number parsing, invalid/duplicate inputs, frame/yaw conversion, height, momentum, actual root articulation/child geometry and non-RoboBoat rejection.

The build succeeded. Its exhaustive 372-file manifest binds all 2,584 current source files; every prebuild binding still matches afterward. Compiled-source audit v3 directly matches the new initializer with assembly/PDB identity and source checksums. Explicit independently bound v10 and v9 compiler-root mappings retain identical-byte cached sources; vendor/unavailable records remain unresolved. Deployment wiring and complete platform reliability are separate claims.

## Fresh candidate population

`generate_roboboat_population_v3.py` creates an unexecuted requested-start population. Seed42006 supplies 120 geometry draws, 240 paired tolerance variants and 20 draws per each existing six route families. It samples start x within0.45m of the existing route anchor, start y within1.5m and yaw in[-1,1]rad, alongside independent route/goal draws. Path starts connect smoothly from requested positions, and actual chords remain at most0.20m. The fixed berth/public task requirements are retained.

The immutable upstream v2 generation and paths are preserved; successor routes use separate filenames. Three generator tests pass for paired identities, route/task coherence, deterministic draws, finite/bounded paths, Int32 seed collision resolution and unexecuted status. The identity audit checks the explicitly bound prior development registries and finds zero identity, seed or exact-goal collisions and 120 distinct requested initial poses. These checks do not establish clearance, feasibility, realized physical state or probabilistic independence. Generation adds zero collected N. The pool is not a ceiling. The v12 collector rejects its candidate status.

## Runtime probes and retained failures

The first three-case headless probe was misconfigured: root supplied the maximum-delta-time override without its required frame-audit output. All cases exited2; the guard's exact source/error is retained. The corrected headless probe supplied that output. Both nondefault cases logged positions/yaws matching requests on the actual root body, but all three exited3 because the existing `train-cpu` guard rejects aquatic scenes: HDRP water requires graphics. No benchmark completed. Both fixed batches remain failures and neither qualifies the new platform. Raw logs/native dumps remain local and excluded from Git.

Rendered successor v4 declares default startup and two offset/heading cases once using the supported train-gpu graphics path, ROS transport disabled,8s duration/2s warmup, and zero independent N. It uses a fresh nonce-owned player bundle/window, checks placement/cleanup receipts, and signals the wrapper gracefully on timeout so owned compositor cleanup can run. No completed probe is yet claimed.

It is queued under exact session51128, waiting on `/tmp/crane-roboboat-population-render.lock` behind collection49910. The wrapper saves/restores the global `render_unfocused_fps` value; simultaneous uncoordinated restores would be unsafe. While queued it changes no compositor state and starts no Unity attempt. This concrete shared-state issue must be repaired/qualified before scaling rendered workers. Source/build inputs are revalidated after acquisition. Earlier prepared rendered v3 was never executed; v4 supersedes its timeout handling.

Even a successful rendered startup probe is narrower than navigation/ROS/action-trace qualification. That latter qualification and version-matched common evidence/source preparation must precede new start-varied study recordings. Repeats and engineering probes never increase independent N.

Artifacts: `artifacts/roboboat-start-pose-v13/`; `artifacts/roboboat-start-varied-development-population-v3-42006/`; retained failed `roboboat-start-pose-headless-probe-v13-001` and `-002`; queued `roboboat-start-pose-rendered-probe-v13-004`. Latest authoritative collection counts and handles are in campaign statusv29.
