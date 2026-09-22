# RoboBoat navigation development

Status: reconnaissance complete; baseline controller is Regulated Pure Pursuit under
`packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml` (SHA-256
`20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`).

ROS-only frame fixes align surge, sway, and yaw without changing the manual controller, thruster,
mixer, or physics. A supplied 10 m path tracks at 0.048 m RMS cross-track, but reports success at
1.183 m/s and then coasts 0.202 m. A source-derived ~20 m far-dock `NavigateToPose` times out under
rotate-only control and reproduces aggressive circling/drift. No controller parameter was tuned.

Full configuration, architecture, runtime identities, and evidence are maintained in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md).
