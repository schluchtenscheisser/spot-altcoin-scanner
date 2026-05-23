> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# BACKTEST-CHUNK-1: Chunk-Capable Historical Replay Runner

## Metadata

- Ticket ID: BACKTEST-CHUNK-1
- Title: Chunk-Capable Historical Replay Runner with State Handoff
- Status: Ready for implementation
- Priority: P1
- Language: Implementation and code artifacts in English

---

## Context and motivation

The Historical Signal-Quality Replay (Pre-2) runs the full scanner pipeline
day-by-day over a 382-day evaluation window. A full replay run takes approximately
5–6 hours on available hardware. This exceeds the reliable runtime of a single
Codespace session and the GitHub Actions 6-hour job timeout.

The current runner does not support splitting a replay into time-bounded chunks with
state continuity between chunks. This ticket adds chunk-capable execution.

Chunking is a purely technical concern. The scenario definition (canonical evaluation
window, `scenario_config_hash`) remains unchanged. A chunked replay and a full replay
of the same scenario are semantically identical.

---

## Authoritative references

1. Approved Pre-2 ticket:
   `docs/legacy/tickets/2026-05-18__BACKTEST_PRE_2__historical_daily_replay_harness.md`
2. Approved scenario YAML:
   `configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml`
3. Existing implementation:
   `scanner/evaluation/historical_replay/replay_runner.py`
   `scanner/evaluation/historical_replay/production_adapter.py`
   `scanner/evaluation/historical_replay/state_store.py`
   `scanner/tools/run_historical_daily_replay.py`

---

## Chunk semantics — non-negotiable rules

1. **Scenario-YAML is the canonical full-period contract.** `evaluation.start_date`
   and `evaluation.end_date` remain the canonical window. Chunk parameters do not
   replace them.

2. **Chunk boundaries are technical, not semantic.** State at chunk boundary must be
   fully preserved — no resets, no re-initializations.

3. **`scenario_config_hash` does not change for chunks.** Chunk parameters are not
   scenario-defining fields and must not affect the hash.

4. **All chunks share the same `replay_id`.** The `replay_id` is generated once (at
   first chunk or provided externally) and reused for all subsequent chunks. All chunk
   outputs land under one canonical run directory.

5. **`replay_id` must be externally providable** via `--replay-id` CLI parameter.

6. **Chunk boundaries must fall within the scenario evaluation window.**

7. **Both `--chunk-start` and `--chunk-end` are required if either is provided.**
   Providing only one is a hard error.

8. **The first chunk must start exactly at `scenario.evaluation.start_date`.** If
   `--chunk-start > scenario.evaluation.start_date`, a `--resume-from-state` path
   must be provided. A mid-period chunk without prior state is a hard error.

9. **If `replay_manifest.json` exists with `chunks_completed` non-empty, then
   `chunk_start` must equal `last_chunk_end_date + 1 day`.** No gaps between chunks
   are permitted. Fail fast if a gap is detected.

10. **If `chunk_id` already exists in `chunks_completed`, fail fast.** No silent
    overwrites of completed chunks.

11. **Existing full-window behavior (no chunk parameters) is preserved exactly.**
    No behavioral regression. Full-window runs continue to write outputs at the run
    root as before.

---

## New CLI parameters

Extend `scanner/tools/run_historical_daily_replay.py`:

```
--chunk-start YYYY-MM-DD
    Start date for this chunk (inclusive).
    Must equal scenario.evaluation.start_date for first chunk.
    Requires --chunk-end.

--chunk-end YYYY-MM-DD
    End date for this chunk (inclusive).
    Must be <= scenario.evaluation.end_date.
    Requires --chunk-start.

--resume-from-state PATH
    Path to state_final.sqlite from prior chunk.
    Required if --chunk-start > scenario.evaluation.start_date.
    Source file must not be modified.

--replay-id REPLAY_ID
    Externally provided replay ID (format: YYYY-MM-DDTHH:MM:SSZ).
    If provided, used instead of generating a new ID.
    If run directory exists for this replay_id, scenario_id and scenario_config_hash
    must match. If chunk_id already appears in chunks_completed, fail fast.

--chunk-id CHUNK_ID
    Optional human-readable chunk label.
    If omitted, derived as "YYYY-MM-DD_to_YYYY-MM-DD" from chunk_start and chunk_end.
    A monthly GitHub Actions workflow may pass an explicit "YYYY-MM" label.
```

---

## Output structure

### Full-window mode (no chunk parameters) — unchanged

```
evaluation/replay/runs/<scenario_id>/<replay_id>/
  replay_manifest.json
  replay_symbol_diagnostics.jsonl.gz
  replay_event_candidates.parquet
  state.sqlite
```

No changes to this structure. Full-window runs must not write under `chunks/`.

### Chunk mode

```
evaluation/replay/runs/<scenario_id>/<replay_id>/
  replay_manifest.json              (updated atomically after each chunk)
  state_latest.sqlite               (physical copy of most recent chunk final state)
  chunks/
    <chunk_id>/
      chunk_manifest.json           (written atomically at chunk completion)
      state_working.sqlite          (written during chunk execution)
      state_final.sqlite            (copy of state_working.sqlite on success only)
      replay_symbol_diagnostics.jsonl.gz
      replay_event_candidates.parquet
```

Merged run-level `replay_symbol_diagnostics.jsonl.gz` and
`replay_event_candidates.parquet` are **out of scope** for BACKTEST-CHUNK-1.
Backtest-1 or a later merge ticket will combine chunk files.

### Chunk mode — diagnostics and events are chunk-local only

In chunk mode, diagnostics and events must not accumulate prior chunks in memory.
The runner collects only the current chunk's diagnostics and events, then writes:

```
chunks/<chunk_id>/replay_symbol_diagnostics.jsonl.gz
chunks/<chunk_id>/replay_event_candidates.parquet
```

Run-level cumulative counters (`signal_events_so_far`, `diagnostics_so_far`) are
read from the existing `replay_manifest.json` at chunk start and incremented by the
current chunk's counts. They are not recomputed from scratch.

### Full-window mode — state.sqlite

Full-window mode continues to use `run_dir/state.sqlite` directly, as before.
Chunk mode must not use `run_dir/state.sqlite`. These two paths must never overlap.

---

### Chunk start

If `--resume-from-state` is provided:
1. Verify source file exists. Fail fast if not.
2. Verify it is a valid SQLite file that sqlite3 can open. Fail fast if not.
3. Verify it is a ReplayStateStore-compatible database: required tables must exist
   and a schema/version sanity check must pass if available. Fail fast with:
   `resume_from_state is not a valid replay state store: <path>`
4. Copy source to `chunks/<chunk_id>/state_working.sqlite`.
5. Do not modify the source file.
6. Log: `INFO: Resuming from state: <path>`

If first chunk (no `--resume-from-state`):
1. Initialize empty `state_working.sqlite` in `chunks/<chunk_id>/`.
2. Log: `INFO: Starting fresh replay state for chunk <chunk_id>`

### During chunk execution

The runner reads and writes only `chunks/<chunk_id>/state_working.sqlite`.
It must not read from or write to `state_latest.sqlite` or any prior chunk's files
during execution.

### Chunk completion (success only)

1. Copy `chunks/<chunk_id>/state_working.sqlite`
   to `chunks/<chunk_id>/state_final.sqlite`.
2. Copy `chunks/<chunk_id>/state_final.sqlite`
   to `run_dir/state_latest.sqlite` (physical copy, not symlink).
3. Write `chunks/<chunk_id>/chunk_manifest.json` atomically.
4. Update `run_dir/replay_manifest.json` atomically.
5. Log: `INFO: Chunk <chunk_id> complete. State written to <path>`

### On failure

Do not update `state_latest.sqlite`. Do not write `state_final.sqlite`.
Leave `state_working.sqlite` in place for debugging. Log the failure clearly.

---

## Atomic manifest writes

Both `replay_manifest.json` and `chunk_manifest.json` must be written atomically:

```python
tmp = manifest_path.with_name(manifest_path.name + ".tmp")
tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
tmp.replace(manifest_path)  # atomic swap; overwrites existing target
```

Use `Path.replace()`, not `Path.rename()` — `replace` overwrites an existing target
atomically. Never leave a partially written manifest on failure.

---

## Warm-up summary accumulation across chunks

At chunk start, if `run_dir/replay_manifest.json` exists and contains
`warmup_summary_by_symbol`, load and merge it into the current chunk accumulator:

```
For each symbol in prior warmup_summary:
  warmup_days_skipped = prior.warmup_days_skipped + current.warmup_days_skipped
  first_evaluable_date = prior.first_evaluable_date if present else current
```

The merged summary is written to `replay_manifest.json` after the chunk completes.

---

## replay_manifest.json — chunk mode fields

After each chunk, update `replay_manifest.json` with:

```json
{
  "scenario_id": "...",
  "replay_id": "...",
  "evaluation_start_date": "2025-05-01",
  "evaluation_end_date": "2026-05-17",
  "replay_days_total": 382,
  "replay_days_completed": 62,
  "chunks_completed": ["2025-05", "2025-06"],
  "chunks_total": null,
  "last_chunk_end_date": "2025-06-30",
  "is_complete": false,
  "signal_events_so_far": 0,
  "diagnostics_so_far": 0,
  "warmup_summary_by_symbol": {}
}
```

`chunks_total` is `null` unless the caller provides it — the runner does not compute
a monthly chunk plan. `is_complete` is `true` only when
`last_chunk_end_date == scenario.evaluation.end_date`.

`replay_days_completed` is the cumulative count of days completed across all chunks,
not the full scenario day count.

---

## chunk_manifest.json

```json
{
  "scenario_id": "...",
  "replay_id": "...",
  "chunk_id": "2025-05",
  "chunk_start_date": "2025-05-01",
  "chunk_end_date": "2025-05-31",
  "days_in_chunk": 31,
  "days_completed": 31,
  "signal_events_in_chunk": 0,
  "diagnostics_in_chunk": 0,
  "resumed_from_state": "path/to/prior/state_final.sqlite or null",
  "state_working_path": "...",
  "state_final_path": "...",
  "created_at_utc": "..."
}
```

---

## Validation rules — fail fast before execution

| Condition | Error |
|---|---|
| `--chunk-start` provided without `--chunk-end` (or vice versa) | `Both --chunk-start and --chunk-end are required` |
| `chunk_start < scenario.evaluation.start_date` | `chunk_start is before scenario evaluation start` |
| `chunk_end > scenario.evaluation.end_date` | `chunk_end is after scenario evaluation end` |
| `chunk_start > chunk_end` | `chunk_start is after chunk_end` |
| `chunk_start > scenario.evaluation.start_date` and no `--resume-from-state` | `resume_from_state is required when chunk_start > scenario evaluation start` |
| `--resume-from-state` provided but file not found | `resume_from_state file not found: <path>` |
| `--replay-id` exists but `scenario_id` or `scenario_config_hash` mismatches | `replay_id conflict: scenario mismatch` |
| `chunk_id` already in `chunks_completed` | `chunk_id already completed: <chunk_id>` |
| `chunks_completed` non-empty and `chunk_start != last_chunk_end_date + 1 day` | `chunk gap detected: expected chunk_start <date>` |

---

## Internal `run_replay` function signature

```python
def run_replay(
    scenario: ReplayScenario,
    output_root: Path,
    chunk_start: date | None = None,
    chunk_end: date | None = None,
    resume_from_state: Path | None = None,
    replay_id: str | None = None,
    chunk_id: str | None = None,
) -> dict:
```

When `chunk_start` and `chunk_end` are `None`: existing full-window behavior, no
structural changes.

When chunk parameters are provided: day loop iterates only over `[chunk_start,
chunk_end]`. All other replay semantics (warm-up eligibility, state aging, event
emission, bucket mapping) are unchanged.

---

## Do not change

- `scenario.py` and `scenario_registry.py`
- `bar_loader.py`
- `production_adapter.py`
- Pre-1 fetch logic
- Scenario-YAML format and `scenario_config_hash` computation
- `historical_signal_bucket` mapping
- Execution-disabled semantics
- Existing full-window output structure

---

## Tests

Add `tests/replay/test_chunk_capable_runner.py`.

Required test cases:

1. **First chunk, no resume**: `chunk_start == scenario.evaluation.start_date`, no
   `--resume-from-state`. Runner initializes empty state, processes only chunk days,
   writes `chunk_manifest.json` and `state_final.sqlite`.

2. **Mid-period chunk with resume**: `chunk_start > scenario.evaluation.start_date`,
   `--resume-from-state` provided. Prior state loaded, `bars_since_*` fields not
   reset, processing continues from correct day.

3. **Mid-period chunk without resume**: Fails fast before execution.

4. **Only `--chunk-start` without `--chunk-end`**: Fails fast.

5. **`chunk_start` before scenario start**: Fails fast.

6. **`chunk_end` after scenario end**: Fails fast.

7. **`--replay-id` reuse — scenario match**: Two chunks with same `replay_id` write
   under same run directory. `chunks_completed` grows correctly.

8. **`--replay-id` reuse — scenario mismatch**: Fails fast with clear error.

9. **`chunk_id` already completed**: Fails fast.

10. **Chunk gap detected**: If `chunks_completed = ["2025-05"]` and new
    `chunk_start = 2025-07-01`, fails fast with gap error.

11. **State output**: After chunk completes, `state_working.sqlite`,
    `state_final.sqlite`, and `state_latest.sqlite` all exist. Source
    `--resume-from-state` file is unmodified.

12. **Atomic manifest write**: `chunk_manifest.json` and `replay_manifest.json` are
    never partially written (simulate failure mid-write and verify no corrupt file).

13. **Warm-up summary merge**: Second chunk loads prior `warmup_summary_by_symbol`
    and merges correctly. `warmup_days_skipped` accumulates.

14. **`replay_days_completed` is cumulative**: After two chunks of 31 days each,
    `replay_days_completed == 62`, not 382.

15. **Full-window fallback**: No chunk parameters → existing output structure
    unchanged, no `chunks/` directory created.

Use synthetic fixture data. Do not require real Pre-1 Parquet data or network access.

---

## Acceptance criteria

- AC1: Both `--chunk-start` and `--chunk-end` are required when either is provided.
- AC2: All validation rules produce clear errors before any execution begins.
- AC3: `--resume-from-state` loads prior state without modifying the source file.
- AC4: State is written only to `chunks/<chunk_id>/state_working.sqlite` during execution.
- AC5: On success: `state_final.sqlite` and `state_latest.sqlite` are physical copies.
- AC6: On failure: `state_latest.sqlite` is not updated.
- AC7: `replay_manifest.json` and `chunk_manifest.json` are written atomically.
- AC8: `replay_days_completed` is cumulative across completed chunks.
- AC9: `chunks_total` is `null` in runner output (no monthly plan computation).
- AC10: `is_complete = true` only when `last_chunk_end_date == scenario.evaluation.end_date`.
- AC11: Warm-up summary is merged from prior manifest across chunks.
- AC12: Chunk gap validation fails fast before execution.
- AC13: Full-window behavior (no chunk parameters) is unchanged — no `chunks/` directory.
- AC14: All 15 test cases pass.
- AC15: No regression in existing replay tests.

---

## Definition of Done

- All acceptance criteria met.
- All existing replay tests pass without modification.
- New test file `tests/replay/test_chunk_capable_runner.py` with all 15 cases.
- Merged run-level outputs explicitly documented as out of scope.
- Codex report includes: files changed, test results, example CLI invocations for
  a 2-chunk sequential run with state handoff.
