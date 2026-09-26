# Diagnostic throughput report

Updated: 2026-09-26

Status: **baseline established; boat judge qualified; end-to-end canary still required**

| Measure | Current value |
| --- | ---: |
| Land physical attempts | 31 |
| Valid land configurations | 30 |
| Supported physical references | 25 |
| Untouched semantic-eligible references | 24 |
| Independent first-look references ready | 24 |
| Immutable P/R pairs ready | 18 |
| Fully reconciled P/R clusters | 0 |
| Luna study judgments | 0 |
| Boat prospective configurations | 0 |

The boat-specific Luna extension completed 24 isolated calls with no transport failure. Both
passes achieved 1.0 endpoint and required-unit accuracy, zero false acceptance/rejection, and zero
protected causal/boundary failures; core-field accuracy was 0.96875 and 0.97917. This closes the
marine semantic-qualification subgate but does not itself authorize boat study collection or land
production scale-up.

The completed serial semantic segment generated 18 pairs before closeout. Per-call wall times were
not yet aggregated into a governed baseline report, so no throughput-improvement claim is made.
The dominant current bottleneck is the restorable RoboBoat end-to-end canary, followed by Luna
annotation (96 isolated judgments for the first 24 two-answer/two-pass clusters). The operational
profile begins at R concurrency 2 and Luna concurrency 4; production scaling is prohibited until
the readiness gate and development concurrency canaries pass.

Failures retained at this checkpoint: one invalid land transport recording (`cm-land-conf-052`),
one deliberately interrupted response call for 063 with no output/cache record, and no provider
throttle or Luna study failure. R2 matched the governed cache at the prior closeout.
