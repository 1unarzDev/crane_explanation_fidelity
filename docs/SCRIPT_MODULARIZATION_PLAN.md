# Script Modularization Plan

## Objective

Reduce the Python sprawl into a small, discoverable set of modular tools while preserving every result needed for scientific, operational, or provenance review.

The repository currently contains 789 Python files: 429 in `analysis/`, 252 in `tests/`, 95 in packages, and 12 in `scripts/`. The dominant problem is duplicated, versioned experiment code rather than the number of Python files alone.

The target is a stable library with thin command-line entry points, an explicitly marked active test suite, and an immutable archive for historical experiments.

## Design principles

1. **The current study defines the active surface.** The frozen confirmation manifest, current runbooks, and current execution commands determine what remains operational.
2. **Historical results remain reproducible records.** Superseded scripts move to an archive with metadata; they are not silently rewritten or deleted.
3. **Libraries own behavior; scripts own orchestration.** Business rules, schemas, validation, scoring, and persistence belong in importable modules. CLIs should parse arguments, call library functions, and write declared artifacts.
4. **One concept has one implementation.** Version suffixes describe historical snapshots, not parallel implementations of the same current behavior.
5. **Boundaries stay explicit.** Robot-visible evidence, evaluator-only truth, provider adapters, and retained result records must remain separate.
6. **Every migration is reversible.** Move code in small commits and keep compatibility wrappers until downstream callers have migrated.

## Target layout

```text
src/crane_explain/
  contracts/       # evidence, claims, methods, episode and result schemas
  evidence/        # capture loading, runtime presentation, provenance links
  methods/         # B0–B4 and checked-method implementations
  execution/       # provider adapters, retries/denials, accounting, ledgers
  evaluation/      # annotation records, scoring, paired tests, coverage
  manifests/       # study/configuration manifests and validation
  reporting/       # tables, summaries, traceability and status reports
  cli/             # thin command-line adapters

tools/
  run_confirmation.py
  score_annotations.py
  validate_manifest.py
  build_report.py
  audit_readiness.py

tests/
  unit/            # fast library tests
  integration/     # filesystem/provider/manifest integration tests
  active/          # current study regression tests
  historical/      # opt-in tests for archived implementations

archive/
  analysis/<family>/<date>/
  tests/<family>/<date>/
  INDEX.md
```

The exact package location may follow the existing package conventions, but the separation between reusable library code, thin CLIs, and archived experiments is required.

## Classification before migration

Create `docs/script-inventory.csv` (or an equivalent generated manifest) with one row per Python file:

- path and Git history
- role: library, CLI, validator, test, experiment, generated helper, or fixture
- lifecycle: active, transitional, historical-retained, or removable candidate
- imports and repository references
- produced artifacts and consuming reports
- canonical replacement, if any
- required command and expected inputs
- migration owner and status

Classify from evidence, not filenames. A dated file is historical only when no active manifest, runbook, test command, or current result depends on it.

## Canonical module boundaries

### Contracts

Define typed schemas for evidence records, claims, provenance links, method calls, physical calls, annotations, failures, and result envelopes. Validate at boundaries and serialize deterministically.

### Evidence and provenance

Centralize loading and normalization of robot-visible records, evaluator-only records, runtime presentations, source links, hashes, and configuration identity. No method should parse raw JSON independently.

### Methods

Expose a common interface such as:

```python
class ExplanationMethod(Protocol):
    name: str
    def explain(self, episode: Episode, evidence: EvidenceView) -> MethodResult: ...
```

B0–B4 and the checked method should implement this interface while retaining their declared evidence restrictions.

### Execution

Put provider adapters, call envelopes, usage/cost accounting, technical-failure handling, and no-retry rules in one package. The study runner should depend on the adapter interface, not provider-specific code.

### Evaluation

Centralize annotation import, blinded scoring, episode-level failure rules, coverage calculations, paired tests, and interval calculations. Evaluation must consume retained result envelopes without importing execution internals.

### Reporting

Generate current summaries and traceability tables from structured records. Reports should link back to manifests and artifact paths rather than embedding duplicated facts in multiple scripts.

## Migration phases

### Phase 0: Freeze and inventory

- Record the active confirmation commands and required files.
- Generate the inventory and dependency/reference graph.
- Mark current scripts and tests with `active`, `historical`, `transitional`, or `candidate` status.
- Add a CI check that prevents an unclassified Python file from entering `analysis/` or `tests/`.

**Gate:** every Python file has an owner, lifecycle status, and replacement decision.

### Phase 1: Extract shared foundations

- Introduce the contract types and deterministic serialization.
- Move duplicated path, hashing, JSON, manifest, and artifact helpers first.
- Add unit tests around each extracted helper.
- Keep old scripts as compatibility wrappers that call the new modules.

**Gate:** active commands produce byte-equivalent or explicitly versioned equivalent artifacts.

### Phase 2: Consolidate execution and methods

- Extract provider adapters and execution accounting.
- Implement the common method interface.
- Move B0–B4 and checked-method logic behind that interface.
- Replace versioned active runners with thin `tools/` commands.

**Gate:** a clean checkout can run the declared smoke test and one retained development fixture without importing archived code.

### Phase 3: Consolidate evaluation and reporting

- Move annotation, scoring, coverage, paired analysis, and report generation into library modules.
- Make report inputs explicit manifests and retained result paths.
- Remove duplicated calculations from historical runners only after their results are captured and indexed.

**Gate:** current reports are regenerated from retained artifacts with no manual script edits.

### Phase 4: Archive and simplify tests

- Move superseded versioned scripts and their tests into dated archive families.
- Mark historical tests opt-in and exclude them from default CI.
- Delete only generated helpers and candidates with no references, retained output, or provenance value.
- Update all documentation links to canonical tools.

**Gate:** default CI covers the active package and active study; an archive audit confirms every moved result has a pointer and checksum.

### Phase 5: Enforce maintainability

- Require a module owner and lifecycle label for new Python files.
- Reject new numbered copies such as `_v10.py` unless they are explicitly archived snapshots.
- Require a library test for new domain behavior and a CLI smoke test for new commands.
- Run import-cycle, formatting, typing, and package-boundary checks in CI.

## Compatibility and provenance policy

- Preserve old import paths temporarily with deprecation wrappers.
- Never mutate archived scripts to make them use the new implementation; that would change historical provenance.
- Store the canonical replacement and archive location in the inventory.
- Record artifact hashes and the migration commit when moving a script.
- Keep failed calls, technical interruptions, raw outputs, and excluded records untouched.
- Treat a changed numerical result, artifact schema, or evidence boundary as a versioned behavior requiring review.

## Success measures

Track these measures after each phase:

- number of active entry points
- number of duplicated implementations by concept
- default test count and runtime
- import graph depth and cycle count
- percentage of Python files classified
- percentage of active commands using the canonical package
- ability to regenerate a retained report from a clean checkout
- number of historical artifacts with indexed provenance

The cleanup is complete when a new agent can find the active commands from the root README, understand the module boundaries from this plan, run the default tests without archived dependencies, and locate every retained historical result through the archive index.

## First implementation slice

Start with one vertical slice rather than a repository-wide move:

1. inventory the current confirmation runner, B2/B4 implementations, manifest validation, execution accounting, and scoring scripts;
2. extract their shared schemas and artifact helpers;
3. create one canonical `run_confirmation` command;
4. run it against a retained fixture and compare outputs;
5. archive only the superseded wrappers after the comparison passes.

This slice exercises the most important boundaries and provides a template for migrating the older diagnostic and qualification families.

## Versioning policy

Do not create a new top-level `_vN.py` file for ordinary iteration. Keep the stable module or command name and record behavior changes in Git, a changelog entry, or a manifest revision. A versioned filename is allowed only when an immutable historical implementation is required for a retained result; it should be removed from the working tree when no active caller depends on it.

For nested experiment families such as RoboBoat, diagnostic land, and qualification runs, use a stable command name plus an explicit input manifest or output namespace (for example, `export_roboboat_prospective_evidence.py` with a manifest-selected cohort). Do not encode every pilot revision in the Python filename.
