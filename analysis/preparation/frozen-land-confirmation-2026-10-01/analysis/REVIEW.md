Read-only frozen analysis review, 2026-10-01

Declaration SHA256: `77e0c6ac4f8da3eccfeeb5ed31990d504a907953f63e8c19822e4e0c4e540ac2`.
No actual confirmation response, blind score, join key or effect was accessed. No model/provider call was made. Frozen scientific code and artifacts were unchanged.

The implementation matches the registered primary mechanics: union of failures across A/B and four levels; intersection of coverage across A/B; equal weighting of episode coverage; exact directional McNemar at N1200; descriptive two-sided p retained; alpha .01; both useful-coverage thresholds; adjusted projected Clopper–Pearson interval; zero discordance at N600 terminal p1; any discordance at N600 produces a continuation-only artifact without estimates or p-value. Concordant failures remain failures while contributing no discordance. Twenty synthetic checks passed, including both terminal sizes and interval boundaries. Run `python3 analysis/preparation/frozen-land-confirmation-2026-10-01/analysis/synthetic_review.py` to reproduce.

The scorer CLI returns zero even if individual records fail. The analyzer fails closed on any nonvalid record, duplicate, missing or extra score before joining method identities. A synthetic omitted score confirms this. Process exit code alone must not be treated as successful annotation. No change to frozen code is needed: preserve failed requests, resume only scoreless technical failures identically, and assemble only the first valid return per episode/pass in a fresh namespace. Never retry an already structurally valid annotation, even when its judgment is poor.

Missingness uses incomplete attempted method pairs and physical/outside-population disposition records. Its arbitrary-missing-pair bounds correctly matched the synthetic fixture. A defensive limitation is that the implementation assumes incomplete method rows and disposition rows are disjoint: a hypothetical row carrying both `METHOD_TECHNICAL_FAILURE` disposition and `b2_calls` could be counted twice. The execution/accounting reviewer should verify the actual metadata schema, without looking at responses. Do not silently alter frozen code if a real discrepancy is found.

The first-look analyzer computes internal aggregates to determine discordance, but persists only the registered continuation flag for nonzero discordance. That branch must remain coordinator-only; no preparation task should ingest annotation artifacts. The reported mean coverage criterion is descriptive, with no inferential coverage test added.

No established material statistical defect or blocker was found. Residual scientific limitations include shared same-model judge error, possible style recognition, simulator-population generalizability and complete-pair selection under technical missingness. Automated agreement does not establish human validity; zero development discordance does not demonstrate equivalence.

Preparation helpers are transport/export utilities only. They add no qualification requirement, model calls, stopping rules or scientific revisions. They must not execute on confirmation outcomes before their registered release.
