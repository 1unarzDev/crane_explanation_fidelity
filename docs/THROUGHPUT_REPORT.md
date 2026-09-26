# Diagnostic throughput report

Updated: 2026-09-26

Status: **boat narrow arm frozen; production launch is the active stage**

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
| Boat development P/R canary pairs | 1 |
| Boat development Luna judgments | 4/4 valid |

The boat-specific Luna extension completed 24 isolated calls with no transport failure. Both
passes achieved 1.0 endpoint and required-unit accuracy, zero false acceptance/rejection, and zero
protected causal/boundary failures; core-field accuracy was 0.96875 and 0.97917. This closes the
marine semantic-qualification subgate but does not itself authorize boat study collection or land
production scale-up.

The current boat canary required 46.2 s for R. Its four Luna jobs took 28.9, 55.8, 35.5, and
53.4 s; the bounded canary runner invoked them serially, yielding one fully reconciled development
P/R cluster in about 3.3 minutes of judge wall time. This is an execution baseline, not a
production-throughput result. At Luna concurrency four, the same observed service times imply a
best-case judge-stage wall time near the 55.8 s tail, subject to measured throttling tests.

The configuration blocker is closed as a prospectively frozen, honestly narrow arm: four exact
physical configurations and one clustered missing-speed control. The arm omits unsupported
disturbance families and remains separate from land N, alpha, and replication. Configuration
application and reset isolation pass with the current immutable graphics/water build and validated
Nav2 profile. Production begins with boat simulation concurrency 1, R concurrency 2, Luna
concurrency 4, CPU concurrency 4, and a single publisher. The intended production metric remains
valid fully reconciled P/R clusters per hour; no improvement is claimed until actual production
clusters complete.

Failures retained at this checkpoint: one invalid land transport recording (`cm-land-conf-052`),
one deliberately interrupted response call for 063 with no output/cache record, and no provider
throttle or Luna study failure. R2 matched the governed cache at the prior closeout.
