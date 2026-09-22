# Paper sources

Anonymous TRUSTMORE paper and supplementary-material sources belong here. Keep authors,
affiliations, acknowledgments, private repository URLs, and other identifying metadata out of the
double-blind branch. Every reported number must map to a retained result artifact through a
committed manifest.

`main.tex` is the living anonymous manuscript and `references.bib` contains only sources already
checked against the research notes. Red `PENDING` markers are intentional acceptance gates: they
must be replaced by manifest-traceable results after blinded annotation and prospective evaluation,
never by estimated or development-only values. A TeX engine/template installation is not currently
present in the workspace, so PDF compilation remains `NOT_RUN`.

The living claim audit is `CLAIM_EVIDENCE_MAP.md`. The manuscript story is a bounded legacy
provenance result followed by a separately prospective diagnosis-to-language method and
land/RoboBoat evidence only where the new study supports it. Simulation evidence must not be
presented as hardware validation, factual correctness as human trust, or lateral disturbance as
wave drift without discrimination.

Expected build command once the official IEEE template/toolchain is installed:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```
