# Received-result coverage audit

The read-only v33 auditor extends v28 to admit honest missing-result fixture timeouts into the measurement audit without counting them as short received-result windows. It leaves the bound collector, queued assay, player, original admissions and method packets unchanged.

Fixed profile-v10 retains all 348 scheduled dispositions: 59 valid recordings, seven technical failures, two running and 280 unattempted; 26 geometries have both tolerance variants admitted. These are development recordings, not scored independent method pairs.

Of 59 valid recordings, 53 received action results and six reached the fixture deadline without a received result. The six have empty raw and L2 post-result inventories, null result receipt and elapsed post-result time. Their spans and hypothetical dual-clock gates remain null. This does not establish ROS cancellation completion or a physical docking failure.

Among the 53 received-result recordings, 48 have complete sampled windows and five have simulator-header spans shorter than the five-second dwell: `00062-v2` (0.30 s), `00066-v2` (0.58 s), `00056-v1` (1.28 s), `00059-v1` (0.30 s), and `00138-v1` (0.34 s), all prefixed `boat-geom-42007-`. Raw and exported sample counts and simulator timestamps match for all 59 recordings. Per-sample wall times are raw diagnostics, not packet fields. No extraction loss or causal slowdown is established by this audit.

The actual v28 auditor rejects this fixed snapshot because a timeout's elapsed post-result time is null. The successor processes the same snapshot; eight explicit regression checks pass, including separate denominators, null timeout spans/gates and retention of every scheduled row. Source hashes, inputs and results are recorded in `post-result-coverage-qa-v33-001.json`. This qualifies the read-only audit only, not the dual-clock runtime candidate or the explanation endpoint.

The queued two-case assay remains the prospective operational test of the isolated dual-clock capture candidate. No new method generation, model judging, endpoint score, statistical N or confirmation freeze follows. Archived snapshot files exclude raw logs and owned player binaries; their immutable bindings remain in the artifacts and originals remain on the collection host.
