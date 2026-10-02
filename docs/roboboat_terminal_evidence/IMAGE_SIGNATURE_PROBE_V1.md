# Optional image-signature instrumentation probe, development v5

Prepared prospectively; **not launched** by this task. The independent v4 player-affinity collector remains unchanged. V5 should run only after the shared rendering lock is available, using untouched rows in the existing population capture root. It must not create a new output root to replay earlier registry identities.

Hypothesis: full-byte benchmark checksum work contributes avoidable main-thread latency. Removing that optional measurement should shorten `CRANE.ROS.CreateMessage`/depth-publish tails and, if it contributes to the freshness failure, reduce stale observations while preserving physical sensing and navigation. This is a separate instrumentation intervention, not an established root cause or repair.

## Exact intervention

`analysis/run_roboboat_population_development_v5.py` executes the original immutable physical player **directly**, without the v4 CPU-affinity wrapper. Original 640x360 presentation, unrestricted default host affinity, timeScale1, fixed 1280x720 depth render texture, sensor cadence, task/configuration, physics, ROS publishing and controller settings are preserved. The sole extra Unity argument is `--crane-no-signatures`, forwarded through `CRANE_NAV2_UNITY_EXTRA_ARGS` by the inherited fixture and worker launchers. Inherited CRANE overrides are removed before declaring the launch.

The physical binary SHA-256 is checked against `a7ad5b156bd9a1232544ff6fc12e5f863d8f1f2348c5b141f5c3d4230e5be292` before each fresh launch. Restricted inherited CPU affinity fails closed rather than silently combining the v4 and v5 interventions.

Available source inspection finds the flag read only in `CraneBenchmarkRunner.ParseArguments`; it sets the benchmark's `imageSignatures` field and `CraneRuntimeMetrics.CaptureImageSignatures`. The latter is used only to guard the byte-traversal FNV loop inside `ReportImage`. Image counts, dimensions, byte totals and acquisition ticks continue updating. `ROSDepthCameraAsync.CreateMessage` continues constructing and returning the actual data-bearing float32 message; publishing, readbacks, payload copies, row flipping, fixed sensor dimensions and physics are unaffected by that guard. Distinct image payloads remain allocated because asynchronously queued senders retain them.

The available benchmark `valid` expression, inherited collector technical checks, reset-summary validation, v2 exporter, certificates and independent reference contain no image-checksum admission requirement. The probe therefore removes no existing scientific validity gate. Available source bindings are retained for inspection; the immutable compiled-player binding and observed `imageSignatures=false` check are required runtime attestations. A mismatch fails the attempt.

## Retention and admission

Probe/attempt intents bind registry, collector, launcher, display wrapper, inspected instrumentation sources and original physical binary. Each records v5 version, exact flag, default CPU set and actual launched command/environment values. Sources and older attempts are never edited.

The default prospective pilot maximum is four new physical attempts, recorded in the probe intent; it is not a study sample ceiling. Stop after two consecutive fresh technical failures. Old failures do not enter that count. Existing attempt directories are skipped; a direct call for a retained final attempt returns that record, and unresolved attempt directories cannot be reissued. Use the common capture root across versions to preserve this identity exclusion.

All inherited strict worker, sensor, transport, bounded command-lag and trajectory checks remain active. Added operational checks require `imageSignatures is False`, actual640x360 display, acquired1280x720 depth, one enabled sensor camera with no spectator/water-driver camera, and timeScale1. Stale observations or rejected/stale commands still invalidate the recording. Successful admission uses the corrected v2 projection/export namespace and supplemental provenance publisher. It adds no confirmatory or replication N.

## Limitations and decision rule

Disabling content signatures removes the benchmark's full-byte image-checksum diagnostics. Although a checksum field still updates from a constant accumulator, it no longer fingerprints image content and must not be interpreted as one. Counts/dimensions and real ROS data continue, but an image-content corruption investigation cannot rely on those disabled signatures. V5 recordings require explicit instrumentation-version labeling.

One clean attempt would establish operability, not a resolved cause or a reliable invalid-run rate. Compare tails and failures across fresh development rows; do not use outcome desirability to admit a recording. If staleness persists, preserve the failures and investigate boundary timing or resource isolation without changing queues, gates or scientific sensing.

Prepared validation: `PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_population_development_v5.py` passes12 tests. These mock the actual collector launch boundary, verify the exact command and flag/environment forwarding, reject stale depth/signature/resolution/camera changes, check original binary and default-affinity requirements, and verify untouched-row selection/versioned prospective intent/two-new-failure stopping. They do not execute Unity or claim runtime equivalence. No GPU or provider call was made.
