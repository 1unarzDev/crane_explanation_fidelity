# Terminal-distance development population v4

The unexecuted seed42007 candidate pool contains180 geometry draws and360 paired tolerance variants. Six terminal route families cross three reference-curve arc-distance bands(2–5,5–9,9–14m), with ten draws per stratum. This planning point is not a sample ceiling. Generation reads no outcomes and adds zero collected N.

The generator crops bounded legacy reference routes from their goals, then constructs controlled terminal alternatives. Requested physical start matches the first path point; heading offsets are canonical radians. Goal/task requirements, berth, tolerance pairing, controller, sensing and physics settings are preserved. Direct-goal rows have no executed path file; their curve is design metadata. Reference arc distance is neither Euclidean start distance nor actual executed path length.

Three generator tests passed, including180-draw balance, immutable task/pairs, geometry spacing, reproducibility and rejection of confirmation promotion. The bound identity audit includes all documented prior registries and the unexecuted v3 seed42006 artifact pool: zero identity, seed or exact-goal collisions;180 distinct requested starts. Exact duplicate checks do not establish probabilistic independence, clearance or feasibility.

Artifacts are in `artifacts/roboboat-terminal-distance-development-population-v4-42007/`: registry, upstream v2 generation, contracts, identity audit and engineering QA. Runtime paths are versioned separately in the crane_ml submodule. The v12 collector rejects the candidate status. Exact-build/start-pose receipts and full navigation/trace qualification are required before collection.

Shorter paths alone do not improve current collection throughput: the launcher waits for the fixed340s worker cap. No throughput gain is asserted.

# Capture-window development candidate v15

`analysis/roboboat_fixture_capture_v15/nav2_follow_path_fixture.py` is an isolated copy of the currently bound ROS fixture. Its lineage binds both source versions. One timer condition changes: the action deadline applies while a result is pending; a received result can complete the full requested post-result/BT-drain window. Three tests execute the actual candidate timer method and cover a late terminal result, unchanged pending-action timeout, longer drain, and retained aborted/canceled statuses.

The live launcher and running or queued builds are unchanged. The candidate is unexecuted and operationally unqualified. A future launcher/worker completion protocol must publish completion only after complete fixture output/process shutdown, preserve action/trace counters and footer conservation, and retain technical failures. Uniform capture-complete termination is a separate implementation and qualification step; it cannot depend on method scores.
