# Paper sources

Anonymous TRUSTMORE paper and supplementary-material sources belong here. Keep authors,
affiliations, acknowledgments, private repository URLs, and other identifying metadata out of the
double-blind branch. Every reported number must map to a retained result artifact through a
committed manifest.

`main.tex` is the living anonymous manuscript and `references.bib` contains only sources already
checked against the research notes. Red `PENDING` markers are intentional acceptance gates: they
must be replaced by manifest-traceable results after blinded annotation and prospective evaluation,
never by estimated or development-only values. The current draft compiles with the IEEE conference
class required by the workshop's IEEE BigData 2026 instructions. It remains a four-page draft and
is not submission-ready while those gates remain.

The living claim audit is `CLAIM_EVIDENCE_MAP.md`. The manuscript story is a bounded legacy
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
