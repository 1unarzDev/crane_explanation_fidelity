# Paper sources

Anonymous TRUSTMORE paper and supplementary-material sources belong here. Keep authors,
affiliations, acknowledgments, private repository URLs, and other identifying metadata out of the
double-blind branch. Every reported number must map to a retained result artifact through a
committed manifest.

`main.tex` is the living anonymous manuscript and `references.bib` contains only sources already
checked against the research notes. Red `PENDING` markers are intentional acceptance gates: they
must be replaced by manifest-traceable results after blinded annotation and prospective evaluation,
never by estimated or development-only values. The current draft compiles with the IEEE conference
class required by the workshop's IEEE BigData 2026 instructions. It is currently a six-page
short/WIP-length scaffold, including references. A full-paper submission still requires enough
prospective evidence to justify and fill 8--9 pages; the manuscript is not submission-ready while
its empirical gates remain open.

The living claim audit is `CLAIM_EVIDENCE_MAP.md`; exact development-number provenance and its
fail-closed validator are documented in `NUMBER_TRACEABILITY.md`. The manuscript story is a bounded legacy
provenance result followed by a separately prospective diagnosis-to-language method and
land/RoboBoat evidence only where the new study supports it. Simulation evidence must not be
presented as hardware validation, factual correctness as human trust, or lateral disturbance as
wave drift without discrimination.

Reproducible build command (downloads the pinned Tectonic 0.17.0 Linux archive and verifies its
SHA-256 before execution):

```bash
scripts/build_paper.sh
```

The PDF is written to `output/pdf/main.pdf`; pass a different output directory as the first
argument when building a scratch copy. Tectonic downloads its TeX bundle on first use, so a fresh
machine requires network access for that initial build. Before delivery, render every page with
Poppler and inspect it for column overflow, clipped tables, illegible references, and unresolved
red `PENDING` markers.

After building and visual inspection, run the fail-closed category/anonymity audit with the intended
submission category:

```bash
python scripts/audit_submission_readiness.py --category full
```

Use `short` or `demo` only after a deliberate category decision. The audit checks the corresponding
8--9 or 4--6 page range including references, unresolved `\pending{}` gates, anonymous author and
PDF metadata, developer-specific path/repository fragments, letter page geometry, font embedding,
PDF freshness, and numeric traceability. It does not submit or publish anything and does not replace
visual inspection. The current seven-page, results-pending draft is expected to fail.
