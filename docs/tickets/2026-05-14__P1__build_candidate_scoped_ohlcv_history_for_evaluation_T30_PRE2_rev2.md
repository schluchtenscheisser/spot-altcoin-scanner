# Build Candidate-Scoped 1d OHLCV History for T30 Evaluation

**Ticket ID:** T30_PRE2_CANDIDATE_SCOPED_OHLCV_HISTORY  
**Priority:** P1  
**Status:** Draft for implementation  
**Date:** 2026-05-14  
**Target schema:** no diagnostics schema bump expected  
**Expected PR size:** Medium, one PR only  
**Primary owner:** Codex implementation  
**Review focus:** OHLCV history fetch contract, T18 compatibility, artifact-only storage, symbol-scope correctness, idempotent Parquet writing, no repo persistence of market data

---

## 1. Authoritative context

This ticket is the second precondition for T30 Forward-Return Evaluation.

T18 already implemented the replay and forward-return machinery:

- `scanner/evaluation/replay.py`
- `scanner/evaluation/forward_returns.py`
- `scanner/evaluation/dataset_export.py`

T30 will later execute that machinery on accumulated Shadow-Live signal events. Current repo reality blocks T30 because `scanner/evaluation/forward_returns.py` expects daily OHLCV history under:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/*.parquet
```

but this history is not currently present in the repo or SQLite state.

T30-Pre-1 addresses report persistence integrity and replay manifest availability. This ticket addresses only the OHLCV history input needed by T18 forward-return metrics.

Authoritative references for this ticket:

1. The 7 v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `docs/canonical/SNAPSHOTS.md`.
4. `docs/canonical/REPORTS.md`.
5. `docs/AI_CONTEXT_CURRENT.md`.
6. Existing T18 implementation in:
   - `scanner/evaluation/replay.py`
   - `scanner/evaluation/forward_returns.py`
   - `scanner/evaluation/dataset_export.py`
7. Existing MEXC market-data client:
   - `scanner/clients/mexc_client.py`
8. T30-Pre-1 persistence decision:
   - small reports/index/manifests may be committed,
   - large data files remain artifact-only.

If the current authoritative reference set, repo canonical documents, and existing code collide, the v2.1 reference set plus this ticket's explicit requirements win. Existing repo documents remain valid only where they do not conflict with this ticket.

---

## 2. Architectural decision for this ticket

### 2.1 Commit strategy

OHLCV history must **not** be committed to the repository.

This ticket must create an artifact-only OHLCV history build step:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/*.parquet
```

The generated Parquet files are local run outputs and future CI artifacts. They are not repo-persisted.

### 2.2 Symbol scope

The symbol population for T30 v1 OHLCV history is:

```text
all symbols that appeared in confirmed_candidates or early_candidates
within the selected evaluation window
```

Do **not** restrict the symbol population to:

```text
is_operational_trade_candidate == true
```

Reason: T30 must compare operational candidates against important non-operational comparison groups, including:

- confirmed/early but reduced-size only,
- confirmed/early but below-min liquidity,
- confirmed/early but later chased,
- structurally strong but not operationally tradeable symbols.

This preserves INJ/LAB/UB-style analysis instead of filtering it away.

### 2.3 Historical window

Default evaluation/backfill start date:

```text
2026-05-03
```

This covers the accumulated Shadow-Live period including pre-`ir1.5` runs.

T30 later separates:

```text
Primary cohort: ir1.5+
Exploratory historical cohort: 2026-05-03 through ir1.4, with explicit schema compatibility handling
```

This ticket only fetches OHLCV history. It does not implement the final T30 cohort analysis.

### 2.4 Execution placement

This ticket must implement a **separate pre-T30 script**, not embed downloading inside the T30 evaluation run.

Required script:

```text
scripts/fetch_ohlcv_history_for_evaluation.py
```

Reason:

- T30 becomes more idempotent.
- T30 can skip the download step if an OHLCV history artifact is already present.
- The fetched OHLCV dataset can be inspected independently.
- API failures are isolated from metric calculation.

---

## 3. Problem statement

T18 forward-return calculation already supports daily OHLCV Parquet files. It loads per-symbol history from:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=*/month=*/*.parquet
```

and requires at minimum:

```text
daily_bar_id
close
high
low
```

If those files are missing, signal metrics are emitted as `missing_ohlcv_history` rather than real forward returns.

Current Shadow-Live state:

- SQLite state contains no useful OHLCV history for T30.
- The repository currently does not contain `snapshots/history/ohlcv` Parquet history.
- Current report persistence intentionally does not commit Parquet/OHLCV.

Therefore T30 cannot produce real 1d/3d/5d/10d returns until a candidate-scoped 1d OHLCV history is generated.

---

## 4. Scope

### 4.1 In scope

1. Add a standalone script:

```text
scripts/fetch_ohlcv_history_for_evaluation.py
```

2. Extract the evaluation symbol universe from accumulated Shadow-Live outputs.
3. Fetch 1d OHLCV from MEXC for those symbols.
4. Write idempotent Parquet history under:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/part-000.parquet
```

5. Produce machine-readable fetch summary/manifest files.
6. Add tests for symbol extraction, kline normalization, partition writing, idempotency, empty/malformed data handling, and no-commit guardrails.
7. Update `.gitignore` if needed so `snapshots/history/ohlcv/**` is not accidentally committed.
8. Add minimal docs explaining that OHLCV history is artifact-only and must be present before T30 metrics can be computed.

### 4.2 Out of scope

Do not implement any of the following in this ticket:

- Do not implement T30 final Forward-Return Evaluation analysis.
- Do not change T18 event semantics.
- Do not change `scanner/evaluation/forward_returns.py` metric formulas unless a small compatibility fix is strictly necessary and covered by tests.
- Do not change T_EL2 thresholds or action-hint logic.
- Do not change Q1/Q2 operational tradeability logic.
- Do not change candidate bucket semantics.
- Do not commit generated OHLCV Parquet files.
- Do not persist OHLCV history through `scripts/persist_shadow_live_reports.py`.
- Do not add `snapshots/history/**` to report persistence allowlists.
- Do not fetch or store 4h history in this ticket.
- Do not fetch OHLCV for the full exchange universe.
- Do not implement a scheduled T30 workflow in this ticket unless an existing test requires a tiny script-level invocation hook. T30 orchestration is a later ticket.
- Do not implement final `ir1.5+` vs exploratory cohort analysis in this ticket.

---

## 5. Required script contract

Add:

```text
scripts/fetch_ohlcv_history_for_evaluation.py
```

The script must be executable from repo root.

### 5.1 Required CLI arguments

Implement these arguments, with these defaults:

```text
--project-root .
--reports-root reports/runs
--snapshots-runs-root snapshots/runs
--history-root snapshots/history
--start-date 2026-05-03
--end-date <latest closed daily bar date in UTC, unless provided>
--horizons 1,3,5,10
--include-buckets confirmed_candidates,early_candidates
--symbol-source auto
--output-summary evaluation/replay/ohlcv_history_fetch_summary.json
--output-symbols evaluation/replay/ohlcv_history_symbols.json
--dry-run false
--use-cache true
```

Notes:

- `--symbol-source` valid values:
  - `auto`
  - `reports`
  - `diagnostics`
- `auto` must prefer diagnostics when available and fall back to reports when diagnostics are not available.
- Do not require diagnostics to be present for this script to work, because repo persistence intentionally excludes `symbol_diagnostics.jsonl.gz`.
- `--end-date` may be omitted. If omitted, use the latest completed daily bar date according to the existing bar-clock convention.
- `--horizons` is included so the script can fetch enough history for the requested forward-return horizons. It must not change T18's canonical horizon constants.

### 5.2 Optional CLI arguments

Codex may add these if useful and tested:

```text
--max-symbols <int>          # testing/debug only
--force-refetch             # ignore existing local history for requested symbols
--fail-on-empty-universe     # default false
--mexc-limit <int>           # default computed, max 1000
```

Do not add interactive prompts.

---

## 6. Symbol universe extraction

### 6.1 Required symbol population

The script must collect all unique symbols that appeared in:

```text
confirmed_candidates
early_candidates
```

within the selected evaluation window.

The selected evaluation window is based on run/report dates and defaults to:

```text
start-date = 2026-05-03
end-date = latest closed daily date
```

### 6.2 Extraction from reports

When using reports as source, read accumulated reports from:

```text
reports/runs/YYYY/MM/DD/<run_id>/report.json
```

Only process valid non-empty JSON object reports.

A symbol must be included if it appears in either:

```text
symbol_lists.confirmed_candidates
symbol_lists.early_candidates
```

or an equivalent existing report-level candidate list field if the current repo schema uses a different nested path.

If the report contains candidate lists as arrays of strings, use them directly.
If candidate lists contain objects, extract their `symbol` field only when it is a non-empty string.

### 6.3 Extraction from diagnostics

When diagnostics are available, read:

```text
reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz
```

Important: `symbol_diagnostics.jsonl.gz` is intentionally excluded from report persistence and will usually not be present in the repository. It exists in the full Shadow-Live CI artifacts, not in the committed report-persistence subset.

Therefore `--symbol-source auto` must treat missing diagnostics as normal and must transparently fall back to `report.json` candidate lists for that run. Missing diagnostics are not an error in auto mode.

A symbol must be included if:

```text
decision.decision_bucket in {confirmed_candidates, early_candidates}
```

Do not use top-level `decision_bucket` unless the current schema explicitly has it. Current diagnostics are nested.

### 6.4 Auto mode

In `--symbol-source auto`:

1. Prefer diagnostics for a run if a valid diagnostics file exists.
2. Otherwise use that run's `report.json` candidate lists.
3. If neither usable diagnostics nor usable report candidate lists are present for a run, record the run as skipped in the summary.

Do not fail the entire script because one historical run is missing or invalid, unless all runs are unusable and `--fail-on-empty-universe` is true.

### 6.5 De-duplication and ordering

The final symbol list must be:

```text
unique
sorted lexicographically
stable across runs
```

This prevents nondeterministic API request ordering and nondeterministic output summaries.

---

## 7. OHLCV fetch and normalization

### 7.1 Required source

Use the existing MEXC client where possible:

```text
scanner/clients/mexc_client.py
MEXCClient.get_klines(symbol, interval="1d", ...)
```

If the existing helper is insufficient, extend it minimally and safely. Do not create a parallel HTTP client unless there is a concrete repo-reality reason.

### 7.2 Timeframe

Fetch only:

```text
1d
```

No 4h, 1h, or intraday history in this ticket.

### 7.3 Fetch window

The script must fetch enough daily bars to cover:

```text
start_date through end_date
```

plus enough trailing bars that the latest available events can later compute the requested forward horizons when future bars exist.

Because MEXC spot klines may be limit-based rather than start/end based in the existing client, the implementation may fetch a larger recent window and filter locally, but must respect MEXC's API limit constraints.

For the current T30 preparation, max 1000 1d candles per symbol is sufficient. Do not attempt multi-year full-history backfill unless explicitly needed.

### 7.4 Normalized output columns

Each written Parquet row must contain at least:

```text
symbol                  string
timeframe               string, always "1d"
daily_bar_id            string, YYYY-MM-DD
open_time_utc_ms         integer or null
close_time_utc_ms        integer or null
open                    float
high                    float
low                     float
close                   float
volume                  float or null
quote_volume            float or null
source                  string, "mexc_spot_klines"
fetched_at_utc          string, ISO-8601 UTC
```

The existing T18 forward-return code needs at minimum:

```text
daily_bar_id
close
high
low
```

Do not omit those columns.

### 7.5 Numeric robustness

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid and must not be written as valid OHLCV values.

Rules:

- `open`, `high`, `low`, `close` are required for a valid row.
- Required OHLC price fields must be finite and greater than zero.
- `volume` and `quote_volume` may be null if unavailable, but if present they must be finite and non-negative.
- Rows with invalid required OHLC values must be dropped and counted in the summary.
- Symbols with no valid bars must be recorded in the summary and must not produce empty Parquet files.

Do not silently coerce invalid numeric values to zero.

### 7.6 Date normalization

`daily_bar_id` must use UTC and must be derived deterministically from the kline timestamp.

Preferred derivation:

```text
daily_bar_id = UTC date of the candle close/open according to existing project convention
```

If the repo already has a canonical helper for `daily_bar_id`, reuse it. If there is ambiguity between open-time date and close-time date, document the chosen convention in a code comment and keep it consistent with `scanner/evaluation/forward_returns.py` expectations.

---

## 8. Parquet writing contract

### 8.1 Required path layout

Write files under:

```text
<history-root>/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/part-000.parquet
```

Default:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/part-000.parquet
```

This path must remain compatible with `scanner/evaluation/forward_returns.py`.

### 8.2 Idempotent merge behavior

If a partition already exists, the script must:

1. read the existing partition,
2. append newly fetched rows,
3. de-duplicate by `daily_bar_id`,
4. keep the existing row for duplicate `daily_bar_id` unless `--force-refetch` is explicitly set,
5. sort by `daily_bar_id`,
6. write the merged partition back.

Rationale: closed daily bars should be immutable. Re-running the fetcher should not rewrite already persisted closed-bar values unless the caller intentionally requests a refresh.

If `--force-refetch` is set, fetched rows may replace existing rows for duplicate `daily_bar_id`.

Running the script twice with the same inputs and unchanged API data must not create duplicate bars.

### 8.3 Partition scope

Partition by the `year` and `month` of `daily_bar_id`.

If a symbol has bars spanning multiple months, write one partition per month.

### 8.4 Empty partitions

Do not write empty Parquet files.

If a symbol has no valid bars after filtering, record:

```text
status = no_valid_bars
```

in the summary.

---

## 9. Summary and manifest outputs

The script must write:

```text
evaluation/replay/ohlcv_history_fetch_summary.json
evaluation/replay/ohlcv_history_symbols.json
```

### 9.1 `ohlcv_history_symbols.json`

Required structure:

```json
{
  "generated_at_utc": "...",
  "start_date": "2026-05-03",
  "end_date": "...",
  "include_buckets": ["confirmed_candidates", "early_candidates"],
  "symbol_source": "auto",
  "symbol_count": 0,
  "symbols": []
}
```

### 9.2 `ohlcv_history_fetch_summary.json`

Required structure:

```json
{
  "generated_at_utc": "...",
  "start_date": "2026-05-03",
  "end_date": "...",
  "horizons_days": [1, 3, 5, 10],
  "symbol_source": "auto",
  "symbol_count": 0,
  "symbols_fetched": 0,
  "symbols_with_existing_history": 0,
  "symbols_with_new_history": 0,
  "symbols_without_valid_bars": 0,
  "invalid_bar_count": 0,
  "written_partition_count": 0,
  "skipped_run_count": 0,
  "skipped_runs": [],
  "per_symbol": {
    "EXAMPLEUSDT": {
      "status": "ok",
      "bars_written": 0,
      "first_daily_bar_id": null,
      "last_daily_bar_id": null,
      "partition_paths": []
    }
  }
}
```

Allowed per-symbol statuses:

```text
ok
no_valid_bars
fetch_failed
skipped_existing_complete
```

Do not collapse `fetch_failed` and `no_valid_bars`.

---

## 10. Artifact-only and git guardrails

### 10.1 No repo persistence

Generated OHLCV files must not be committed.

Ensure `.gitignore` includes an explicit rule for:

```text
snapshots/history/ohlcv/
snapshots/history/ohlcv/**
```

If equivalent ignore coverage already exists, do not duplicate it.

### 10.2 Do not modify report persistence allowlists

Do not add OHLCV files to:

```text
scripts/persist_shadow_live_reports.py
```

Do not add `snapshots/history/**` to any persistence allowlist.

### 10.3 CI artifact contract for future T30

This ticket does not need to create the final T30 workflow. However, the script outputs must be suitable for future artifact upload.

A future workflow should be able to upload:

```text
snapshots/history/ohlcv/**
evaluation/replay/ohlcv_history_fetch_summary.json
evaluation/replay/ohlcv_history_symbols.json
```

as an evaluation artifact.

Do not implement broad artifact upload in the Shadow-Live daily workflow unless a minimal test harness requires it. The normal daily Shadow-Live workflow should not start fetching OHLCV for T30 on every run in this ticket.

---

## 11. Schema compatibility boundary

This ticket only fetches OHLCV history.

It must not implement final T30 schema compatibility logic.

However, the symbol extraction must work over older Shadow-Live report/diagnostic files where:

- `is_operational_trade_candidate` may be absent,
- `entry_location` may be absent,
- T_EL2 fields may be absent,
- Q1/Q2 `ir1.5` fields may be absent.

This is why symbol extraction is based only on:

```text
confirmed_candidates
early_candidates
```

and not on newer tradeability fields.

---

## 12. Tests required

Add or update tests. Prefer a new test file such as:

```text
tests/test_t30_pre2_ohlcv_history_fetch.py
```

Use fixtures and monkeypatching. Do not call the real MEXC API in unit tests.

### 12.1 Symbol extraction from report lists

Fixture:

```text
reports/runs/2026/05/03/daily-a/report.json
reports/runs/2026/05/04/daily-b/report.json
```

with:

```json
{
  "symbol_lists": {
    "confirmed_candidates": ["INJUSDT"],
    "early_candidates": ["ABCUSDT"],
    "watchlist": ["SHOULDNOTINCLUDEUSDT"]
  }
}
```

Expected:

```text
ABCUSDT
INJUSDT
```

and not `SHOULDNOTINCLUDEUSDT`.

### 12.2 Symbol extraction from diagnostics

Fixture diagnostics records with nested:

```text
decision.decision_bucket
```

Expected:

- include records where bucket is `confirmed_candidates` or `early_candidates`,
- exclude `watchlist`, `late_monitor`, `discarded`,
- do not require `is_operational_trade_candidate`.

### 12.3 Auto mode fallback

Fixture one run with diagnostics and one run without diagnostics but with report lists.

Expected:

- diagnostics run uses diagnostics,
- missing-diagnostics run falls back to report lists,
- summary reports skipped runs only when neither source is usable.

### 12.4 Kline normalization

Mock MEXC kline payload:

```text
[openTime, open, high, low, close, volume, closeTime, quoteVolume, ...]
```

Expected normalized columns:

```text
symbol
timeframe
daily_bar_id
open_time_utc_ms
close_time_utc_ms
open
high
low
close
volume
quote_volume
source
fetched_at_utc
```

Values must be finite numeric where required.

### 12.5 Invalid numeric rows are dropped

Fixture klines with:

- non-numeric close,
- zero close,
- negative high,
- `NaN`,
- `inf`.

Expected:

- invalid rows are not written,
- invalid count appears in summary,
- no invalid OHLC row reaches Parquet.

### 12.6 Parquet partition layout

For symbol `INJUSDT` and bars in May 2026, expected output path:

```text
snapshots/history/ohlcv/timeframe=1d/symbol=INJUSDT/year=2026/month=05/part-000.parquet
```

### 12.7 Idempotency and de-duplication

Run the writer twice with the same bars.

Expected:

- one row per `daily_bar_id`,
- sorted ascending by `daily_bar_id`,
- no duplicate rows.

### 12.8 Existing partition merge

Fixture an existing Parquet partition with one day and fetched data with one overlapping day plus one new day.

Expected without `--force-refetch`:

- overlapping day is de-duplicated,
- the existing overlapping row is kept,
- new day is added,
- partition remains sorted.

If `--force-refetch` is implemented in the same PR, add a separate assertion that the fetched overlapping row replaces the existing row only when `--force-refetch` is set.

### 12.9 Empty universe handling

Fixture no confirmed/early symbols.

Default expected behavior:

- script exits 0,
- writes summary with `symbol_count = 0`,
- writes no Parquet,
- unless `--fail-on-empty-universe` is passed.

With `--fail-on-empty-universe`, script must exit non-zero.

### 12.10 No git persistence regression

Test or inspect that:

- `.gitignore` excludes `snapshots/history/ohlcv/**`,
- `scripts/persist_shadow_live_reports.py` does not allowlist `snapshots/history/**`,
- generated Parquet files are not staged by any persistence helper.

### 12.11 CLI dry run

`--dry-run` must:

- extract symbols,
- write or print summary according to implementation choice,
- not call MEXC,
- not write Parquet.

---

## 13. Acceptance criteria

1. `scripts/fetch_ohlcv_history_for_evaluation.py` exists and is runnable from repo root.
2. The script extracts symbols from accumulated confirmed/early candidate outputs.
3. The script does not require `is_operational_trade_candidate` to exist.
4. The script can operate without committed diagnostics by falling back to report candidate lists.
5. The script fetches only 1d OHLCV.
6. The script writes T18-compatible Parquet history under `snapshots/history/ohlcv/timeframe=1d/...`.
7. Written Parquet contains at least `daily_bar_id`, `close`, `high`, `low`.
8. Written Parquet also contains symbol/timeframe/provenance columns listed in this ticket.
9. Existing partitions are merged idempotently and de-duplicated by `daily_bar_id`.
10. Empty or malformed OHLCV payloads are reported explicitly, not silently converted to valid data.
11. Non-finite numeric values do not reach output Parquet as valid OHLC values.
12. The script writes `evaluation/replay/ohlcv_history_fetch_summary.json`.
13. The script writes `evaluation/replay/ohlcv_history_symbols.json`.
14. OHLCV Parquet is ignored by git and not added to report persistence allowlists.
15. No full-exchange OHLCV fetch is implemented.
16. No 4h history fetch is implemented.
17. Unit tests cover report extraction, diagnostics extraction, auto fallback, normalization, invalid rows, partition writing, idempotency, empty universe, and no-persistence guardrails.
18. Existing tests continue to pass.

---

## 14. Definition of done

Codex must report:

1. Files changed.
2. Whether `MEXCClient.get_klines` was reused or minimally extended.
3. Exact script invocation tested locally, for example:

```bash
python scripts/fetch_ohlcv_history_for_evaluation.py --project-root . --dry-run
```

4. Exact test commands and results, at minimum:

```bash
python -m pytest -q tests/test_t30_pre2_ohlcv_history_fetch.py
python -m pytest -q tests/test_ticket18_evaluation_replay.py
python -m pytest -q
```

5. Confirmation that no generated Parquet/OHLCV files are staged or committed.
6. Confirmation that `scripts/persist_shadow_live_reports.py` still excludes `snapshots/history/**`.

---

## 15. Self-review checklist applied to this ticket

Before handing this ticket to Codex, this draft was checked for:

- one-PR scope,
- no silent T30 implementation,
- no OHLCV repo persistence,
- explicit symbol-scope definition,
- explicit fallback when diagnostics are absent,
- no dependency on `is_operational_trade_candidate`,
- numerical robustness for OHLCV values,
- missing vs invalid vs empty payload separation,
- deterministic symbol ordering,
- idempotent Parquet writes,
- exact path compatibility with T18 forward-return loader,
- no broad persistence allowlist expansion,
- concrete tests rather than vague inspection-only requirements.
