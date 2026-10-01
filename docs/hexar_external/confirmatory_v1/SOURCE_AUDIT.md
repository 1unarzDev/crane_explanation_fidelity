# Prospective HEXAR superiority: source and alpha audit

**Historical disposition superseded prospectively:** the later [fixed-sequence amendment](FIXED_SEQUENCE.md) retains B4/B2 as H1 and makes HEXAR H2 eligible only upon H1 rejection within one .01 family. No release document is required. The source hashes and historical accuracy recalculation below remain valid; development and acquisition qualification proceed without alpha consumption.

Audit date: 2026-09-30. Status: **BLOCKED_ALPHA_CONFLICT**. No alpha is bound or consumed by this audit; no semantic outputs are generated. This document records repository-owned sources and a read-only recalculation of the authors’ released labels.

## Discovery allocation cannot currently be assigned

The authoritative [ledger](../../../manifests/study/diagnostic-sequential-error-ledger-v2.json) contains program alpha 0.05: 0.02 permanently consumed by `focused-supported-diagnostic-communication-v1-confirmation`, 0.01 `candidate-revision-reserve` marked `AVAILABLE`, and 0.02 `selected-method-replication` marked `AVAILABLE`. The consumed 0.02 belongs to an earlier focused campaign; it does **not** establish that the current B2-versus-B4 evidence-calibration claim has been tested or completed.

The [error-budget audit](../../../manifests/study/evidence-calibration-error-budget-audit-v1.json) explicitly calls the discovery allocation `AUDITED_PROVISIONAL_UNBOUND`, limits it to one primary confirmatory endpoint, and requires binding in the P11 freeze after the fresh pilot. Its replication protection states: “The replication allocation cannot be borrowed for discovery, pilot work, judge qualification, or infrastructure failures.” Thus the ledger’s word `AVAILABLE` is insufficient evidence of availability for a second unresolved discovery claim.

The latest shared `main` and `land-evidence-calibration-study` both resolve to `630c8e2d25eb643b09a2af3de7171e9a27671829`. Their [current-state checkpoint](../../CURRENT_STATE_2026-09-30.md), inspected with `git show main:docs/CURRENT_STATE_2026-09-30.md`, explicitly says “B2 versus B4 remains the sole candidate primary discovery test,” with P11 closed, nineteen open conditions, and confirmation/replication N=0. Later interface/context-capacity updates retain those boundaries. The main-branch P11 readiness manifest has `status=NOT_READY_CONFIRMATION_PROHIBITED`, `confirmation_authorized=false`, `confirmation_independent_n=0`; its `error_budget_allocation` requirement says final binding remains a P11 action after the fresh pilot. The main [protocol](../../EVIDENCE_CALIBRATION_PROTOCOL.md) likewise preserves the existing ledger and requires prospective B2/B4 inference.

**Disposition:** fail closed. The same 0.01 is still needed by the unresolved internal B2-versus-B4 discovery candidate. There is no documented retirement, completed inferential role, or release of that candidate. Assigning another 0.01 to HEXAR would double-commit the one remaining discovery reserve. The protected replication 0.02 cannot resolve this conflict. A proposed external amendment must remain blocked and unbound until an explicit prospective global decision resolves the competing claim; merely relabeling the reserve is insufficient. No shared ledger was edited.

## Historical HEXAR 49/54 is verified separately

The primary source is the authors’ [released CSV](https://github.com/fgebelli/HEXAR/blob/f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc/detailed_results.csv), retained locally at `data/hexar_external/upstream/detailed_results.csv`. The upstream checkout resolves to `f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc`. SHA-256 of that CSV is `8a441ef1601be34cbf3be6b13ab78df8421a0973320a5ad1c3e41bca95ffcb7b`.

A new read-only `csv.DictReader` calculation filtered `ablation == "explanation"` and `category == "navigation"`, summed integer `accuracy_majority`, and counted unique `bagfile`. It reproduces 49/54 = 0.9074074074 (90.7%), from 18 physical recordings. The full CSV has 540 rows. This subset has 54/54 root-cause correctness labels and 5/54 incorrect-fact labels. Every navigation primitive/accuracy majority agrees with at least two of the three released rater labels (zero mismatches).

All six released navigation families contribute nine queries: `charging`, `dynamic_env`, `localization`, `manual_joystick`, `obstacle`, and `success`. The [existing recalculation](../../../data/hexar_external/audit/historical_results.json) matches those counts. Its [source analysis](../../../analysis/hexar_external/audit_release.py) preserves original labels and additionally audits experiment correspondence, pairing, aggregation, and per-rater accuracy.

The authors’ [paper, version 1](https://arxiv.org/html/2601.03070v1), §§V-A, V-C–V-E, supplies metric definitions, the 60-execution/180-query design, blinded three-coauthor human annotation, and rounded overall results. Cached primary text: `data/hexar_external/primary_sources/paper_v1.html`, SHA-256 `e1c0665097acb4bedf2cdc00dce4c2a0ec951c24fa41313c94aa7e9254685aef`. The exact **navigation subgroup** 49/54 is a recalculation from released artifacts; it should not be presented as a separately reported paper-wide published accuracy. The paper’s original accuracy concerns ground-truth root-cause identification without incorrect facts. The new endpoint concerns evidence calibration under visible evidence and does not demonstrate improvement on HEXAR’s complete original metric suite.

## Auditable source identities

The following SHA-256 values bind the inspected bytes. Paths prefixed `main:` were read with `git show` from main commit `630c8e2d25eb643b09a2af3de7171e9a27671829`; links to working-tree files may show older branch-local snapshots. Main and land agree at this audit.

| Source | SHA-256 |
|---|---|
| `main:manifests/study/diagnostic-sequential-error-ledger-v2.json` (same locally) | `d6e67e9d4c8da68c434fa639a67ce34de53039f85734c51714a83973bca2dfbe` |
| `main:manifests/study/evidence-calibration-error-budget-audit-v1.json` (same locally) | `c0ae56b3e1f61c1aaa1d7e0bf0f65ddd64b6c7912f39bd07d5f100d7ab51d415` |
| `main:docs/CURRENT_STATE_2026-09-30.md` | `bdaaec11bbee2549ca9ed924204871857caea1ea266a2ede600064e47599997d` |
| `main:manifests/study/evidence-calibration-p11-prefreeze-readiness.json` | `0f82b7cc0d3ff6c01319e1b66732424ca2c0a9d2d9c05fe84adcbe755d0cce1f` |
| `data/hexar_external/audit/historical_results.json` | `722cfe7e3a05e6a0851e075d1d534816307e48a079ccb7018062335718439c48` |
| `analysis/hexar_external/audit_release.py` | `bb0b16ae8f335454acc28191d52106c94aa241cdf61a5d5bab81c8e8c8420410` |

The inspected twelve-recording comparison remains development/external-validation evidence. The historical CSV calculation reads previously published annotations; it creates neither new model output nor confirmatory observations.
