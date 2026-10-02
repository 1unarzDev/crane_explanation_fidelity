# Post-output semantic review of the frozen v1 assertion-role task

Date: 2026-09-30. Status: **development diagnosis, not regrading or qualification**.

The frozen synthetic task is
`research/explanation_fidelity/qualification/evidence-calibration-claim-role-v1-development.json`
(raw SHA-256 `2f34e7b6f258110cd661a36bc59277c028820fa73f4d22a4bbb746c12794990e`).
Its prompt is
`research/explanation_fidelity/prompts/evidence-calibration-claim-role-v1-development.md`
(raw SHA-256 `b64613c5ce29022dee61653399ad11c5ea76b2a41fed4dd80d80861ff7fdd18e`).
The retained failed-outcome manifest is
`manifests/study/evidence-calibration-claim-role-v1-qualification-outcome.json`
(raw SHA-256 `14d9957b35c9612d1a8a29916e0230c82d43ab4f7b7abd0f8f45150932733914`).
This review was performed **after** both model passes. It cannot amend v1 gold, turn a
disagreement into an agreement, or qualify v1.

The structural audit found 49 valid calls and no retry. Pass A matched 12/20 held-out cases;
pass B matched 14/20. The union of mismatched cases is below. A mismatch may reflect model
behavior, an underdefined reference, or both; the frozen failure remains the disposition.

| Case and atom | Observed disagreement | Post-output interpretation for successor construction |
| --- | --- | --- |
| `role-ho-02/c1`, `role-ho-03/c2` | Both passes sometimes put completed `Wait` at `software_action_failure` rather than `recovery_mechanism`. | The prompt does not explicitly map a completed recovery child, as distinct from recovery invocation or measured recovery, to a level. Define the event kind before assigning abstraction. |
| `role-ho-03/c1` | Pass A puts “Motion returned” at `task_outcome`; pass B matches the recovery reference. | The text omits the measurement source and interval. A successor reference should say whether it means measured response recovery. |
| `role-ho-07/c2` | Pass A puts “Response loss occurred” at `command_motion_discrepancy`; pass B matches `physical_execution_mechanism`. | The atom has no explicit command comparison or measurement basis. A physical response observation, a command-motion relation, and a proposed mechanism need distinct definitions. |
| `role-ho-08/c2` | Both passes put hedged wheel slip at `physical_execution_mechanism`; gold says `specific_physical_cause`. | The ontology treats wheel slip as a specific cause, but the role prompt lacks an explicit example or mapping. The successor must bind this mapping and the endpoint treatment of hedged candidates. |
| `role-ho-12/c1,c2`, `role-ho-13/c1` | Both passes treat direct-route restriction and connected detour as observations, or choose a different level. | The linear label `physical_execution_mechanism` does not name geometry/planning, although the ontology has distinct geometry claims. Use a declared geometry claim kind or an explicit cross-family mapping; do not silently force geometry into a motion level. Geometry remains non-pooled. |
| `role-ho-16/c2` | Both passes call “the quoted text is not a robot diagnosis” source/observation; gold calls it a limitation. | The prompt does not draw a crisp boundary between a source-attribution fact and a diagnostic non-entailment. Construct separate unambiguous examples. |
| `role-ho-18/c1` | Pass A treats absence from the retained trace as a recovery assertion; pass B matches source/observation gold. | The statement concerns a record, not physical nonoccurrence. Keep the paired `role-ho-19` contrast, but write the distinction explicitly in a new task. |
| `role-ho-20/c1` | Both passes elevate five seconds of stationarity to a physical-execution level; gold calls it observation. | Stationarity alone lacks delivered-command comparison or cause. State that raw measured motion is an observation, then test the relation separately. |

The following are **construction requirements**, not a new instrument or a changed endpoint:

1. Keep speech act (affirmative, hedged, limitation, source/observation, hypothetical) separate
   from ontology claim kind and diagnostic abstraction. A task outcome or negative physical
   finding is not automatically a mechanistic primary-endpoint claim.
2. Define recovery invocation, recovery-child completion, measured response recovery, raw
   stationarity, command-motion discrepancy, physical mechanism, and specific cause with
   distinct examples and exact evidence-neutral wording.
3. Give geometry/planning its own declared type or a prospectively bound cross-family map;
   keep its secondary-arm status.
4. Resolve the hedged-candidate and unresolved-role endpoint mappings from valid development
   evidence before P11. Do not infer them from the failed v1 labels.
5. Construct a new reference-complete held-out suite before model calls. The exposed v1 held-out
   cases may guide development examples but cannot be reused as fresh held-out qualification.

No pilot role labels, support annotations, B2/B4 effect estimates, confirmatory calls,
independent episodes, or alpha are created by this review.
