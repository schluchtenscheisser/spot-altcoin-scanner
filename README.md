# Spot Altcoin Scanner — Independence-Release Bootstrap Repo

This repository is now the **bootstrap repository for the Independence-Release architecture**. It preserves reusable technical infrastructure from the older scanner while making the new target structure explicit.

**Canonical documentation (source of truth):** `docs/canonical/INDEX.md`

## Repository status
- **Primary target path:** Independence-Release structure under `docs/canonical/` and the new `scanner/*` module skeleton.
- **Legacy/reference only:** the existing legacy scanner pipeline that remains in this repository for reference and technical reuse.
- **Out of scope in this bootstrap:** implementing the new business logic, SQLite schema, runners, axes, phase/state logic, or automated execution.

## What this bootstrap changes
- Establishes the target directory structure for reports, snapshots, evaluation, artifacts, and legacy isolation.
- Establishes the target `scanner/` module skeleton for future Independence-Release implementation.
- Keeps legacy technical code available instead of destructively deleting it.

## Where to start
- Canonical index: `docs/canonical/INDEX.md`
- Target architecture skeleton: `docs/canonical/ARCHITECTURE.md`
- Runtime model bootstrap: `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- Migration view: `docs/canonical/MIGRATION_NOTES.md`
- Codex workflow: `docs/canonical/WORKFLOW_CODEX.md`

## Legacy note
The old scanner runtime continues separately in the old repository. Inside this repository, legacy modules and documents remain only as migration/reference material until replaced by future Independence-Release implementation tickets.
