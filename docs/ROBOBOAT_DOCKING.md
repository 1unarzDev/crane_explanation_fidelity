# RoboBoat docking development

Status: known-path docking and full long-range `NavigateToPose` docking now pass repeatedly under
the frozen independent predicate. The RoboBoat environment, marina, docks, water, lighting, and
visual assets are unchanged.

The physical dock assemblies have approximately 2 m berth-divider spacing. The hull envelope is
about 0.895 x 1.063 m. Nav2's 0.80 m circular radius is conservative (1.60 m diameter), leaving
about 0.40 m nominal logical diametral clearance before the 1.0 m inflation layer. Retained global
costmaps nevertheless show the corrected far-berth route connected and obstacle-free, with the
known supplied path at least 1.146 m from a lethal cell.

The correct far target is `(0.8641434,-27.586906,+pi/2)`. The obsolete
`(0.8641434,-24.586906,-pi/2)` target was on the dock's closed/back side. The LiDAR and catamaran
noses define the bow; the Blastoise head is aft. At the corrected target, the bow points toward
ROS `+Y` into the open-side approach.

The independent evaluator requires the full 1.063 x 0.895 m hull inside a 3 x 2 m berth, XY/yaw
within 0.40 m/0.35 rad, translation/yaw rate below 0.05 m/s/0.05 rad/s, zero dock/marina contacts,
and every condition continuously for five seconds. These criteria remained frozen while Nav2's
internal XY tolerance was tested.

## Goal-checker experiment

The original known-path run with Nav2 XY tolerance 0.40 m succeeded at 0.374 m while moving
0.0486 m/s, then coasted 0.188 m to 0.559 m. Its hull remained in the berth, but it correctly
failed the independent 0.40 m pose predicate. This isolated a goal-checker/stopping-margin
mismatch rather than a path-tracking or physics defect.

Changing only Nav2's internal XY tolerance to 0.20 m produced three consecutive known-path
successes:

| Artifact | Action XY | RMS CTE | Post-result coast | Settled XY | Dock success |
|---|---:|---:|---:|---:|---|
| `roboboat-gate5-known-dock-xy020-1` | 0.194 m | 0.0319 m | 0.182 m | 0.375 m | yes |
| `roboboat-gate5-known-dock-xy020-2` | 0.195 m | 0.0318 m | 0.182 m | 0.375 m | yes |
| `roboboat-gate5-known-dock-config-xy020-1` | 0.198 m | 0.0316 m | 0.185 m | 0.382 m | yes |

All three were strict-valid, full-hull-contained, stopped, contact-free, and held the predicate for
at least five seconds. Physics, controller gains, speed, lookahead, command adapter, and mixer were
unchanged.

## Full long-range navigation

Five subsequent runs asked Navfn/RPP to solve the corrected far `NavigateToPose` directly; no
supplied path was used. All five Nav2 actions and independent docking predicates succeeded:

| Runs | Physical dock | Strict harness | Settled XY | Settled yaw | Speed | Coast | Contacts |
|---|---|---|---:|---:|---:|---:|---:|
| `roboboat-far-dock-nav2-xy020-{1..5}` | 5/5 | 3/5 | 0.205-0.224 m | 0.264-0.345 rad | 0.016-0.042 m/s | 0.185-0.190 m | 0 |

Runs 1 and 4 are excluded from strict generic validity only because Unity's depth-camera callback
logged one transient `Failed to read back texture once`; both retained clean ROS transport,
populated costmaps, valid water observations, Nav2 success, and independent docking success. Runs
2, 3, and 5 are fully strict-valid. This is a sensor/harness reliability issue, not a docking
failure, and the shared validity rule was not weakened.

The final yaw has two repeatable clusters and can approach the 0.35 rad limit. That is the main
remaining margin concern. It does not currently prevent stable docking, and there is no evidence
supporting a physics or manual-controller change. Retained plots are under
[`research/roboboat-navigation-plots`](research/roboboat-navigation-plots).
