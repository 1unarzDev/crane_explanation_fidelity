# Five-method development reporting — 2026-09-30

## Dated resolution

The prospective comparison declaration already includes B2 versus B4 and B0, B1,
and B3 versus B4. The preserved v1 analyzer reports all contrasts and Holm-adjusts
the three secondary p-values. Its secondary rows omit explicit failure rates, and
its projected control descriptors use B2 field names for every comparator.

A separate [v2 reporting layer](../analysis/report_evidence_calibration_five_methods_v2.py)
adds uniform actual-method names, failure counts/rates, paired episode counts,
absolute B4-minus-comparator effects, useful-coverage numerators/denominators and
floor status. It retains every original estimate, whole-episode percentile bootstrap
bound, exact two-sided McNemar p-value and three-contrast Holm-adjusted p-value.
Controls and geometry remain descriptive and nonpooled. The original code,
comparison declaration, manifests and retained responses remain preserved.

Intervals are pointwise development intervals, not adjusted simultaneous intervals.
Their level, seed and replicate count come from the supplied development plan;
they do not select P11 procedures or spend alpha. Zero-spanning and degenerate
intervals are flagged. With no observed discordances, a degenerate empirical
bootstrap interval cannot establish population equivalence. All contrasts remain
reported for ties, unfavorable effects and inconclusive p-values. No confirmatory
rejection or equivalence decision is emitted.

The wrapper requires an exact canonical match to the active development comparison
declaration and refuses to overwrite an existing output. It accepts adjudicated
results through the existing analyzers; it does not authorize real-pilot scoring,
a method-key join, new endpoint mapping or semantic execution.

## Verification and remaining gates

23 targeted synthetic tests pass (eight new reporting checks and fifteen existing
analysis checks). They verify statistical preservation, correct comparator names,
coverage, tied and unfavorable results, declaration rejection and episode N under
additional masks. No retained response was scored or model/annotation call made.

Fresh aligned B0–B4 outputs, qualified automated annotation, shared validity rules,
coverage floor, endpoint mapping, exact intervals/weighting, alpha allocation,
sample size and P11 freeze remain open. The three secondary tests have zero
allocated discovery alpha. Failed combined support qualification and pending
measurement reopening remain unchanged; confirmation and replication N remain zero.
