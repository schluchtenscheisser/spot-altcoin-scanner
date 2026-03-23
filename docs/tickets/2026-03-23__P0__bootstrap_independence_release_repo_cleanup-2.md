# Title
[P0] Bootstrap Independence-Release repo structure and isolate legacy architecture

## Context / Source
The repository has been duplicated to serve as the new **Independence-Release** development repo.

This ticket is the required bootstrap/cleanup step before implementing the new architecture. The goal is **not** to continue the old scanner architecture in-place, but to:

- establish the new target repository structure,
- isolate legacy material as non-primary,
- create the canonical documentation skeleton for the new architecture,
- preserve reusable technical infrastructure,
- avoid destructive cleanup that would remove useful reference or utility code too early.

This ticket is based on the agreed Independence-Release implementation concept and the repo-specific operating model defined during planning.

**Gesamtkonzept reference:** This ticket corresponds to Gesamtkonzept §19, Ticket 2 ("canonical docs bootstrap + path conventions").

`depends_on: []`

## Goal
After this ticket is completed, the repository must clearly reflect that:

1. **Independence-Release** is the new primary architecture target.
2. The old architecture is retained only as legacy/reference material.
3. The new canonical documentation structure exists with the complete set of files defined in Gesamtkonzept §4.1.
4. The new target runtime/output/storage directory structure exists.
5. Reusable technical code remains available.
6. Clearly obsolete or legacy-only documentation/test artifacts are isolated from the new primary path.

## Scope
Allowed changes for this ticket:

- `docs/canonical/**`
- `docs/tickets/**` only as required by `WORKFLOW_CODEX.md`
- `docs/legacy/**`
- `docs/AGENTS.md` if needed
- top-level repo structure for:
  - `reports/**`
  - `snapshots/**`
  - `evaluation/**`
  - `artifacts/**`
  - `legacy/**`
- `scanner/**` only for directory/bootstrap structure and entrypoint preparation
- `README*` if needed to clarify repo primary architecture
- `.github/workflows/**` only if minimal path/bootstrap adjustments are required
- placeholder files such as `.gitkeep` where needed

## Out of Scope
- Implementing business logic of the new Independence-Release pipeline
- Removing reusable technical infrastructure from the repo
- Rewriting clients, utilities, liquidity logic, or existing scripts
- Implementing `bar_clock.py`, SQLite persistence, axes, phase logic, state logic, pattern logic, or runners
- Deleting large parts of `scanner/pipeline/**` just because they are legacy
- Renaming the entire repo or changing package metadata unless strictly required
- Modifying auto-generated files manually:
  - `docs/code_map.md`
  - `docs/GPT_SNAPSHOT.md`
- Populating canonical docs with fake implementation detail for logic that is intentionally deferred to later tickets

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`
- Gesamtkonzept §2.1 (Repo-Zielarchitektur), §4.1 (Dokumentationsarchitektur), §5 (Verzeichnisrollen)

For this ticket, Codex must create or update the following canonical docs as part of the bootstrap (complete set per Gesamtkonzept §4.1):
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/REPORTS.md`
- `docs/canonical/SNAPSHOTS.md`
- `docs/canonical/TEST_STRATEGY.md`
- `docs/canonical/SCOPE.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/MIGRATION_NOTES.md`
- `docs/canonical/open_questions.md`
- `docs/canonical/feature_enhancements.md`

## Proposed change (high-level)

### Before
- The repo is a duplicated copy of the old scanner repo.
- Legacy architecture is still structurally dominant.
- The new Independence-Release target paths are not yet clearly established.
- Canonical documentation for the new architecture is incomplete or missing.
- Legacy and target architecture are not yet clearly separated.

### After
- The repo exposes the new Independence-Release target structure.
- Legacy material is isolated as legacy/reference, not primary.
- Canonical docs for the new architecture exist with the complete file set from Gesamtkonzept §4.1 and describe the target layout at bootstrap level.
- Output/storage/evaluation/artifact directories exist in their target structure.
- `scanner/` exposes the new module skeleton for the future Independence-Release architecture.
- Reusable technical code remains available for later implementation tickets.

### Edge cases
- Existing legacy technical files that are still useful must **not** be deleted just because they belong to the old implementation path.
- Legacy business docs/tests must be clearly isolated, not silently mixed into the new canonical path.
- Missing canonical files required by the new architecture must be created in this ticket rather than deferred.
- If a directory would otherwise be empty, create a placeholder (for example `.gitkeep`) so the target structure is visible and commit-stable.

### Backward compatibility impact
This is a bootstrap/structure ticket for the new repo. Runtime backward compatibility with the old scanner is not required inside this repo, because the old scanner continues in the old repository.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> This section is an execution instruction for Codex. Do not guess. If something is unclear, follow these rules exactly.

- **Workflow priority:** Follow `docs/canonical/WORKFLOW_CODEX.md` for ticket lifecycle (`docs/tickets/` → `_in_progress/` → `docs/legacy/tickets/`) and for the "docs first" rule.
- **Conflict handling for this ticket:** If current repo documentation outside `docs/canonical/WORKFLOW_CODEX.md` still reflects the old architecture and conflicts with this ticket, treat that as **documentation drift**, not as a blocker. Update canonical docs first in the same PR to remove the drift.
- **Authority hierarchy:** The 7 v2.1 Abschnittsdateien and the `independence_release_gesamtkonzept_final.md` are the authoritative source for the target architecture. Any older content in `docs/canonical/` or elsewhere in the repo that conflicts with these documents is superseded. When creating or updating canonical docs in this ticket, derive content from the Gesamtkonzept and Abschnittsdateien, not from pre-existing repo documentation.
- **Do not treat stale legacy docs as authority.** Legacy docs may be moved or left in `docs/legacy/**`, but they must not remain the implied primary architecture.
- **Do not manually edit auto-docs:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are read-only supporting artifacts.
- **Non-destructive cleanup:** Do not delete reusable technical files unless they are clearly obsolete and legacy-only. Prefer isolation/marking over destructive deletion.
- **No silent architecture mixing:** Do not present old `scanner/pipeline/**` as the active target path. It may remain in place as reference, but the repo must clearly expose the new target structure.
- **No business-logic implementation drift:** This ticket is for bootstrap/cleanup only. Do not start implementing `bar_clock`, SQLite schema, axes, phase logic, or runners here.
- **Determinism:** Directory and file creation must be explicit and stable. If placeholder files are needed, use a consistent convention (`.gitkeep`).
- **Ticket workflow constraint:** Even though this ticket itself creates/updates canonical docs, Codex must still archive the ticket in the same PR per `WORKFLOW_CODEX.md`.
- **Canonical doc content rule:** Do not invent implementation detail, thresholds, or business rules for deferred logic. Each doc must contain only what is specified below under "Required canonical documentation bootstrap" and nothing more.

> If the current authoritative reference, Canonical, and existing code conflict, the authoritative reference wins. If additional clarification is needed, extend the ticket or ask the user rather than interpret.

> Existing repo paths/helpers may be reused as long as they do not conflict with Canonical; do not introduce a second source of truth.

## Implementation Notes

### Required target directories to create

#### Repository-level runtime/storage/output structure
Create these directories if missing:

```text
reports/index/
reports/daily/
reports/runs/
reports/aux/
snapshots/history/
snapshots/runs/
evaluation/exports/
evaluation/replay/
evaluation/calibration/
artifacts/
legacy/
```

#### Scanner target module skeleton
Create these directories if missing:

```text
scanner/universe/
scanner/data/
scanner/features/
scanner/axes/
scanner/phase/
scanner/state/
scanner/entry/
scanner/execution/
scanner/decision/
scanner/storage/
scanner/output/
scanner/runners/
scanner/evaluation/
```

Use `.gitkeep` placeholders where necessary so the structure is committed.

### Required canonical documentation bootstrap

Create/update these files so they exist and are clearly framed as the new target architecture skeleton. Each file has **mandatory minimum content** specified below. Do not add speculative detail beyond what is specified.

#### `docs/canonical/ARCHITECTURE.md`
Mandatory minimum content:
- Reproduce the module structure from Gesamtkonzept §2.1 (the `scanner/` directory tree)
- Reproduce the module responsibilities from Gesamtkonzept §2.2 (one paragraph per module)
- A header statement that Independence-Release is the primary target architecture and that the old scanner runs separately in the old repo

#### `docs/canonical/SCOPE.md`
Mandatory minimum content:
- State that the fachliche Grundlage are the 7 Abschnittsdateien
- State that legacy documentation is not binding for the target architecture
- Reproduce the Leitprinzipien from Gesamtkonzept §1

#### `docs/canonical/GLOSSARY.md`
Mandatory minimum content — define at minimum these terms:
- `daily_bar_id`
- `intraday_bar_id`
- `setup_cycle_id`
- `market_phase`
- `state_machine_state`
- `decision_bucket`
- `structural_break`
- `bars_since_*` (canonical 4h-bar unit)
- `daily_discovery_scan`
- `intraday_promotion_scan`

Definitions must match the 7 Abschnittsdateien. Where a term does not yet have a single strict definition in the authoritative Abschnittsdateien, the glossary entry must be a reference to the authoritative source section (e.g., "See Abschnitt 4, §5.3"), not a freely paraphrased definition. Terms without a settled definition in the spec must not be speculatively defined.

#### `docs/canonical/DATA_MODEL.md`
Mandatory minimum content:
- Placeholder skeleton with sections for: Persistence (SQLite), History (Parquet), Field Groups (A/B/C/D from Abschnitt 6 §4)
- No fake column definitions or business schemas

#### `docs/canonical/RUNTIME_AND_OPERATIONS.md`
Mandatory minimum content:
- Reproduce the Betriebsmodell from Gesamtkonzept §10 (Daily Discovery Scan steps 1–14, Intraday Promotion Scan steps 1–7)
- State that SQLite is the persistence foundation

#### `docs/canonical/REPORTS.md`
Mandatory minimum content:
- Reproduce the Reports-Architektur from Gesamtkonzept §7 (directory structure, verbindliche Dateitypen)

#### `docs/canonical/SNAPSHOTS.md`
Mandatory minimum content:
- Reproduce the Snapshot-Klassen (A/B/C/D) from Gesamtkonzept §6
- Reproduce the Parquet-Partitionierung from Festlegung 1

#### `docs/canonical/TEST_STRATEGY.md`
Mandatory minimum content:
- Reproduce the Golden-Strategie from Gesamtkonzept §16 (Typ 1–4)
- Reproduce the Validierungsstrategie from Gesamtkonzept §17

#### `docs/canonical/CHANGELOG.md`
Mandatory minimum content:
- Initial entry for the Independence-Release bootstrap

#### `docs/canonical/MIGRATION_NOTES.md`
Mandatory minimum content:
- Reproduce the classification from Gesamtkonzept §3 (directly reusable / structural template only / not carried forward)

#### `docs/canonical/open_questions.md`
Mandatory minimum content:
- Reproduce the open questions from Gesamtkonzept §21 with their resolution-before-ticket references

#### `docs/canonical/feature_enhancements.md`
Mandatory minimum content:
- Empty list with a header explaining purpose (per Gesamtkonzept §1: "bewusst verschobene Themen")

### Legacy isolation rules
Codex must apply the following cleanup/isolation policy:

#### Move or isolate as legacy/reference
- `docs/legacy/**` remains legacy
- Any file under `docs/` (excluding `docs/canonical/`, `docs/tickets/`, `docs/code_map.md`, `docs/GPT_SNAPSHOT.md`, `docs/AGENTS.md`) that describes concepts from the old scoring, ranking, or decision architecture. These are legacy business docs and must not remain in a path that could be mistaken for primary canonical documentation.

#### Keep in place for now
- `scanner/clients/**`
- `scanner/utils/**`
- `scripts/**`
- `.github/workflows/**`
- technical fetch/mapping/helper code
- technical liquidity-related code
- legacy pipeline code that is still useful as reference

#### Do not present as primary
- old scoring pipeline
- old global ranking / decision architecture
- old output architecture as canonical target

### Entry-point preparation
If needed, adjust the main entrypoint or repo-level documentation so that the new repo clearly indicates:
- Independence-Release is the target path
- old pipeline remains reference/legacy
- future implementation will land under the new module structure

This must be done without prematurely implementing the new runtime behavior.

## Acceptance Criteria (deterministic)

1) The repository contains all required new top-level target directories:
   - `reports/index/`
   - `reports/daily/`
   - `reports/runs/`
   - `reports/aux/`
   - `snapshots/history/`
   - `snapshots/runs/`
   - `evaluation/exports/`
   - `evaluation/replay/`
   - `evaluation/calibration/`
   - `artifacts/`
   - `legacy/`

2) The repository contains all required new scanner target module directories:
   - `scanner/universe/`
   - `scanner/data/`
   - `scanner/features/`
   - `scanner/axes/`
   - `scanner/phase/`
   - `scanner/state/`
   - `scanner/entry/`
   - `scanner/execution/`
   - `scanner/decision/`
   - `scanner/storage/`
   - `scanner/output/`
   - `scanner/runners/`
   - `scanner/evaluation/`

3) All 12 canonical docs listed in this ticket exist after the PR. Each file contains at least the mandatory minimum content specified in the "Required canonical documentation bootstrap" section. No file is empty or contains only a title.

4) `docs/canonical/ARCHITECTURE.md` reproduces the module structure from Gesamtkonzept §2.1 and the module responsibilities from Gesamtkonzept §2.2. It identifies Independence-Release as the primary target architecture.

5) `docs/canonical/GLOSSARY.md` contains definitions for at least the 10 terms listed in this ticket. Definitions are consistent with the 7 Abschnittsdateien.

6) `docs/legacy/**` remains clearly non-primary. Legacy business/architecture documentation that describes old scoring, ranking, or decision concepts is not left under `docs/` in a path that could be mistaken for canonical.

7) Reusable technical infrastructure is retained:
   - clients are not deleted,
   - utilities are not deleted,
   - scripts are not deleted,
   - technical helper code is not deleted solely because it belongs to the old repo shape.

8) The ticket does **not** implement new business logic for the Independence-Release pipeline:
   - no `bar_clock` implementation,
   - no SQLite schema implementation,
   - no axes implementation,
   - no phase/state/pattern/runner implementation.

9) The PR updates canonical docs first and archives the ticket in the same PR according to `docs/canonical/WORKFLOW_CODEX.md`.

10) `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually modified.

11) If placeholder files are used to preserve empty directories, `.gitkeep` is used consistently and only where needed.

12) The repo clearly communicates, either through canonical docs or entrypoint-adjacent documentation, that the duplicated repository is now the Independence-Release bootstrap repo and that the old scanner continues separately.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ (N/A – this ticket does not implement config-reading logic)
- **Config Invalid Value Handling:** ✅ (N/A – this ticket does not implement config validation logic)
- **Nullability / kein bool()-Coercion:** ✅ (N/A – this ticket does not define runtime output fields)
- **Not-evaluated vs failed getrennt:** ✅ (N/A – this ticket does not implement evaluation logic)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write mode is introduced here)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (AC: #11 ; deterministic `.gitkeep` placeholders only)
- **Deterministische Sortierung/Tie-breaker:** ✅ (N/A – no sorting logic introduced in this ticket)

## Tests (required if logic changes)

### Unit
- No new business-logic unit tests are required. This ticket performs only deterministic repo/documentation bootstrap.

### Integration
- If the repo already has a suitable pattern for asserting required paths or documentation presence, add a lightweight validation step. Otherwise, document verification in the PR body explicitly.

### Golden fixture / verification
- Not required. This ticket introduces no scoring, threshold, or curve behavior.

## Constraints / Invariants (must not change)

- [ ] `docs/canonical/WORKFLOW_CODEX.md` remains the governing Codex workflow document
- [ ] `docs/code_map.md` remains read-only
- [ ] `docs/GPT_SNAPSHOT.md` remains read-only
- [ ] Legacy docs do not regain implied authority over canonical docs
- [ ] No Independence-Release business logic is implemented in this ticket
- [ ] Reusable technical infrastructure is preserved
- [ ] Ticket is archived in the same PR per workflow
- [ ] Canonical doc content does not invent implementation detail for deferred logic

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Required bootstrap structure implemented per Acceptance Criteria
- [ ] All 12 canonical docs created/updated with mandatory minimum content
- [ ] No manual edits to read-only auto-docs
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata (optional)
```yaml
created_utc: "2026-03-23T00:00:00Z"
priority: P0
type: refactor
owner: codex
depends_on: []
gesamtkonzept_ref: "§19 Ticket 2"
related_issues: []
```
