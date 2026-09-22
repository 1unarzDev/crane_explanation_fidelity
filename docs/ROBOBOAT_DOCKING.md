# RoboBoat docking development

Status: no physical docking attempt is accepted yet. Gates 1-2 pass; long-path and turn gates are
still in progress before known-path docking.

The two physical dock assemblies are centered near Unity X=16.087 m and X=26.087 m, with berth
divider spacing of 2 m. The boat starts near Unity `(x,z)=(4.753,-2.275)`. Nav2's 0.80 m circular
radius is conservative for the roughly 0.895 m by 1.063 m hull envelope, while 1.0 m inflation may
logically pinch the entrance.

The baseline source-derived far target at ROS odom `(0.8641434,-24.586906)`, yaw `-pi/2`, timed out
after 90 s under saturated rotate-only control. That remains a failed historical test, not evidence
against the corrected interface. The LiDAR is at the physical bow; the Blastoise head is aft, and
the target yaw is defined from that catamaran geometry.

The active stack now uses approach scaling and `StoppedGoalChecker`. On a 5 m, 90-degree supplied
path it succeeded at 0.400 m XY / 0.305 rad yaw error while moving 0.041 m/s and 0.022 rad/s, then
settled to 0.029 m/s and 0.0024 rad/s. This validates stopped action semantics on a development
route, but it is not the independent dock-region/contact/clearance/settle predicate required for
Gate 6. No far-dock goal should be counted until known-path long tracking and turns pass.

No environment, marina, dock, water, lighting, or visual asset has been modified.
