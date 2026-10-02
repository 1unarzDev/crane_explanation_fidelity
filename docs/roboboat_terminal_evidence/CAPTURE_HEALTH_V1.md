# Capture freshness diagnosis, development population 42001

This audit is read-only. It preserves all original attempts, raw records, strict admission gates and scientific identities. It does not salvage either genuinely invalid recording or establish a repaired root cause. All observations remain development evidence.

The diagnosing-bugs workflow is applied through retained-trace replay. The deterministic feedback command is:

```bash
python analysis/audit_roboboat_capture_health_v1.py artifacts/roboboat-population-development-42001/captures/*/worker-0
```

It completes in seconds and exits **1** on the retained batch. The first recording is healthy under this limited worker audit. The second reports `staleActions_not_zero`, `rejectedActions_not_zero`, and `worker_valid_not_true`. The third reports `staleObservations_not_zero`, `trace_staleObservations_not_zero`, and `worker_valid_not_true`. The audit binds both raw inputs by SHA-256 and checks timestamp/counter monotonicity, trace completeness, terminal-counter agreement and sampled maximum age. It does not replace the collector's transport, fixture and trajectory admission checks.

Four targeted tests pass via `python -m pytest -q tests/test_audit_roboboat_capture_health_v1.py`. These test the audit's ability to catch a transient stale burst despite a falsely clean terminal counter, action rejection, truncation and malformed time ordering. They do not reproduce asynchronous Unity scheduling or prove a runtime fix.

## Retained evidence

| Recording | Worker verdict | Maximum sampled observation age | Freshness issue |
|---|---|---:|---|
| `boat-geom-42001-00001-v1` | valid | 5 ticks | none |
| `boat-geom-42001-00001-v2` | invalid | 5 ticks | 1 stale/rejected action |
| `boat-geom-42001-00002-v1` | invalid | 17 ticks | 3 stale observations |

The wide-turn stale count increases from zero at 172.00265 simulated seconds to three at 173.02990. The precise event times are only localized to that interval; queue age at the latter sample is 17 ticks. The trace is sampled once per simulated second. The first stale events precede navigation termination (246.23 seconds), so removing post-terminal capture would not fix this failure.

The issue persists in a minimized trace inspection of those two adjacent samples; all body/water payloads can be removed without changing the counter verdict. This localizes the symptom, not the scheduling cause. The actual retained readback path is not replayable in Python.

Mean GPU-frame times (13.35, 13.28, 13.08 ms respectively) and real-time factors near one cannot exclude rare stalls. The wide-turn recording has a 77.04 ms maximum LiDAR marker duration, compared with 24.82 and 17.16 ms in the other recordings. Those summary maxima have no event timestamps, so they cannot establish temporal causation.

`Assets/Scripts/Sensors/Vision/RosDepthCameraAsync.cs` reports stale observations when an acquisition becomes due with both allowed asynchronous readbacks still pending (`MaxPendingReadbacks=2`). The failed recording acquires 5097 depth images versus 5100 in both other recordings. This is consistent with three skipped acquisitions. Increasing the queue or suppressing the counter would change the sensor contract and is not the proposed repair.

## Ranked hypotheses and discriminating probes

1. Transient GPU/readback starvation: reducing presentation dimensions with unchanged fixed depth RT, cadence and physical settings should reduce stale bursts if presentation cost contributes. Measure tail/queue behavior, not only mean GPU time.
2. CPU/GC scheduling stalls: stale intervals should align with long main-thread, LiDAR, copying or collection events and persist when presentation work shrinks. The current trace lacks frame-level timing needed to distinguish this from GPU starvation.
3. ROS/executor or transport scheduling stall: source-to-application action lag should worsen while depth stays clean, consistent with the second recording. Isolated ROS resources and timestamped source/receive/apply tracing are the relevant probe. Do not loosen bounded lag.
4. Acquisition/reset metadata lifecycle: callback/request tracing would show overlapping episode or metadata problems independent of screen resolution. No retained evidence currently demonstrates such a mismatch.

These are falsifiable hypotheses, not findings. No GPU probe, compositor change, player edit or physics edit was performed by this diagnosis task.

## Same-aspect display probe

`Tools/Performance/run_worker.sh` supports `CRANE_SCREEN_WIDTH` and `CRANE_SCREEN_HEIGHT`; the existing benchmark records actual `Screen.width` and `Screen.height`. A prospective 640x360 to 320x180 probe keeps the 16:9 aspect ratio and `timeScale=1`. The depth image is sized from its fixed serialized `depthRenderTexture` (retained runtime: 1280x720), and `CameraDepthBake` calls `RenderDepthFromCamera` into that texture. It sets camera aspect to the maximum of current aspect and texture aspect, so preserving aspect is necessary.

A source scan of task sensors finds no `Screen.width`/`Screen.height` reads. Nevertheless the ordinary sensor camera/HDRP render pipeline can depend on presentation size. Therefore fixed image dimensions alone do not prove sensor-content equivalence. Treat this as a documented operational development version, retain all evidence, and verify actual depth dimensions, active sensor count, physics/water validity and strict freshness gates. The expected unchanged configuration includes sensor RT, acquisition rates, controller, scene/player hashes, seed meaning, simulation duration and physics time step. Do not switch to `-nographics` or disable rendering/water.

The existing options `--crane-validation-period`, `--crane-validation-capacity`, and `--crane-validation-output` support denser timestamped validation retention without a rebuild. `RecordValidation` writes every sample to JSONL before trimming the in-memory ring. Thus `validationSamplesDropped=85` with 341 JSONL rows denotes ring eviction, not loss of retained trace. Denser validation adds main-thread JSON serialization and flushing; qualify it separately, rather than changing resolution and logging period simultaneously. Per-action stale onset is not included in current validation rows and would require additional instrumentation to resolve precisely.

A time-scale probe is deferred: existing `--crane-time-scale` changes simulated/wall timing and potentially ROS wall-timer relationships, so it is not interchangeable with a display-only headroom probe.

## Parallel rendering qualification

The current hidden-render adapter routes exact `CRANE.x86_64` XWayland class onto one temporary compositor output and changes global compositor rules/limits during its lifetime. Concurrent uses are not isolated merely by ROS domains, ports or output directories.

A worker-specific executable basename/window class is a candidate routing mechanism, not a qualified existing capability. An arbitrary renamed Unity executable may also require correspondingly resolved data/library paths; verify startup and scientific build identity before adopting it. Alternatively test a supported SDL WM-class setting, but do not assume Unity honors it. The wrapper must accept and verify the actual unique class/window PID, and global rule/monitor cleanup must be coordinated. Independent display/compositor sessions can avoid global-rule collision, but still need Vulkan/HDRP/water and freshness qualification on this host.

Keep rendered collection at one worker until that operational qualification passes. Non-GPU response generation, review and analysis can run in parallel immediately with independent artifact directories.
