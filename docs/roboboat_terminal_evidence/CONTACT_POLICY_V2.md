# Explicit contact policy v2 — development successor

The settling strict-score difference exposed an ambiguous public requirement. The v1 flag `contact_required:true` did not say whether contact was required, prohibited or merely required to be assessed. Legacy production also accepted in-window contact hits before checking clock alignment. Preserve those sources, contracts, source answers, judgments and scores; neither defect demonstrates method superiority.

The separate `task_contract_v2.json` declares absence of any hull contact with external objects over the same fixed dwell. Geometry, frame, clock, thresholds, dwell, capture length and uncertainty remain identical to v1. This is an explicit public restriction, not hidden evaluator truth. Every method and judge must receive the identical v2 contract before a new comparison. Successor packet/task/certificate identities distinguish inspected replays from frozen experiments. The upgrade helper rejects any non-contact requirement change and refuses automatic conversion of legacy contact evidence.

`roboboat_temporal_certificate_v2.py` reuses frozen production kinematics and computes contact support separately. An aligned valid positive prohibited-contact observation within the inclusive declared interval establishes false without complete capture. A different clock cannot establish either violation or absence without a clock mapping. No mapping is implemented. Missing contact, an unanchored dwell, incomplete capture, or coverage that fails to bracket the dwell gives unknown. Only an aligned complete prohibited-contact event stream, with declared sensor identity and completeness basis covering the entire dwell, establishes absence. Empty messages alone never establish absence. Counts must be nonnegative integers; observation/coverage times must be finite and ordered; nested fields are allowlisted. Completeness remains an external sensing/capture guarantee to be justified by any future sensor integration, not something this arithmetic can independently certify.

A contact after the fixed dwell does not falsify that dwell. Contact evidence is excluded from all L0–L2 packets, rather than leaked as a retained summary; genuine future contact observations need a separately declared L3. No genuine contact telemetry exists in the seven retained fresh recordings. Construction-defined contact cases in tests and qualification are not observations of boats.

The independent successor reference imports only the independent v1 reference. It computes aligned contact support separately. Its evaluator-only synthetic completeness input isolates kinematic arithmetic and is never exported to method packets or presented as observed contact evidence. Production/reference independence does not eliminate a shared specification error; targeted cases check the declared semantics, endpoints, incompleteness, clock mismatch and post-dwell scope.

The v2 renderer retains the unpromoted v4 positive sampled kinematic/hull witness and makes the contact restriction explicit even at L0. Construction-defined fully observed success receives a positive sampled answer with interval and coverage; continuous-time compliance remains unestablished. Retained recordings continue to have unknown contact and unknown full completion. No physical cause is identified by post-result motion.

Executed replay: `artifacts/roboboat-contact-policy-v2/replay/`. Six successor packets from two inspected settling recordings pass independent references and two removal-only ladder audits. Original source hashes and all dependency hashes are bound in `development-audit.json`. These are reissued development observations, adding zero recording/cluster N, not a new method comparison, annotation result or confirmation.

The separately frozen six-case semantic suite uses the current qualified judge, prompt/schema, two isolated passes and original 300-second deadline. It checks explicit restrictions, mismatched clocks, violation sufficiency, complete absence, post-dwell timing, positive partial-information coverage, unnecessary omission, causal negation and hidden-but-unsupported causes. Qualification is agent-assessed and construction-defined; it does not qualify a material-assertion primary endpoint or validate hardware/sensor completeness. Zero retries, zero alpha, no land binding changes. The one-shot runner refuses rerun after either success or a retained failure.

Commands from `/home/lunarz/worktrees/roboboat-terminal-evidence`:

```bash
# Already executed; replay output is immutable and this refuses overwrite.
PYTHONPATH=analysis python analysis/replay_roboboat_contact_policy_v2.py
# One-shot; inspect its terminal before attempting any action. Never retry a live/failed identity.
PYTHONPATH=analysis python analysis/run_roboboat_contact_policy_qualification_v2.py
# Numerical/temporal/contact validation (safe to rerun).
PYTHONPATH=analysis python -m pytest -q tests/test_roboboat_temporal_certificate_v2.py
```

No baseline response or old support label is rescored by this repair. New comparative use requires an equal-source/equal-contract method freeze and qualified endpoint mapping. Confirmation still requires coordinated inferential disposition, resources and untouched populations; replication remains unexecuted.


Contact-policy v2 numerical/replay validation is complete, but the separate semantic extension is **not qualified**. All twelve calls completed normally, with no retry. Each pass scored 14/15 atomic labels and 14/15 fields against the frozen reference; zero unsupported false acceptance and zero supported false rejection. Both fail the predeclared perfect-accuracy gates on case 04. Its authored response asserts continuous proof after saying it is unestablished; the expected limitation-preserved=true reference is inconsistent with whole-response stance. Both judges correctly retain the contrary assertion when assessing preservation, and both use contradicted rather than the frozen insufficient label for the proof assertion. Preserve the failed result, all gold and returns. `contact_policy_development_disposition_v2.json` records this project-agent reference review; it is not human adjudication or a revised passing score. Existing global/marine qualified bindings remain unchanged. No queue remains active. Next: prospectively audit/freeze fresh bounded reference cases and resolve materiality/coverage primary mapping; no same-case retry or confirmation activation.
