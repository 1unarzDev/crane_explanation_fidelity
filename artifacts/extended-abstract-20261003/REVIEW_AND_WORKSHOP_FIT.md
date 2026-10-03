# Extended abstract review and workshop alignment

## Target and requirements

Official source, retrieved 2026-10-03: https://www.ieee-aiot.org/2026/workshop-TNI-AIoT.php

TNI-AIoT welcomes early-career/demonstration abstracts of up to two pages, including figures and references, in English, IEEE conference two-column format, anonymous for proposed double-blind review. Short abstracts are non-archival presentations/discussion contributions.

The document connects the robot-visible evidence-to-language boundary to:

- Reliable foundation models and autonomous agents for AIoT.
- Explainability, risk assessment, and monitoring of deployed AIoT systems.
- Dependable digital twins and secure sensing-to-action processes.
- Testbeds, datasets, benchmarks, and reproducible evaluation.

Edge/cloud consumers motivate evidence-preserving communication; no network coordination, privacy, security, or deployment experiment is claimed. The website lists submission 30 October, notification 7 November, and camera-ready 16 October 2026; the camera-ready chronology is inconsistent and requires organizer verification if used for scheduling.

## Team review

Research/literature reviewer: sharpen novelty against REFLECT/HEXAR; exactly three contributions; distinguish physical truth from justified explanation; retain exploration/automated scoring boundaries.

Evidence reviewer: final framing 9.2/10, contribution clarity 9.1, numerical/statistical scope 9.0, honest limitations 9.3, robotics relevance 9.1. Visual clarity initially 8.5; requested arrow routing, episode-denominator title, and explicit B4 upper confidence limit were subsequently corrected.

Revision team: rewrote the robotics narrative, literature positioning, contributions, results, and proportional limitations. Orchestrator integrated official workshop themes, final figure, and two-page layout.

These are editorial reviews, not empirical validation or independent human agreement. No claim of unanimous 9+ on the underlying scorer's construct validity is made: phrasing cannot supply missing semantic validation. The shared ontology, template realization, narrow simulation cohort, exploratory stop, and usefulness proxy remain explicit limitations.

## Figure provenance and checks

Use `review-capsule/final-capture/mid.png`, rather than the earlier capsule run. The final-capture verification reports passed=true, strictHarnessValid=true, and a 5.10 s verified docking interval. This scene illustrates an ASV evidence interface; it is outside the quantitative land/Nav2 corpus. Earlier root-capsule failures are preserved.

The raw screenshot is unchanged. A vector legend replaces the visible historical platform title with ASV terminology. Vector arrows identify vessel, dock, observed trajectory, and local costmap. The figure pairs the scene with the exact E0–E3 ladder and B2/B4 adverse-flag proportions, using marginal Wilson 95% intervals and actual per-level denominators.

## Build and visual QA

```bash
python artifacts/extended-abstract-20261003/build_figure.py
tectonic abstract.tex --outdir artifacts/extended-abstract-20261003 --keep-logs
pdfinfo artifacts/extended-abstract-20261003/abstract.pdf
pdftoppm -scale-to 1400 -png artifacts/extended-abstract-20261003/abstract.pdf /tmp/crane-abstract-final
```

Compiled to two US-letter pages; both rendered pages inspected. No overlapping text, clipped figure labels, missing references, or overfull boxes were observed. The build has TeX font fallback notices and a PDF input-version notice; rendered output is legible. Main manuscript, immutable study outputs, and unrelated worktree changes were not modified.

## Revision 2: platform clarity and figure composition

User-requested second review/revision cycle: platform reviewer identified the ambiguous attribution of CRANE to the explanation algorithm, repeated causal-limit statements, and insufficient B2/B4 information-parity detail. Revision team added the CRANE platform definition, ROS-connected Unity/PhysX context, and a concrete E2/E3 diagnosis example. Visual reviewer supplied scene anchors for dock, ASV, observed trajectory, cyan route, and the short magenta desired-velocity twist.

Final integration: opaque dark scene labels with white text/arrow leaders; horizontal E0–E3 cards adjacent to grouped B2/B4 bars with Wilson whiskers; compact method key and interval note directly below the chart; B2/B4 explanation panels in the upper right. Recorded colored traces remain unchanged. B4 zero values are shown at baseline with their actual upper interval, not positive-height bars. Figure caption and redundant prose were shortened to retain two pages at normal IEEE formatting.

The platform supports investigation across land and surface domains, but this abstract does not claim measured Isaac Sim speed/hardware advantages or demonstrated real-world transfer. Earlier failed approaches remain in repository history and are omitted from this focused abstract. Final two-page PDF and source figure were visually inspected; no missing glyphs, clipped legends, or overlapping labels remain. Editorial review is separate from empirical validation.

## Revision 3: spacing and final user corrections

Rebuilt the figure on a consistent grid with restrained typography and aligned panel headings. Cropped the lower empty-water display area without altering the source capture; compressed the method descriptions into aligned paths. Removed route, trajectory, and desired-velocity scene callouts, retaining their color legend. Remaining scene labels use 68% opacity dark fills and white leaders. Thin chevrons without shafts replace the ladder arrows. Chart rates and confidence intervals are now loaded directly from the frozen results rather than handwritten numeric literals. Added the explicitly requested public CRANE platform repository citation; the link exposes project identity despite the anonymous author block. The final PDF remains two pages.
