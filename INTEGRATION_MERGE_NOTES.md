# Branch integration

This integration branch combines the land evidence calibration study, RoboBoat terminal evidence, and both HEXAR external validation and development histories on top of `main`.

`integrate-roboboat-environment` and `roboboat-docking` were already ancestors of `main`, so no additional merge commit was needed for those lines.

The RoboBoat terminal merge had a submodule-pointer conflict for `packages/crane_ml`. The terminal branch points at an unavailable submodule commit; the integration retains the available frozen land pin `40b7fa64c4850cc47fcdddf6a46a2e5831430f64`. No unavailable submodule state was fabricated.

The land confirmation remains administratively incomplete at 494 complete pairs; this integration does not reinterpret it as a confirmatory result.
