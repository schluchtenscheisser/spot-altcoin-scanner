> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# \[P0] Persist Shadow-Live SQLite State Between Runs

## Metadata

* **Ticket ID:** T28-pre (prerequisite to T28 and T\_EL1 Step B)
* **Priority:** P0 — blocks State Machine aging, `late`/`chased` demotion, and all multi-day analysis
* **Depends on:** T22 (Shadow-Live workflow), T27 (diagnostics schema)
* **Authoritative references:**

  * Current `main` after T22/T27
  * `.github/workflows/independence-shadow-live.yml` (existing Shadow-Live workflow)
  * `scripts/run\_independence\_shadow\_live.py` (existing orchestrator)
  * v2.1 Abschnitt 4 (state machine, multi-day state carry-over)
  * `independence\_release\_gesamtkonzept\_final.md`

> If existing implementation and this ticket conflict, the v2.1 specification and the established T22/T27 contracts take precedence. No second artifact model is introduced.

\---

## Context

### The bug

The Shadow-Live workflow currently produces no persistent SQLite state between daily GitHub Actions runs. Every run starts with an empty state database. This has been confirmed empirically across all available Shadow-Live artifacts:

* All `confirmed\_candidates` records across all runs have `bars\_since\_confirmed\_entered == 0`.
* Population 2 (Day-1+ confirmed) is structurally zero across all runs.
* Five symbols confirmed on two consecutive days (COOKIEUSDT, JUPUSDT, PUMPUSDT, TONUSDT, VANAUSDT) show `bars\_since\_confirmed\_entered == 0` on both days with different `close\_at\_confirmed\_entry\_bar` values — proving state was not carried over, not re-entered from the same position.

### Impact

Without state carry-over:

* `bars\_since\_confirmed\_entered` resets to 0 on every run regardless of actual cycle age.
* `freshness\_distance\_state\_confirmed` and `distance\_from\_ideal\_entry\_after\_confirmed` never accumulate meaningful values.
* `late` and `chased` state demotions (Abschnitt 4 §6.4–6.5) never trigger in Shadow-Live.
* All multi-day analysis (T28, T\_EL1 Step B) operates on structurally incorrect state data.

### Root cause

GitHub Actions runners are ephemeral. The SQLite database at `data/independence\_release.sqlite` (and WAL files) is created fresh on each run and discarded when the runner terminates. No mechanism currently exists to restore the previous run's database before the scan starts or to persist the updated database after the scan completes.

### Design decision: GitHub Actions Artifact as state store

The fix uses GitHub Actions Artifacts as the persistence layer. This is consistent with the existing Shadow-Live model (no repo commits, all outputs as artifacts) and requires no external infrastructure.

A dedicated `shadow-live-state` artifact is maintained separately from the run ZIP artifacts. It contains only the checkpointed SQLite database — not reports, diagnostics, or other run outputs.

\---

## Goal

Before each Shadow-Live daily run, restore the SQLite state database from the most recent successful Shadow-Live run's `shadow-live-state` artifact. After the run, checkpoint and upload the updated database as a new `shadow-live-state` artifact.

After this fix, symbols that remain `confirmed\_candidates` across consecutive daily runs must show `bars\_since\_confirmed\_entered >= 1` on the second day.

\---

## Behavioral specification

### Restore phase (before scan)

1. Query the GitHub Actions API for the most recent successful run of `independence-shadow-live.yml` on branch `main` that produced a `shadow-live-state` artifact.
2. If found: download the artifact, extract `independence\_release.sqlite` to `data/independence\_release.sqlite`. Log `state\_restore\_status = restored`.
3. If not found (no prior successful run, or artifact expired): start with an empty database (existing behavior). Log `state\_restore\_status = cold\_start`.
4. If the download or extraction fails for any reason: abort the restore, delete any partial file, proceed with an empty database. Log `state\_restore\_status = restore\_failed`. The run must not abort — `restore\_failed` is a degraded-but-acceptable state equivalent to `cold\_start`.

### Persist phase (after scan)

1. After the daily scan completes successfully, run a WAL checkpoint:

```
   PRAGMA wal\_checkpoint(TRUNCATE);
   ```

   This consolidates any WAL data into the main file and allows uploading a single file.

2. Upload `data/independence\_release.sqlite` as a GitHub Actions artifact named `shadow-live-state`.
3. The persist phase must not run if the scan itself failed. A failed scan must not overwrite a previously valid state artifact.

   ### `state\_restore\_status` field

   `state\_restore\_status` must be logged and included in the run's diagnostic/manifest output so it is visible in artifacts for downstream analysis.

|Value|Meaning|
|-|-|
|`cold\_start`|No prior state artifact found; run started with empty DB|
|`restored`|Prior state artifact found and successfully restored|
|`restore\_failed`|Prior artifact found but download/extraction failed; run started with empty DB|

\---

## Scope

### In scope

1. Modify `.github/workflows/independence-shadow-live.yml` to add restore and persist steps.
2. Modify `scripts/run\_independence\_shadow\_live.py` (or add a helper script) to:

   * Execute the restore phase before invoking the scanner.
   * Execute the WAL checkpoint and persist phase after the scanner completes successfully.
   * Write `state\_restore\_status` to the run manifest or a dedicated status file.
3. The `shadow-live-state` artifact contains exactly one file: `independence\_release.sqlite` at the artifact root (post-checkpoint). It is restored into `data/independence\_release.sqlite` before the scan. WAL and SHM files are excluded.
4. The restore step must verify the downloaded file is a valid SQLite database before placing it at the target path. Minimum check: file exists and is non-empty. If verification fails → `restore\_failed`.
5. Workflow permissions remain `contents: read` unless artifact upload/download via the GitHub API strictly requires `actions: read`. No `contents: write` permission is added. Artifact operations use `GITHUB\_TOKEN` with the minimum required scope.

### Out of scope

* Committing the SQLite database or WAL files to the repository. This is explicitly forbidden.
* Modifying the existing run ZIP artifact structure or the `shadow-live-report.json` schema.
* Changing any scanner logic, scoring, or state machine behavior.
* Handling SQLite schema migrations between runs. If a schema mismatch is detected, treat as `restore\_failed` and start with empty DB.
* Retention policy management for `shadow-live-state` artifacts (GitHub's default retention applies).
* Intraday state persistence (daily state only in this ticket).

\---

## Implementation notes

### Finding the last successful run

Use the GitHub CLI (`gh`) or the GitHub REST API with `GITHUB\_TOKEN`. Example using `gh`:

```bash
LAST\_RUN\_ID=$(gh run list \\
  --workflow independence-shadow-live.yml \\
  --branch main \\
  --status success \\
  --limit 10 \\
  --json databaseId,conclusion \\
  --jq '\[.\[] | select(.conclusion=="success")] | first | .databaseId')
```

**The restore logic must never select the current workflow run.** The current run ID must be explicitly excluded from the candidate list — pass `github.run\_id` into the filter and exclude any match. This guards against re-run scenarios or unusual scheduling timing where the current run could appear as a candidate.

If `LAST\_RUN\_ID` is empty, null, or equal to the current run ID → `cold\_start`.

Then check whether that run produced a `shadow-live-state` artifact before attempting download:

```bash
gh run download "$LAST\_RUN\_ID" \\
  --name shadow-live-state \\
  --dir .state-restore
```

### Download path verification

After download, validate the extracted file before copying. The validation must pass all three checks:

1. File exists and is non-empty.
2. `PRAGMA integrity\_check` returns `ok`.
3. The `state\_machine\_context` table exists (schema presence check).

```bash
RESTORED\_FILE=".state-restore/independence\_release.sqlite"
STATE\_RESTORE\_STATUS="restore\_failed"

if \[ -f "$RESTORED\_FILE" ] \&\& \[ -s "$RESTORED\_FILE" ]; then
  INTEGRITY=$(sqlite3 "$RESTORED\_FILE" "PRAGMA integrity\_check;" 2>/dev/null)
  TABLE=$(sqlite3 "$RESTORED\_FILE" \\
    "SELECT name FROM sqlite\_master WHERE type='table' AND name='state\_machine\_context';" 2>/dev/null)
  if \[ "$INTEGRITY" = "ok" ] \&\& \[ "$TABLE" = "state\_machine\_context" ]; then
    mkdir -p data
    cp "$RESTORED\_FILE" data/independence\_release.sqlite
    STATE\_RESTORE\_STATUS="restored"
  fi
fi
```

If any check fails → `STATE\_RESTORE\_STATUS=restore\_failed`, no copy is performed, scanner starts with empty DB.

### WAL checkpoint

```bash
sqlite3 data/independence\_release.sqlite "PRAGMA wal\_checkpoint(TRUNCATE);"
```

This must run after the scanner exits successfully and before the artifact upload step.

### Artifact upload

Stage the file into a dedicated upload directory before uploading. This ensures the artifact contains exactly `independence\_release.sqlite` at its root — without any `data/` path prefix — and makes the restore download path unambiguous:

```bash
mkdir -p .state-upload
cp data/independence\_release.sqlite .state-upload/independence\_release.sqlite
```

```yaml
- name: Upload shadow-live-state
  if: success()
  uses: actions/upload-artifact@v4
  with:
    name: shadow-live-state
    path: .state-upload/independence\_release.sqlite
    retention-days: 30
```

The downloaded artifact will extract to `.state-restore/independence\_release.sqlite` — matching the path used in the restore verification step.

### `state\_restore\_status` in manifest

Add `state\_restore\_status` to `run.manifest.json` (or equivalent run-level output file) so it is visible in downloaded artifacts without requiring log inspection.

\---

## Acceptance criteria

1. A symbol that is `confirmed\_candidates` in two consecutive daily Shadow-Live runs shows `bars\_since\_confirmed\_entered >= 1` in the second run.
2. `close\_at\_confirmed\_entry\_bar` is not reset between runs for a symbol that remains in the same confirmed cycle.
3. The `shadow-live-state` artifact is produced after each successful daily run and contains exactly `independence\_release.sqlite`.
4. WAL and SHM files are not included in the `shadow-live-state` artifact.
5. The SQLite database is not committed to the repository under any code path introduced by this ticket.
6. If no prior `shadow-live-state` artifact exists, the run completes with `state\_restore\_status = cold\_start` and produces a valid report.
7. If artifact download fails, the run completes with `state\_restore\_status = restore\_failed` and produces a valid report (scanner ran with empty DB).
8. `state\_restore\_status` is present in `run.manifest.json` (or equivalent run-level output).
9. Workflow permissions: `contents: read` is not escalated beyond what artifact operations strictly require. No `contents: write` permission is added.
10. The existing run ZIP artifact structure and `shadow-live-report.json` schema are unchanged.
11. Population 2 (Day-1+ confirmed) in T\_EL1 Step A re-run against new artifacts is non-zero within 2 consecutive runs after this fix is deployed.

