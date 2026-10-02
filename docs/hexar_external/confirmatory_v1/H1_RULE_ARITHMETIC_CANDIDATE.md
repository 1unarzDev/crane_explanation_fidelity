# H1 gate arithmetic preparation; actual results unopened

The frozen H1 analyzer source was read and its SHA-256 checked against the original H1 freeze. A byte-identical source copy and receipt are retained under `h1_rule_arithmetic_candidate_v1`. No H1 answer, label, effect, p-value or terminal result was opened, and no H1 source was modified.

`h1_rule_candidate_v1.py` exercises the unchanged rule using synthetic inputs only: first look at 600 complete independent pairs can stop only for zero-discordance futility or require continuation; a final positive decision requires 1,200 pairs, the exact one-sided paired-discordance threshold .01, superiority direction and both frozen coverage constraints. It computes the binomial tail with integer/rational arithmetic. Incomplete or wrong-look N has no nominal positive p-value. Invalid paired counts and impossible coverage inputs are rejected.

Ten scoped synthetic checks pass. Together with the companion/proof and prepared streaming-audit rejection tests, 29 focused checks pass. This is arithmetic preparation, not complete H1 validity qualification. The function contains no actual result reader and always denies H2 activation. Raw/annotation/accounting reproduction, provenance, stopping chronology and procedural-validity checks still require a qualified immutable-result adapter after the complete H2 freeze. User authorization of the timing change alone cannot replace them.

The original frozen H1 has a different status/schema from the earlier hypothetical family fixture. A future versioned adapter must explicitly bind these actual commitments rather than retroactively asserting that H1 executed under the old unbound H1→H2 companion.
