# Category A: released historical annotations

| Released method | All accuracy | Navigation accuracy | Navigation wrong-info |
|---|---:|---:|---:|
| HEXAR | 167/180 (92.8%) | 49/54 (90.7%) | 5/54 |
| No reasoning module | 121/180 (67.2%) | 31/54 (57.4%) | 23/54 |
| LLM baseline | 118/180 (65.6%) | 49/54 (90.7%) | 5/54 |

These are the authors' majority-label metrics, not the new evidence-support endpoint. No new experimental improvement is inferred.

# Categories B/C: fresh component adaptation and evidence-sufficiency extension

| Method | Useful supported success¹ | Required-unit coverage² | Unsupported material¹ | Unsupported causal relation¹ | Intact success¹ | Median words |
|---|---:|---:|---:|---:|---:|---:|
| HX-ORIGINAL | 4.6–4.6% | 28.2% | 59.3–59.3% | 55.6–56.5% | 2.8–2.8% | 11 |
| HX-PROMPT | 90.7–90.7% | 100.0% | 9.3–9.3% | 5.6–5.6% | 80.6–80.6% | 43.5 |
| HX-CONTRACT | 100.0–100.0% | 100.0% | 0.0–0.0% | 0.0–0.0% | 100.0–100.0% | 29 |

¹ Full declared denominator: 108 answers/method, grouped by 12 physical recordings in six known families. Ranges are unknown-label/role bounds, not confidence intervals. Intact denominator: 36 answers/method.
² Mean compact required-unit coverage among finalized agent assessments; not exhaustive information coverage. Unsupported material includes noncausal facts. Causal roles are independently blind-coded developer judgments, not qualified/human-validated; qualified support labels are unchanged.

Registered contract-minus-prompt full-cohort effect bounds: **[+9.3, +9.3] percentage points**. Complete principal recording pairs: 12/12. No confirmatory alpha or p-value.
Predeclared contextual contract-minus-original contrast on the same endpoint: [+95.4, +95.4] percentage points; complete recording pairs:12/12. HX-ORIGINAL keeps its concise upstream format; the equally formatted strengthened baseline is the principal comparator.

Descriptive recording t95: +2.6 to +15.9 points; complete six-family sensitivity: +3.2 to +15.3 points. Seven favorable, five tied, zero unfavorable recording pairs. Zero alpha; no confirmatory superiority claim. See [PAPER_SECTION.md](PAPER_SECTION.md) for scope and tradeoffs.
