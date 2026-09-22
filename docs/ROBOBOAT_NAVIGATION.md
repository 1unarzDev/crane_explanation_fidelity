# RoboBoat navigation development

Status: baseline controller is Regulated Pure Pursuit under
`packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml` (SHA-256
`20562df69b9c07e0b82c3d1479435b79e66f9c105472aa29abcabaf346fe80c2`).

An unchanged 0.5 m `NavigateToPose` run returned success after 8.98 s and 0.582 m displacement, but
all observed controller commands were rotation-only. Because the direct command characterization
proves swapped translation axes and inconsistent pose/twist yaw sign, this result is not accepted as
path-following success. No controller selection or tuning is justified until Gate 1 passes.

Full configuration, architecture, runtime identities, and evidence are maintained in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md).
