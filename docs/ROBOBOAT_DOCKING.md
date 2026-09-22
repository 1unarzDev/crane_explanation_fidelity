# RoboBoat docking development

Status: no physical docking attempt is accepted yet.

The two physical dock assemblies are centered near Unity X=16.087 m and X=26.087 m, with berth
divider spacing of 2 m. The boat starts near Unity `(x,z)=(4.753,-2.275)`. Nav2's 0.80 m circular
radius is conservative for the roughly 0.895 m by 1.063 m hull envelope, while 1.0 m inflation may
logically pinch the entrance.

A source-derived far target at ROS odom `(0.8641434,-24.586906)`, yaw `-pi/2`, was attempted with
the current untuned stack. `NavigateToPose` timed out after 90 s. Nav2 issued rotate-only commands,
the hull drifted 6.166 m, and terminal yaw rate was 0.784 rad/s. The LiDAR is at the physical bow;
the Blastoise head is aft, and the target yaw was checked against that catamaran geometry. This is a
failed navigation test, not physical docking. Collision/clearance, dock membership, and a
stopped-settle predicate remain required.

No environment, marina, dock, water, lighting, or visual asset has been modified.
