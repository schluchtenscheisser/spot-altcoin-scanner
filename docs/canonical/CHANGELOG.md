# Changelog — Independence-Release Canonical Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_CHANGELOG
status: canonical
canonical_track: independence_release
canonical_schema_version: 6.3.0
canonical_schema_versioning: semver
canonical_schema_version_location: docs/canonical/CHANGELOG.md
```

## 2026-03-23 — Independence-Release bootstrap
- Established the Independence-Release repository structure as the primary target path for this repository.
- Added the canonical bootstrap documents required for architecture, runtime, data model, reports, snapshots, testing, migration notes, open questions, and deferred enhancements.
- Reserved target top-level directories and scanner module directories without implementing new business logic.
- Clarified that legacy scanner material remains reference-only inside this repository while the old runtime continues separately.

## 2026-04-22 — Ticket 13 output artifacts contract
- Defined the canonical output artifact layer for Independence-Release with `schema_version = "ir1.0"` for report/diagnostics records.
- Bound output responsibilities to `scanner/output/schema.py`, `scanner/output/diagnostics.py`, and `scanner/output/report_builder.py`.
- Specified canonical run and daily report paths under `reports/` with `daily_bar_id` as the date-partition source.
- Fixed required index artifacts and latest-pointer semantics (`latest.json`, `latest_daily.json`, `latest_paths.json`, `recent_runs.json`).
- Clarified manifest pointer-only semantics and the no-duplication rule for `run.manifest.json`.
