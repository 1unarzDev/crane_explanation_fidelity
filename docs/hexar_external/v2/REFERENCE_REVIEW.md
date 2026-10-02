# Independent six-recording development reference review

Constructed 2026-09-30 before inspecting the v2 production ontology or method answers. The evaluator-only artifact is `data/hexar_external/v2/development/references.json`. It matches the previous independent-reference schema and covers all 54 packet jobs, with packet hashes, required communication units, required scope limitations and optional supported facts. No endpoint labels, model preferences or method guesses were assigned.

## Prospective useful-information requirements

Each job requires the correct recorded navigation outcome: success for D001/D005/D006, failure for D002/D003/D004. Recorded timeout or abort can convey failure when explicitly present. No timestamps, measured duration, full task plan or exact phrase is required. Thirty jobs have relevant diagnostic observations and receive exactly one disjunctive diagnostic unit: communicate at least one of the available bounded alternatives. D002 allows recorded planning/invalid-path/abort trouble; D003 allows recorded manual selection or progress/abort trouble; D004 allows recorded charging selection or progress/abort trouble; D005 allows recorded localization uncertainty or planning/invalid-path/abort trouble; D006 allows recorded planning/invalid-path/abort trouble. All alternatives are source-qualified facts rather than guessed physical causes.

D001 has no retained trouble or selected override diagnostic, so its successful outcome remains useful without requiring negative state checks. Diagnostic-removal conditions likewise retain useful outcomes without requiring removed diagnostics. False manual/charging indicators are optional supported status facts; they do not become mandatory diagnostic explanations. None of the 54 packets establishes a unique physical failure mechanism or a measured reason for subjective bad/slow motion. An explicit unknown-cause sentence is optional when the answer stays clearly bounded to recorded facts. Supported extras remain valid beyond the compact required list.

The rules agree with the prospectively written [endpoint](ENDPOINT.md). Subject mention, opposite polarity and unsupported value do not cover the specifically requested unit. Coverage is independent from unsupported material-claim rejection: a correctly conveyed failure can remain covered when an attached physical cause overclaims. Outcome/state/diagnostic/software-action/causal assertions are material, including negative causal claims; a requested clear is not completed clearing, and a failed planning attempt is not global route infeasibility. Useful information is not an exhaustive-detail contest. Stylistic differences and optional omissions do not create failures.

## Independent state and numerical checks

All 54 canonical packet hashes recompute using sorted compact JSON. Present state values and receipt timestamps match the latest retained raw joystick/charging messages after each declared mask; unavailable states have no retained state message and are never converted to false. Every intact packet equals its irrelevant-removal counterpart for each recording/question. All logs fall inside the upstream float-converted selected task windows.

The independent localization counter replay used the upstream threshold: mean of covariance entries 0 and 7 above 0.2 OR orientation covariance entry 35 above 0.2, counter increment for high, decrement without a floor for low, derived message only on a high sample with counter greater than five. All covariance arrays have 36 finite values. D005 has 30 high and 51 low samples in intact input, ending at counter −21 but generating 25 in-window high-uncertainty diagnostics; all 25 match the permitted packet. Other intact recordings generate zero in-window high-uncertainty diagnostics despite isolated high samples. Diagnostic removal produces no such diagnostics. These checks were repeated for all packet jobs and stored with references.

Raw covariance values/counts and other audit-only observations are **not** additional permitted evidence for response support. The top-level numerical replay checks remain evaluator-only provenance; annotate only against the complete permitted packet plus its packet-specific reference. The method-visible diagnostics do not license quoting raw numeric covariance measurements absent from that packet.

## Timing limits discovered independently

D002/D004/D005/D006 intact windows each contain two inversions when callback-time strings are converted to floats. The logs preserve recorded event order, but upstream unpadded `sec.nanosec` representation can invert numeric subsecond order. D001/D003 have no such inversion in their selected logs. No observation order was edited, and no exact timing assertion is required by these references. Reusing the legacy timestamp conversion cannot justify measured timing/causal-delay claims.

Every intact latest charging sample arrives after the selected task-window end, while latest manual samples precede it. This matches the upstream final-state injection semantics, not a time-filtered state observation. The reference therefore requires only latest-received status when a selected charging/manual diagnostic is used; it does not establish that the same state held throughout the navigation window or physically inhibited motion. The retained packet contains receipt times and that scope warning for all methods.

D002 logs report no valid path and aborted handles but its outcome is aborted/failed, not timed out. D003/D004 explicitly report timeout. D005/D006 retain software planning trouble even though their recorded navigation succeeds; neither success nor software trouble measures the requested bad/slow movement or its cause. D001 success does not prove safety-limited speed or normal physical behavior.

## Limits and next measurement step

This is independent developer-agent reference construction, not human validation or qualified annotation. Six physical recordings across known released navigation situations support development only. Repeated queries and masks do not create independent executions. The passed external qualification covers the declared synthetic support/coverage distinctions; it does not independently validate these references, atomization completeness, endpoint materiality or robot-generalization claims. Main source semantics were imported read-only; no ontology or shared pipeline was changed.

Packet-specific references should be frozen before inspecting matched method answers. Blinded atomic inventory and the two independently qualified support passes remain necessary; retain disagreements and technical failures. Full task fields are available here as permitted evidence, so valid supplemental task/room/sequence facts are not rejected just because a compact reference omitted them. A task instruction or success status still is not independent proof of a physical delivery mechanism.

## Reproduction and prospective reserved construction

The generic independent builder is `analysis/hexar_external/build_references_v2.py`. It imports only the Python standard library and embeds the unchanged independently authored reference rules; it does not import a production ontology or read responses. Run from the repository root:

```bash
python analysis/hexar_external/build_references_v2.py --cohort development --check
python analysis/hexar_external/build_references_v2.py --cohort reserved
python analysis/hexar_external/build_references_v2.py --cohort reserved --check
```

The development rebuild is byte-identical: SHA-256 `e45d721cd6c46f9a9bc8d2f382d04700d4cdce775522ea456e018f62f4820ba2`. Existing reference bytes are immutable: a mismatch fails closed rather than overwriting. The reserved command is supplied for the coordinator after prospective freeze; it was not run in this review. The embedded date identifies the reference-rule construction record, not an assertion about the eventual reserved run date. Reference output must be completed before reserved answer inspection.
