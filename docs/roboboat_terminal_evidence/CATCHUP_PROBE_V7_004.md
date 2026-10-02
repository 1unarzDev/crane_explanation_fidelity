# Fresh development catch-up probe 004

Prospectively declared after rendering-v2 default-clock attempts 42004-00004-v1/v2 failed strict technical gates. Those failures remain invalid and will not be reissued. Confirmation/replication N remain zero.

Ranked mechanisms: (1) multiple fixed updates issue acquisition requests before GPU callbacks drain the two-slot queue; (2) GPU/readback latency fills the queue even without catch-up; (3) host/compositor stalls contribute to both. Sparse LateUpdate traces establish association only, not request-time causation.

One-variable intervention: set Unity maximumDeltaTime to 0.04 seconds rather than its observed default 0.333333343 seconds. Preserve the 0.02-second fixed step, sensing rates/readback queue, image signatures, controller/task, compiled player, rendering-v2 wrapper and every inherited strict validity gate. This changes simulation/wall catch-up; equivalence to the prior platform is not claimed.

Use the next untouched rows in population42004 at the existing capture root, starting00005-v1. Maximum initial diagnostic batch: four attempts, stopping after two consecutive technical failures. No quality retries. The operational batch limit is not a study sample ceiling. Collector writes a source-bound pre-call intent before executing any row.

Discriminating observations: applied cap readback, stale-observation counts, stale/rejected-action counts, retained fixed-update counts, queue state and overall technical validity. Persistent queue overflow with at most two fixed updates per frame argues against catch-up alone being sufficient. Zero overflow is promising engineering evidence but cannot establish a causal mechanism or scientific method advantage. Preserve all results and compare descriptively with the already retained default-clock traces; fresh geometry differs, so this is not a randomized causal estimate.

No explanation scores, method labels or endpoint effects govern this intervention. Subsequent valid data are development from the revised timing platform.
