# RoboBoat docking development

Status: one corrected long-range run satisfied the independent physical docking predicate, but it
is not yet a repeatability result. Gates 1-3 pass; turn/S-turn and known-path docking gates remain
before configuration freeze.

The two physical dock assemblies are centered near Unity X=16.087 m and X=26.087 m, with berth
divider spacing of 2 m. The boat starts near Unity `(x,z)=(4.753,-2.275)`. Nav2's 0.80 m circular
radius is conservative for the roughly 0.895 m by 1.063 m hull envelope, while 1.0 m inflation may
logically pinch the entrance.

The original far target `(0.8641434,-24.586906,-pi/2)` was on the closed/back side of the
180-degree-rotated dock and is obsolete. The corrected open-side target is
`(0.8641434,-27.586906,+pi/2)`. The LiDAR and catamaran noses define the physical bow; the
Blastoise head is aft. A retained costmap shows the corrected target cell is free and connected,
with sufficient physical and logical lethal-obstacle clearance.

The active stack now uses approach scaling and `StoppedGoalChecker`. On a 5 m, 90-degree supplied
path it succeeded at 0.400 m XY / 0.305 rad yaw error while moving 0.041 m/s and 0.022 rad/s, then
settled to 0.029 m/s and 0.0024 rad/s.

An opt-in evaluator now requires the full 1.063 x 0.895 m hull inside a 3 x 2 m berth, XY/yaw
within 0.40 m/0.35 rad, translation/yaw rate below 0.05 m/s/0.05 rad/s, zero dock/marina contacts,
and all conditions continuously for five seconds. With only the global planning window changed
from 40 x 40 m to 60 x 60 m, the corrected 23.11 m `NavigateToPose` run succeeded and held this
predicate for eight seconds: 0.221 m XY error, 0.338 rad yaw error, 0.0153 m/s speed, 0.0079 rad/s
yaw rate, 0.361 m final minimum region clearance, and zero observed contacts. The generic worker
summary is still conservatively invalid because of one post-result adapter timeout/stale event;
therefore this run is evidence that docking is physically possible, not a completed reliability
gate.

No environment, marina, dock, water, lighting, or visual asset has been modified.
