# RoboBoat docking development

Status: no physical docking attempt is accepted yet.

The two physical dock assemblies are centered near Unity X=16.087 m and X=26.087 m, with berth
divider spacing of 2 m. The boat starts near Unity `(x,z)=(4.753,-2.275)`. Nav2's 0.80 m circular
radius is conservative for the roughly 0.895 m by 1.063 m hull envelope, while 1.0 m inflation may
logically pinch the entrance.

A far-dock `NavigateToPose` test was requested and remains part of the baseline suite, but running it
before fixing the proven command/feedback frame defect would not diagnose Nav2. The test must retain
the exact dock pose, planned and actual trajectories, final pose/speed, clearance/contact, settle
interval, Nav2 status, and an independent docking predicate.

No environment, marina, dock, water, lighting, or visual asset has been modified.
