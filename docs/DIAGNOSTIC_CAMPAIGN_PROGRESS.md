# Diagnostic sequential-campaign progress

Updated: 2026-09-24

Protocol: `diagnostic-sequential-protocol-v2`
Current status: **NO ACTIVE CONFIRMATORY CAMPAIGN**

## Readiness

| Gate | Status | Evidence / next action |
|---|---|---|
| Candidate P frozen | NOT_READY | Select only after a separate development cycle |
| Strongest baseline R frozen | DESIGNATED, NOT_HASH_FROZEN | Tool-enabled repository-aware R; freeze exact model/prompts/resources with candidate |
| Information/tool/resource parity | DRAFT | Audit at campaign freeze |
| Target land strata | PARTIAL | Existing cases are development only; fresh generators/configurations required |
| Target surface strata | NOT_READY | Both geometric and command--motion admission required; do not reallocate weight |
| Luna development qualification | SELECTED | Audited v2-medium offline rescore passes every gate; zero new calls |
| Luna held-out qualification | FAILED | Both frozen passes failed category gates; no study scoring allowed |
| Replication configurations reserved | NOT_RUN | Reserve before discovery collection |
| Sequential null simulation | PASS_QA | 20,000 replicates per endpoint; all boundary estimates below component alpha 0.02 |
| Alternative budget sensitivity | COMPLETE | +0.30 scenarios reach 0.9946/0.9366 joint success by 1,600; this is not observed power |

## Program error-budget ledger

| Allocation | Alpha | Status | Campaign |
|---|---:|---|---|
| `candidate-v1-confirmation` | 0.020 | AVAILABLE | none |
| `candidate-revision-reserve` | 0.010 | AVAILABLE | none |
| `selected-method-replication` | 0.020 | AVAILABLE | none |

Consumed alpha: **0.000 / 0.050**. An allocation becomes consumed when its first confirmatory
response is inspected, not when a favorable result appears. Machine-readable state is retained in
`manifests/study/diagnostic-sequential-error-ledger-v2.json`; before the first response is opened,
the chosen allocation must be atomically bound to that campaign and cannot later be refunded.

## Cumulative evidence

| Quantity | Current value |
|---|---:|
| New independent confirmatory clusters | 0 |
| Diagnosable confirmatory clusters | 0 |
| Ambiguous confirmatory clusters | 0 |
| Discovery configurations reused in replication | 0 |
| Luna confirmatory judgments | 0 |
| Unresolved confirmatory labels | 0 |

No effect estimate, confidence sequence, guardrail result, or replication conclusion exists.
Legacy and the nine diagnostic-development clusters are intentionally absent from these counts.

The v1 framework was retired unused after pre-outcome feasibility checks. No v1 or v2 allocation
was consumed. The v2 fixed-fraction e-process and intersection--union decision rule are documented
in `docs/SEQUENTIAL_STUDY_PROTOCOL.md`; retained simulation is planning evidence only.

## Required update for each collection batch

Record, without deleting earlier rows:

- campaign/candidate/freeze hashes and alpha allocation;
- independent cluster counts by frozen target stratum;
- valid recordings, invalid recordings, exclusions, and predeclared reasons;
- P/R paired estimates and corrected anytime lower/upper bounds;
- primary, material-error, coverage, and ambiguity gate status;
- Luna model/settings, held-out qualification, pass agreement, unresolved fields, and sensitivity;
- deterministic measurement/reference checks;
- model/tool calls, tokens, latency, compute, and cost where available;
- stopping/futility state and the next collection or separate development action.

## Next action

Do not collect confirmatory responses. The frozen two-pass Luna held-out qualification failed and
cannot be retried. Decide prospectively whether a bounded new judge-development cycle has higher
paper value than an independently checkable or limited-category endpoint. Any successor must use a
new version and fresh held-out cases. Candidate/baseline/resource freezing, target-stratum readiness,
and replication reservation remain independently incomplete.

## Held-out judge result (2026-09-24)

The selected v2-medium configuration was run exactly once over 14 untouched cases in each of two
isolated passes. Pass 1: 15/17 required-unit statuses, 97/107 core fields, zero false acceptances,
three false rejections, zero unresolved, correct 2/2 answerability boundaries and 1/1 injection
case, but failed material-error presentation invariance. Pass 2: 17/17 units, 98/107 core fields,
zero false acceptances, two false rejections, zero unresolved, and passed boundary, injection, and
presentation-invariance gates. Both failed the small-category zero-false-rejection rule, especially
for diagnostic omission. There were 28 valid calls, no retries, no call failures, and no exposed
tools. This consumes no confirmatory alpha and creates no study labels or effect estimate.
