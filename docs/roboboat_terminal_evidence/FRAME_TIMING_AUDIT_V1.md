# Development frame-timing probe

The user selected complete supported diagnostic answers as the primary endpoint. Confirmation remains unfrozen. Collection reliability must improve before a broad, adequately powered experiment can proceed.

The v3 display, v4 player-affinity and v5 optional image-signature probes did not remove stale depth observations. Their original attempts remain technical failures. No freshness gate, pending-readback limit or sensor rate has been relaxed.

`CraneFrameTimingAudit` is an opt-in development instrument in the v6 player. With `--crane-frame-timing-audit`, it records sparse frame anomalies, preceding context and one-second samples, including actual fixed-update counts, wall/simulation timing, stale-counter increments and the depth queue size observed at LateUpdate. It installs no host and changes no clock setting when absent. The default-clock probe retains the original image signatures, 640×360 display, 1280×720 depth sensor, unrestricted player affinity, fixed physics step and time scale.

The first v6 runtime probe uses the next untouched row, `boat-geom-42001-00005-v2`, with **no maximum-delta override**. Its immutable intent and retained trace are under the existing population capture root. The first question is whether stale increments coincide with physics catch-up frames. Association cannot distinguish CPU stalls, GPU scheduling, garbage collection or compositor effects. LateUpdate queue occupancy does not reconstruct acquisition-time occupancy. Sparse retention is not a complete sensor-event trace.

The optional `--crane-maximum-delta-time` requires the audit flag, a finite value at least as large as the fixed step, and a separately declared fresh attempt. It changes simulation/wall catch-up and can change relationships with ROS wall timers. Such a run belongs to a revised development platform version; a clean run alone cannot establish a repair or equivalence to the original platform. The default maximum delta is approximately 0.333333 s; a proposed 0.04 s probe would preserve the 0.02 s physics step while limiting catch-up.

The compiled build is bound by `frame_runtime_build_v6.json`: 372 files, 553,791,864 bytes, including managed assemblies and build data. The executable bootstrap hash is identical to the earlier player and is insufficient as a build identity. Supplemental provenance preserves actual source commit/dirty state and the exact source/project-setting bytes used during compilation. The Unity scene-dependency manifest alone omits the runtime-initialize instrumentation. Marine scene, sensor, controller and actuator dependencies match the earlier manifest; whole-build equivalence is not asserted.

Fourteen Unity EditMode tests passed before the build. Eight Python tests exercise trace validation and the collector's actual technical gates, including stale rejection, clock/fixed-step mismatch and assembly tampering despite an unchanged executable hash. The read-only runtime command is:

```bash
PYTHONPATH=analysis python analysis/audit_roboboat_frame_timing_v1.py \
  artifacts/roboboat-population-development-42001/captures/boat-geom-42001-00005-v2/frame-timing.jsonl \
  --require-no-stale
```

This command fails on recorded stale increments or clock changes. A passing trace does not supersede the collector's complete runtime, action, transport and export checks. All failed attempts remain retained; no reissue contributes N. Confirmation and replication N are zero.
