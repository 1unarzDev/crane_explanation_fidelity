# Capture freshness follow-up: requested display reduction

The development v3 attempt `boat-geom-42001-00002-v2` is technically invalid: two stale depth observations, zero stale/rejected actions, and worker `valid=false`. The read-only v1 audit reproduces the failure with exit 1. Preserve the attempt and do not export it as valid evidence.

## Actual intervention and timing

The capture intent requests 320x180. Actual retained `result.json` reports **320x360**, and `player.log` explicitly records `requesting resize 320 x 360` and the runtime profile's 320x360 dimensions. The intended same-aspect intervention was not realized. The reason for the height adjustment has not been established from retained source. Neither wrapper nor worker launcher explicitly clamps height to 360. Do not describe this recording as a qualified 320x180 probe or assume sensor-content invariance. Depth output dimensions remain 1280x720, but image dimensions alone do not establish equivalence of the HDRP path.

The stale count first rises from zero at 250.00258 to two at 251.00263 simulated seconds. The 314-second observation is a later cumulative reading. Queue age is four ticks at the first positive sample, and the entire run's maximum sampled age is five ticks. This demonstrates why both cumulative failure counts and sampled ages are needed: one-second sampling can miss the queue-age peak of a short burst.

| Quantity | Original wide-turn v1 | Requested-display-reduction v2 |
|---|---:|---:|
| Actual display | 640x360 | 320x360 |
| Depth output | 1280x720 | 1280x720 |
| Stale observations | 3 | 2 |
| Stale/rejected actions | 0/0 | 0/0 |
| First positive sample, sim seconds | 173.02990 | 251.00263 |
| Maximum sampled depth age, ticks | 17 | 5 |
| Mean GPU frame, ms | 13.078 | 13.557 |
| Maximum depth-readback marker, ms | 119.272 | 23.802 |
| Maximum depth-publish marker, ms | 117.496 | 16.347 |
| Maximum ROS-create-message marker, ms | 77.492 | 16.943 |
| Maximum LiDAR marker, ms | 77.043 | 15.198 |

These are different tolerance variants of one geometry, not a controlled paired performance benchmark or additional independent configurations. Summary marker maxima lack timestamps, so their relationship to stale onset remains unknown. The persistence of staleness while large CPU marker tails disappear weakens a simple explanation requiring those large CPU tails; it does not identify GPU scheduling as the cause.

## Transport and main-thread work

Available source allocates a distinct 3,686,400-byte depth payload for every published 1280x720 float32 frame. At 15 Hz this alone is about 55.3 MB/s of raw image data/allocation, before other sensors and transport overhead. Payloads cannot be reused while asynchronous senders still reference them. `TopicMessageSender` retains message objects, dequeues them under a lock, then serializes/writes them on the send path. `MessageSerializer.SendTo` writes its byte-array segments; the ordinary sender does not call `GetBytes` to construct an additional monolithic serialized payload.

Main-thread `CreateMessage` also invokes `CraneRuntimeMetrics.ReportImage`, which traverses every byte for a full FNV checksum when image signatures are enabled. Thus a long `CRANE.ROS.CreateMessage` marker need not mean transport serialization is slow. Disabling signatures would change retained instrumentation and should be a separately declared diagnostic intervention if pursued; it is not recommended as the next production change.

Four-second external CPU samples give endpoint mean/max 10.70/15.48% and controller 14.28/20.49% for v2, similar to original wide turn. These coarse Docker values do not show sustained saturation, cannot exclude short stalls, and should not be interpreted as per-core headroom guarantees.

## Next operational probe

A source-preserving CPU-affinity probe can test whether scheduling/resource competition contributes. First restore and verify actual 640x360 presentation so that the next intervention changes one operational factor. Use generous **disjoint physical-core pools** for the Unity player and ROS containers, with no CPU quota or realtime scheduling. On this host `lscpu -e` shows sibling pairs 0/1 through 14/15; CPUs16–19 are separate cores. An example allocation is Unity0–7, controller8–11, endpoint12–13, with remaining CPUs for fixture/collection/other explicitly managed tasks. This is an example requiring current host-load inspection, not a claim of an optimal allocation.

A player-only `taskset` launch does not constrain Docker children: they are created by the Docker daemon. Apply container `--cpuset-cpus` prospectively at startup using additive orchestration, and retain both requested settings and effective process/container affinity. Affinity is not exclusive reservation unless other substantial managed workloads are kept off those cores. Do not call the probe isolated without checking that condition.

Prediction: if scheduling competition causes lag, generous dedicated pools should reduce sensor/command timing tails and stale incidence with unchanged sensor dimensions, cadence, physics, time scale, controller, scene/player and strict admission. A clean single run supports operability only; repeated fresh development probes are needed to estimate reliability. Persistence of failures would motivate higher-resolution boundary timing or GPU/readback instrumentation rather than larger queues, weaker gates or repeated salvage attempts.

The collector can already retain timestamped validation using `--crane-validation-period` and `--crane-validation-output`, but denser synchronous JSONL flushing is itself additional main-thread work. Change and qualify that separately. Capturing thread scheduling/timing externally can help distinguish stalls without changing sensor content; bind measured PIDs and event times, and avoid retaining provider command lines or credentials.

No source, player, scene, GPU worker or compositor mutation was performed in this follow-up. The next probe remains exploratory and requires no scientific confirmatory claim.

## Coordinator disposition and next probe activation

After identifying the actual-display mismatch, the coordinator terminated its owned wrapper for the next v3 row `boat-geom-42001-00003-v1`. That row retains termination code143 and missing terminal summary; it is a technical failure, not salvageable physical evidence or an automatically repeatable identity. V3 stopped after two new failures: the completed stale-depth row above and the deliberately terminated row. The completed row also fails the launcher status gate because the invalid Unity worker exits nonzero. That status failure is consistent with retained runtime invalidity, not a reason to ignore the stale observations.

The coordinator has activated a narrower **v4 exploratory player-affinity probe**, restoring original 640x360 presentation and assigning only Unity to CPUs0–15. Those CPUs comprise the verified performance-core sibling pairs; CPUs16–19 have lower reported maximum frequency (3.8GHz versus4.9GHz). ROS scheduling is unchanged, retaining one operational intervention. Its additive wrapper hash-verifies the original binary, applies `sched_setaffinity`, and `execv`s the original player with the original forwarded arguments. Attempt intents bind the retained wrapper source.

This probe is running at the time of this note; no repair or reliability outcome is established. It tests the narrower hypothesis that restricting Unity away from lower-frequency cores reduces timing failures. It does not establish exclusive CPU isolation or eliminate competition with ROS. If failures persist, the prospectively recorded disjoint ROS/player cpuset design above remains a candidate successor, after evaluating this probe. No live collector was changed by the diagnosis agent.
