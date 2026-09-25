# Manuscript numeric traceability

Status: **LIVING AUDIT — DEVELOPMENT VALUES CHECKED; FINAL RESULTS PENDING**.

Run from the umbrella root:

```bash
python scripts/audit_paper_numeric_traceability.py
```

The validator fails if a mapped source file is no longer pinned by its governing manifest, if an
underlying value or derived count changes, if a diagnostic condition key no longer matches its
recorded hash, or if the corresponding display value disappears from `paper/main.tex`.

| Manuscript claim family | Authoritative retained source | Governing manifest / derivation |
| --- | --- | --- |
| Legacy 33-cluster disposition; 17 recovery-success, 16 abort; frozen 40/50 bounds; 198 calls; 46/66 (69.7%) G fallback | `manifests/study/research-redirect-20260922.json` | Direct disposition fields; percentage recomputed as `100 * 46 / 66` |
| RoboBoat terminal margin and post-result motion | `data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json` | `manifests/data/roboboat-terminal-margin-development-v1.robot-visible.json`; measurements selected by ID |
| Land blockage direct-route restriction, detour, and deadline alignment | `data/robot_visible/dev/diagnostic-pilot-v1/land-blockage-global-002/geometric-diagnostic.json` and adjacent `fixture-summary.json` | `manifests/data/land-blockage-global-002.robot-visible.json`; planning updates are `len(planHistory)` |
| S-turn restriction, deviation, and deadline alignment | `data/robot_visible/dev/diagnostic-pilot-v1/land-s-turn-unexpected-abort-001/geometric-diagnostic-v2.json` and adjacent `fixture-summary.json` | `manifests/data/land-s-turn-unexpected-abort-001.robot-visible.json`; planning updates are `len(planHistory)` |
| Prospective nominal land displacement, deviation, and 90-second XML deadline | `data/robot_visible/dev/diagnostic-pilot-v1/diagnostic-land-nominal-20260922-001/geometric-diagnostic.json` | `manifests/data/diagnostic-land-nominal-20260922-001.robot-visible.json` |
| Warehouse lower-bound recovery sequence | `data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/recovery-execution-diagnostic.json` | `manifests/data/ecological-warehouse-recovery-development-v1.robot-visible.json`; exact lifetime count remains deliberately unclaimed |
| Delivered-plan count, geometry, odometry deviation, and 12,975 retained poses | `data/robot_visible/dev/diagnostic-land-dev-004/geometric-route-diagnostic-v2.json` and adjacent `fixture-summary.json` | `manifests/data/diagnostic-land-dev-004.robot-visible.json`; pose total recomputed as the sum of every retained plan's pose list |
| Held command-motion samples, interval, speeds, failures, and recoveries | `data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json` plus `research/explanation_fidelity/annotations/development/diagnostic-command-motion-supported-pilot-v1-reference.json` | `manifests/data/diagnostic-motion-dev-cm-001.robot-visible.json` and `manifests/annotation/diagnostic-command-motion-supported-pilot-v1.json` |
| Nominal command-motion displacement | `research/explanation_fidelity/annotations/development/diagnostic-command-motion-nominal-pilot-v1-reference.json` | `manifests/annotation/diagnostic-command-motion-nominal-pilot-v1.json` |
| Compensated discrepancy and measured-response recovery windows | `data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-compensated-001/evidence-and-diagnostic.json` | `manifests/data/diagnostic-motion-development-cm-002.robot-visible.json` |
| Diagnostic 52-response, 13-packet, nine-cluster inventory and 13/13 P fallback | `manifests/annotation/diagnostic-development-pilot-v1.json` plus its thirteen hash-pinned evaluator-only keys | Inventory counts are direct; fallback is recomputed from the single P entry in every packet key |
| Historical Luna v7 reference-audited held-out qualification and sensitivity | `manifests/annotation/luna-model-judge-v1-heldout-v7-reference-audited.json` and `research/explanation_fidelity/experiment_configs/prospective/diagnostic-sequential-protocol-v2-annotation-amendment-2.json` | Direct pass-specific composite, required-unit, core-field, false-rejection/acceptance, protected-gate, and upward-rounded Wilson sensitivity values; both original passes qualified and zero confirmatory responses were scored |
| Prospective Luna command--motion endpoint-threat extension failure | `manifests/annotation/luna-model-judge-v7-endpoint-threat-extension-1-disposition.json` | Direct pass-specific extension counts: composite 16/20 and 17/20, core 162/192 and 167/192, protected injection/boundary failures in both passes, 48/48 calls completed, zero alpha consumed; extension bounds are ineligible and candidate-v3 semantic activation is blocked |
| Land command--motion physical/reference cohort progress and bounded findings | `manifests/data/cm-land-conf-001-disposition.json` through `manifests/data/cm-land-conf-028-disposition.json` | Twenty-eight of 100 fixed confirmation configurations attempted and valid; runs 003, 006, 018, and 028 are mechanism-insufficient after independently configured odometry masks while retaining execution facts; runs 004, 008, 011, 015, 016, 024, and 026 record recovered measured response followed respectively by abort and six successes; runs 005, 007, 012, and 013 are nominal `not_triggered` controls; runs 009, 010, 014, 017, 019, 020, 021, 022, 023, 025, and 027 are persistent discrepancies followed by abort; no semantic calls or effect estimate |
| Separate scenario-binding-qualified route-change development scoring: eight valid calls, P/R/T success and N failure in both passes, P-minus-R 0.0 twice | `model_outputs/automated_annotations/luna-model-judge-v1/diagnostic-land-binding-route-change-v1/development-summary.json` | `manifests/annotation/luna-diagnostic-land-binding-route-change-v1-result.json` pins the result hash and records the two pass summaries; development-only, zero confirmatory clusters and alpha |
| Bounded nonterminal composition analysis and ineligible Luna audit | `manifests/data/diagnostic-land-composition-dev-009-composition-result.json` and `manifests/annotation/luna-land-diagnostic-composition-language-v1-result.json` | The first pins the supported 10--51 s composition and withholding; the second preserves the incomplete packet audit and explicitly forbids comparative use |

The audit intentionally excludes bibliography years, equation notation, section/question labels,
LaTeX layout dimensions, and red pending-result placeholders. Those are not empirical results.
Any future study-response or human-adjudication numbers must be added here and to the validator
before corresponding manuscript gates are removed.
