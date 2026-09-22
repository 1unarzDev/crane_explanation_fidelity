# RoboBoat navigation development

Status: reconnaissance complete; interface correction and Gates 1-2 validated. The active
controller remains Regulated Pure Pursuit under
`packages/crane_ml/Tools/Performance/nav2_controller_fixture.yaml` (working-tree SHA-256
`497309b14d4c0c32e50cd49542adfcc76950b8b9abb723310e64999def9ed6a2`).

The measured torque-mode saturation was corrected by selecting proportional shaft-velocity mode;
the mixer, manual controller and bindings, force law, and hydrodynamics are unchanged. A ROS-only
PI body-velocity adapter now interprets Nav2 commands as desired surge, sway, and yaw rate. RPP
uses no rotate-first behavior, slows over the final 2 m to a 0.02 m/s minimum, and uses
`StoppedGoalChecker` with 0.05 m/s and 0.05 rad/s thresholds.

Three current-build 10 m FollowPath runs all succeeded. RMS cross-track was 0.0025-0.0026 m,
maximum cross-track 0.0083-0.0093 m, action-result speed 0.044-0.049 m/s, settled speed
0.0196-0.0214 m/s, and settled final XY error 0.236-0.253 m. Artifacts are
`PerformanceResults/roboboat-active-10m-{1,2,3}`.

Negative matched tests are retained: MPPI Omni with its default path-angle behavior spun instead
of translating; removing that critic did not recover the route. RPP rotate-first remained trapped
even after measured yaw-rate and acceleration limits. RPP without rotate-first plus approach
scaling remains the evidence-supported active controller. Gate 3 (repeated 30-50 m) is next.

Full configuration, architecture, runtime identities, and evidence are maintained in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md).
