# RoboBoat dynamics validation

Status: Gate 1 failed on 2026-09-21. Unity physics and hydrodynamic parameters remain unchanged.

The production `TwistStamped` boundary was exercised with ±0.2 surge, sway, and yaw requests plus
zero-command coast intervals. The reproducible launcher and analyzer are
`packages/crane_ml/Tools/Performance/run_roboboat_command_response.sh` and
`roboboat_command_response_fixture.py`.

Authoritative results are summarized in
[`research/ROBOBOAT_NAVIGATION_BASELINE.md`](research/ROBOBOAT_NAVIGATION_BASELINE.md). The decisive
finding is that requested surge realizes primarily as reported body sway, requested sway realizes
primarily as reported body surge, and pose yaw evolves opposite reported yaw-rate sign. These are
frame/actuation-feedback defects, not evidence for hydrodynamic retuning.

No physics coefficient, mass, inertia, drag, buoyancy, water, thrust, scene, or environment value
has been changed. Gate 1 still requires a corrected repeat, multiple command amplitudes, formal
latency, saturation, and stopping-distance/time measurements.
