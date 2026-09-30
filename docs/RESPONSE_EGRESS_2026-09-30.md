# Complete local response egress candidate — 2026-09-30

## Gap and implementation

MCP v5 retains generated RPC responses before transport, but its sink write return
value is unchecked and it has no cumulative response-byte ledger. Preserve v5 and
coordinator v2. Separate `analysis/evidence_calibration_response_egress_v2.py` wraps
the sink; coordinator v4 integrates it into the existing plan/ownership path. The
initial writer v1 and coordinator v3 remain preserved with their newly found defect. No
study caller or installed-client observer migrates.

Every configuration must declare a typed response total of 1 KiB–2 GiB. This is an
implementation range, not a scientific budget. The exact value participates in the
permitted configuration digest. Owner intent binds the configuration and selected
sources; a separate operator egress intent binds the limit and accounting scope.
The source binding includes the egress module. Limits remain prospective and must
permit full registered evidence and fair method access before scientific use.

Accounting covers the **encoded local MCP response bytes including newline framing**:
initialization, tool lists, errors and tool results. It excludes input, stderr,
provider traffic, model tokens/reasoning, internal audit storage and host work.

Before writing, reserve the whole response and retain its length/hash. Short positive
write counts advance over only the unsent suffix, preserving exact byte order without
repeating a response or computation. Invalid/unknown counts or write exceptions close
egress admission. Flush and settlement retention must both succeed before bytes become
settled. Flush/storage uncertainty retains pending state and null remaining budget;
no output, flush, ledger or condition owner may be replayed/adopted.

A response larger than the remaining total is **withheld completely**, never truncated
or replaced with an invented tool summary. Its generated RPC record remains retained
operator-side. The exception stops the server/condition, and queued calls do not run.
The response may already have required computation: its actual CPU remains charged.
This is a local output budget, not a bound on generated/audit bytes or pre-computation
admission. A denial after valid computation is infrastructure failure, not a semantic
method result. No endpoint failure mapping is frozen here.

## Verification

The initial egress/coordinator v3 suites pass 46 distinct checks; two targeted reruns
strengthen queued-call assertions. These checks missed an unwritten-flush defect.
The repaired writer v2/coordinator v4 suites pass **48 distinct checks**, including
explicit preserved-defect and repair regressions. Checks include short writes,
remaining-budget boundary, invalid return counts, partial/flush failures, intent and
settlement storage failures, typed limits, plan membership, actual stdio computation,
CPU charging despite withheld output, construction/retention failure and restart denial.

Ignored retained root: `output/infrastructure/response-egress-development-v1/`.
Client intent and shared seven-entry execution plan precede all calls. Seven fixed
flows pass and are hash-bound in
`manifests/operations/evidence-calibration-response-egress-v1-development.json`:

- B0/B1 produce **429** locally written/flushed bytes each, with zero exposed tools.
- B2/B3/B4 produce **18,099** bytes each under seven-byte sink writes, with identical
  tool definitions, exact literal output and full 4096-character Unicode reads.
  Each synthetic output total is 65,536 bytes. No truncation occurs.
- A separate B2 flow has 1,024-byte total. Initialization is sent; the large complete
  computation response is withheld. Its original 500-character Unicode result remains
  in the RPC record and **33.701 ms** of computation CPU stays charged. The queued
  second computation has no RPC intent or service.
- A separate operator-injected sink accepts two bytes then raises. Observed write bytes
  remain **2**, settled bytes **0**, pending response **1**, and remaining budget **null**.
  This is an injected infrastructure failure, not a model or scientific method failure.

All seven scopes reject restart. All four original retained computation services are absent. A separately pre-bound
repaired seven-flow set also passes under
`output/infrastructure/response-egress-development-v2/`, with the same exact byte
totals and **33.616 ms** charged CPU in its budget flow. Its four services are absent
too. These assignments and reruns do not increase experimental N.

## Preserved defect and repair

An intent-storage failure sets a pending response before any sink write. Writer v1
incorrectly permits a later flush to settle that unwritten response. A retained
operator-injected regression confirms **3 settled bytes with 0 sink bytes**. This is
a false transport receipt and invalidates that path; it is not a model failure.
Original source and successful fixed-flow records remain unchanged.

Writer v2 adds one completed-write state flag. It permits flush/settlement only
after the entire reserved response was written. The matched retained regression
rejects unwritten flush, keeps settled bytes **0**, leaves response **1** pending
and remaining budget **null**, and creates no settlement record. Coordinator v4
changes only writer/source selection and owner schema. No repaired receipt is
substituted into an original record.

## Limits and governance

Successful local write/flush and retained settlement do not prove peer receipt,
installed-client forwarding, provider payload preservation or model-visible rendering.
Transport interruption may leave an incomplete response in the sink; it is retained
as unknown and never repaired/replayed. Power-loss/distributed durability, immutable
runtime/storage, complete dependency binding and full model-turn accounting remain
open. Installed-client integration for coordinator v4 is unverified.

No semantic output, automated annotation, method-key join, pilot score, physical
acquisition, alpha spending or P11 freeze occurs. Preserve failed combined support,
unlaunched C and unanswered reopening. P11 retains nineteen open conditions and
confirmation/replication independent N=0. Scientific budgets, population, endpoint,
coverage floor and sample size remain unfrozen; five-method reporting remains required.
