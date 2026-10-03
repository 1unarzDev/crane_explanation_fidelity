# Persistent Nav2 visualization goal

Status: complete (2026-10-02). Verification passed; scoped changes published with this checklist. Also recorded through `create_goal`.

Recover working headless boat navigation, reproduce its interactive player,
show received Nav2 evidence without altering physics/sensors, verify actual first-slip
docking independently, soften the shore edge, and commit/push the scoped changes.

## Verification checkpoints

- [x] Read the handoff and recover historical complete runs and exact launch commands.
- [x] Identify the corrected body frame and required odometry plus velocity adapters.
- [x] Build a real Unity player with batched nonphysical costmap, nine water probes,
  left/closer camera and clean screen-space legend; inspect rendered PNGs.
- [x] Run the extra six-minute recording demo requested by the user.
- [x] Locate actual Dock0/Dock1 scene geometry and correct the old outside-slip target.
- [x] Capture the boat near the first dock (<=1.6 m to bounds, nearer than second).
- [x] Recompute five-second qualification and actual projected hull containment:
  `first-dock-tight` interactive and `first-dock-headless` reach the first slip.
- [x] User-authorized shore subagent implemented and pixel-verified underwater fade,
  preserving the original terrain collision asset exactly.
- [x] Pair the first-dock image with an evidence-bound language explanation of
  Nav2's recorded collision prediction/recovery and uncertain physical contact.
- [x] Obtain a fully valid new first-slip run under unchanged command timing rules.
  `first-dock-paced` passes at half speed: 865 accepted, zero stale/rejected.
- [x] Verify the adjusted three-image schedule in `first-dock-final`: all checks pass.
- [x] Commit and push Unity changes: `44dd887` on `origin/diagnostic-composition-v1` (includes `4339aa9`).
- [x] Commit/push root navigation docs, auditor, bounded evidence capsule and gitlink.
  The enclosing root commit records the final checklist and pinned Unity commit.

## Evidence and boundaries

Current instructions are in [NAV2_WORKING_BOAT_NAVIGATION.md](NAV2_WORKING_BOAT_NAVIGATION.md).
Raw logs/configurations remain under `artifacts/nav2-docking-reproduction-20261002`.
The bounded review capsule retains source/build hashes, PNGs, message timestamps,
selected settings, physical verification and the collision-risk log excerpt.

Old far-target passing runs qualified a declared 3 by 2 m region outside the
visible second slip; they are not actual docking proof. Corrected first-dock
runs reached the real slip with recorded zero prohibited contacts, but the user
observed contact and Nav2 logged a collision prediction; actual impact is unconfirmed.
Five-second qualification does not establish indefinite station keeping.

RGB/depth-image readback is explicitly disabled; LiDAR `/points` is active.
Full-sensor reliability remains unproven. Real-time first-dock runs rejected stale
commands (`tight`:54, `headless`:38), so strict benchmark validity failed despite
successful navigation and settling. These failures are retained, not waived.

The headless run's final summary was regenerated from complete worker/log artifacts
because editing the live Bash launcher interrupted its final summary step. No
navigation samples were replaced. Future launch edits must wait until the shell exits.

Existing unrelated scene/paper/settings edits are preserved and excluded from commits.
The build used pre-existing scene transforms/material; the provenance records this
boundary, so a clean checkout is not claimed to reproduce every pixel exactly.
