# Land-study / RoboBoat branch correction — 2026-09-30

Land evidence-calibration work was committed to the incorrectly named
`codex/roboboat_terminal_evidence` branch. This record corrects branch ownership;
it does not amend scientific results, qualify measurement, allocate alpha or freeze P11.

## Preserved histories and dependencies

| History | Original range | Commits | Destination |
| --- | --- | ---: | --- |
| Land evidence calibration | `6581279d` through `a93a3b93` | 68 | `land-evidence-calibration-study`, integrated into `main` |
| Genuine marine terminal evidence | `b0602c24` through `641c46d9` | 27 | `codex/roboboat_terminal_evidence` |
| Original misnamed branch | complete original tip `a93a3b93` | unchanged | `backup/roboboat-terminal-evidence-before-land-split-2026-09-30` |

Both histories descend from `9a81db860f9eec66557240b2297cd122fba9ca06`, the
pre-correction `main` tip. The 68 land commits form a linear chain, with no intervening
marine commit or merge. Retaining that chain preserves the dependency order for
annotation inventories/retained failures, five-method request preparation, realization,
runtime checks, MCP/resource controls, response egress and source binding. It also
preserves commit identities used by the dated scientific record and DVC pointers.
No cherry-picking or rewriting of those scientific commits is necessary.

The 27 genuine marine commits were already isolated on the local
`roboboat-terminal-evidence` branch. Their changes are marine-specific analysis,
documentation, manifests, research artifacts and tests, plus the marine component
gitlink update in `packages/crane_ml`. Preserve that dependency at its recorded revision.
They do not change the land manuscript, shared scientific decisions or shared DVC
pointer relative to the common base. The unrelated RoboBoat docking and HEXAR branches
are outside this correction and retain their existing histories.

`manifests/operations/branch-separation-2026-09-30.json` inventories every original
commit, its parents and changed paths, both tree identities, and component gitlinks.
The backup was pushed before changing either production branch reference. The land
branch receives this administrative record after the original research chain.

## GitHub correction

Integrate the land branch into `main` without changing the original 68 commit hashes.
Replace the misnamed remote branch tip with the genuine marine tip using an explicit
lease on the backed-up remote commit. Keep the backup reachable on GitHub. This leaves
`main` and the clearly named land branch with the land-study work, and the RoboBoat
branch with the genuine marine work. No existing pull requests were found during the
pre-correction GitHub inspection. Recheck remote branch identities after publication.

Scientific gates remain unchanged: P11 is closed, confirmation/replication N=0,
measurement reopening is pending, and all prospective five-method comparison and
reporting requirements remain in force.
