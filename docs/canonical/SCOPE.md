# Scope — Independence-Release Bootstrap Scope (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_SCOPE
status: canonical
primary_architecture: independence_release
bootstrap_ticket: 2026-03-23__P0__bootstrap_independence_release_repo_cleanup-2
```

## Fachliche Grundlage
The fachliche Grundlage for the Independence-Release target architecture are the **7 Abschnittsdateien** together with the authoritative Independence-Release Gesamtkonzept referenced by the bootstrap ticket. Legacy repository documentation is not binding for the target architecture when it conflicts with those authority sources.

## Legacy authority rule
Documentation under `docs/legacy/` is historical context only. Supporting files under `docs/` that predate this bootstrap may remain for compatibility, but canonical truth for the target architecture lives under `docs/canonical/`.

## Leitprinzipien (bootstrap restatement)
- Independence-Release is the new primary target architecture for this repository.
- Legacy scanner material is retained only as reference and migration input, not as the active design center.
- Canonical documentation must define the structure first; implementation follows in later tickets.
- Reusable technical infrastructure should be preserved where it can support later Independence-Release work.
- Deferred business logic must remain explicitly deferred rather than guessed or silently imported from the legacy scanner.
- Repository structure, storage paths, and documentation paths must be deterministic and visible in version control.

## In scope for this bootstrap
- Canonical documentation skeleton for the Independence-Release architecture.
- Repository-level target directories for reports, snapshots, evaluation, artifacts, and legacy isolation.
- Scanner module skeleton for the target architecture.
- Repository messaging that makes the target/legacy separation explicit.

## Out of scope for this bootstrap
- Implementation of runtime business logic for axes, phase, state, entry, runners, SQLite schema, or execution behavior.
- Re-definition of deferred thresholds, scoring curves, or other unsettled business rules.
- Treating legacy scoring/ranking/decision docs as implied authority for the new architecture.
