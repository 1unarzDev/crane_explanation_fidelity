# B0/B1 ordinary interfaces — 2026-09-30

The baseline helpers prepare distinct deterministic presentations of the same runtime evidence:
B0 gets ordinary retained-field/role statements, and B1 gets the structured JSON record. A single
common prompt asks both for the strongest supported explanation, decisive evidence, outcome,
useful partial diagnosis, limits and false-premise handling. Neither receives source assets,
executable tools, diagnostic contracts or a planner's supported-claim list. B2's source/tool access
and existing prompt remain unchanged.

The B0 summary describes each top-level field and evidence role and includes its full original
literal content. Nested telemetry remains literal JSON inside the role statement. This format
does not infer causes, select representative samples or discard quantities/provenance. Its
decoder must reconstruct the structured record exactly, including numeric/boolean/null types,
sample/evidence-ID ordering, empty objects/arrays and escaped strings. B1 receives that same
record directly. This is a declared input presentation difference; usefulness and method effects
remain to be measured and are not implied by the round-trip check.

The earlier five-method packet snapshot retains B0's raw JSON input serialization. This newer
request candidate explicitly derives the ordinary summary from that source and records both the
source packet hash and effective presentation hash/version. It changes no earlier packet, response
or cache. Future execution must bind the complete effective request, rather than assuming the
older raw-JSON B0 serialization is the input used here. Both baseline requests bind the same
evidence hash, exact question and common prompt template.

Return helpers check request/transport/schema identity and raw/parsed consistency only, retaining
ordinary answers verbatim. Empty answers, unsupported claims, wrong quantities and missing
limitations cannot trigger semantic repair or quality-driven retry. Their evaluation remains
subject to the separate support/attachment/endpoint gates. The helpers contain no provider,
stager, retry loop or execution launcher.

Twelve synthetic interface checks verify lossless nested records, distinct presentations with
common instructions, six verbatim-answer cases, rejection of injected contracts/lost facts/private
truth/nonfinite values, duplicate/suffix corruption and retained technical-failure handling.
The read-only audit additionally reconstructs all sixty candidate conditions on the original
fixed sixteen inspected development episodes, verifies their retained method-packet hashes and
records 120 B0/B1 request hashes and UTF-8 byte sizes. No request text or method output is persisted.
Byte sizes do not establish model token capacity. Before execution, bind the model/tokenizer and
capacity policy without silently truncating evidence or dropping a condition.

The inspected candidate's B0 prompts range from 1,538 to 554,254 bytes; B1 ranges from 1,560 to
809,592 bytes. These measured sizes make context-capacity verification a concrete execution
prerequisite. They are not token counts or evidence of successful model processing.

Run `python -m pytest -q tests/test_evidence_calibration_baselines.py` and
`python analysis/audit_evidence_calibration_baseline_requests.py` to reproduce the checks.
This candidate authorizes no model/annotation call or P11 freeze. The failed support canary,
unlaunched C, prior outputs, alpha, quarantine and confirmation/replication N remain unchanged.
Fresh five-method execution and qualified measurement still precede episode effects, intervals,
corrected paired p-values, coverage/power and P11 decisions. All comparisons, including
inconclusive and unfavorable results, remain required.
