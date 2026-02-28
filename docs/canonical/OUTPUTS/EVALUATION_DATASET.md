# Evaluation Dataset Export — JSONL Spec + Snapshot Mapping (Canonical)

## Machine Header (YAML)
```yaml
id: OUTPUT_EVALUATION_DATASET
status: canonical
output_kind: evaluation_dataset_jsonl
path_pattern: "artifacts/evaluation/evaluation_dataset_*.jsonl"
record_types:
  - meta
  - candidate_setup
format:
  type: jsonl
  one_json_object_per_line: true
determinism:
  closed_candle_only: true
  no_lookahead: true
  stable_ordering_required: true
links:
  - docs/canonical/BACKTEST/MODEL_E2.md
  - docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md
```

## 0) Purpose
This document defines the canonical JSONL contract for exporting E2 evaluation rows from snapshot history.

Hard rules:
- No heuristics.
- No inferred fields.
- If a mapped source field is missing, write `null` (when nullable) or fail validation (when non-nullable).

## 1) File-level contract
- Format: JSONL (`.jsonl`), UTF-8.
- Exactly one JSON object per line.
- First line MUST be a `meta` record.
- All subsequent lines are `candidate_setup` records.

Record types:
1. `{"type":"meta", ...}`
2. `{"type":"candidate_setup", ...}`

## 2) Input snapshot contract (source)
Each processed daily snapshot is expected at canonical shape:
- `snapshot.meta`
- `snapshot.data.features`
- `snapshot.scoring.reversals`
- `snapshot.scoring.breakouts`
- `snapshot.scoring.pullbacks`

Missing scoring lists rule:
- If all scoring lists are empty for a snapshot date, exporter emits zero `candidate_setup` records for that date.
- The file still contains exactly one `meta` record (line 1).

## 3) Identity rules (deterministic)

### 3.1 `run_id`
Default derivation:
- Source: exporter wall-clock at export start (`UTC now`)
- Format: `YYYY-MM-DD_HHMMSSZ_mmm`
- Example: `2026-02-27_000510Z_482`

Scope:
- `run_id` is file-scope (one JSONL export = one `run_id`).
- All candidate rows MUST reuse the same file-scope `run_id`.

Override:
- A CLI/runtime override may replace derived `run_id`.
- If override is provided, it MUST be used verbatim for all records.

### 3.2 `record_id`
Canonical formula:
- `record_id = "{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}"`

Where:
- `t0_date` is snapshot day (`snapshot.meta.date`, `YYYY-MM-DD`).
- `symbol` is scoring entry symbol.
- `setup_type` is canonical setup family (`reversal | breakout | pullback`).
- `setup_id` is scoring entry `setup_id`; fallback is `setup_type` if `setup_id` missing/empty.

## 4) Candidate row cardinality
A candidate row is defined as:
- `1 symbol × 1 setup × 1 t0_date`

For each snapshot date:
- Iterate all entries in `scoring.reversals`, `scoring.breakouts`, `scoring.pullbacks`.
- Emit exactly one `candidate_setup` record per scoring entry.

## 5) Ranking rules

### 5.1 `setup_rank`
- 1-based index in the native order of the corresponding snapshot scoring list.
- `scoring.reversals[i]` => `setup_rank = i + 1` for `setup_type = reversal`.
- `scoring.breakouts[i]` => `setup_rank = i + 1` for `setup_type = breakout`.
- `scoring.pullbacks[i]` => `setup_rank = i + 1` for `setup_type = pullback`.

No re-sorting is allowed before computing `setup_rank`.

### 5.2 `global_rank` (Top20-only)
- Recompute global Top-20 deterministically using canonical rules from `SCORING/GLOBAL_RANKING_TOP20.md` over the snapshot scoring lists.
- If the candidate symbol is present in recomputed Top-20: `global_rank` is `1..20`.
- Otherwise `global_rank = null`.

## 6) E2 outcome fields
E2 outcome fields are recomputed per candidate using canonical E2 rules in `BACKTEST/MODEL_E2.md`.

Threshold policy:
- Threshold list is configurable.
- Thresholds `10` and `20` MUST always be included.

Required outcome fields on each candidate record:
- `reason`
- `t_trigger_date`
- `t_trigger_day_offset`
- `entry_price`
- `hit_10` (always present)
- `hit_20` (always present)
- `hits` (object with string keys like `"5"`, `"10"`, `"20"` and nullable boolean values)
- `mfe_pct`
- `mae_pct`

`reason` values and precedence follow `BACKTEST/MODEL_E2.md`.

## 7) JSONL schema by record type

### 7.1 Meta record
```json
{
  "type": "meta",
  "run_id": "2026-02-27_000510Z_482",
  "export_run_id": "2026-02-27_000510Z_482",
  "exported_at_iso": "2026-02-27T00:05:10Z",
  "export_started_at_ts_ms": 1772141110482,
  "source_snapshot_count": 31,
  "source_snapshot_dates": ["2026-01-28", "...", "2026-02-27"],
  "thresholds_pct": [10, 20],
  "notes": null
}
```

### 7.2 Candidate record
```json
{
  "type": "candidate_setup",
  "record_id": "2026-02-27_000510Z_482:2026-02-15:ABCUSDT:breakout:breakout_retest_1_5d",
  "run_id": "2026-02-27_000510Z_482",
  "t0_date": "2026-02-15",
  "symbol": "ABCUSDT",
  "setup_type": "breakout",
  "setup_id": "breakout_retest_1_5d",
  "snapshot_version": "1.0",
  "asof_ts_ms": 1772140800000,
  "asof_iso": "2026-02-27T00:00:00Z",
  "market_cap_usd": 123456789.0,
  "quote_volume_24h_usd": 4567890.0,
  "liquidity_grade": "B",
  "btc_regime": "range",
  "score": 74.12,
  "setup_rank": 2,
  "global_rank": 11,
  "reason": "ok",
  "t_trigger_date": "2026-02-17",
  "t_trigger_day_offset": 2,
  "entry_price": 1.2345,
  "hit_10": true,
  "hit_20": false,
  "hits": {"10": true, "20": false},
  "mfe_pct": 13.7,
  "mae_pct": -4.2
}
```

## 8) Field mapping table (candidate_setup)
| Dataset field | Source path / derivation | Type | Nullable |
|---|---|---:|:---:|
| `type` | Constant `"candidate_setup"` | string | no |
| `record_id` | `"{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}"` | string | no |
| `run_id` | File-scope export identifier: CLI override or derived once from export start UTC as `YYYY-MM-DD_HHMMSSZ_mmm` | string | no |
| `t0_date` | `snapshot.meta.date` | string (`YYYY-MM-DD`) | no |
| `symbol` | `scoring_entry.symbol` | string | no |
| `setup_type` | Iteration context (`reversal` for `scoring.reversals`, `breakout` for `scoring.breakouts`, `pullback` for `scoring.pullbacks`) | string | no |
| `setup_id` | `scoring_entry.setup_id` else fallback `setup_type` | string | no |
| `snapshot_version` | `snapshot.meta.version` | string | no |
| `asof_ts_ms` | `snapshot.meta.asof_ts_ms` | integer | no |
| `asof_iso` | `snapshot.meta.asof_iso` | string (RFC3339 UTC) | no |
| `market_cap_usd` | `snapshot.data.features[symbol].market_cap` | number | yes |
| `quote_volume_24h_usd` | `snapshot.data.features[symbol].quote_volume_24h` | number | yes |
| `liquidity_grade` | `snapshot.data.features[symbol].liquidity_grade` | string | yes |
| `btc_regime` | `snapshot.meta.btc_regime` | string | yes |
| `score` | `scoring_entry.score` | number | no |
| `setup_rank` | 1-based positional index within the current scoring list | integer | no |
| `global_rank` | Rank from recomputed canonical global Top-20 by symbol; else `null` | integer | yes |
| `reason` | Recomputed E2 reason (`BACKTEST/MODEL_E2.md`) | string | no |
| `t_trigger_date` | Recomputed E2 trigger date | string (`YYYY-MM-DD`) | yes |
| `t_trigger_day_offset` | Recomputed E2 offset from `t0_date` | integer | yes |
| `entry_price` | Recomputed E2 entry price | number | yes |
| `hit_10` | Recomputed E2 hit for threshold 10% | boolean | yes |
| `hit_20` | Recomputed E2 hit for threshold 20% | boolean | yes |
| `hits` | Recomputed E2 threshold map (string threshold -> nullable boolean) | object | no |
| `mfe_pct` | Recomputed E2 MFE in percent | number | yes |
| `mae_pct` | Recomputed E2 MAE in percent | number | yes |

Source alias:
- `scoring_entry` means one object from exactly one of:
  - `snapshot.scoring.reversals[*]`
  - `snapshot.scoring.breakouts[*]`
  - `snapshot.scoring.pullbacks[*]`

## 9) Null and missing handling
- For nullable fields: if source path is missing/unavailable, emit `null`.
- For non-nullable fields: exporter MUST fail row validation and surface error (no silent defaults).
- Exporter MUST NOT infer missing values from alternate paths unless explicitly listed in this document.

## 10) Determinism constraints
- Closed-candle-only and no-lookahead apply via E2 canonical model.
- Rank recomputation uses canonical deterministic tie rules.
- For identical input snapshots and thresholds, produced records MUST be byte-stable modulo `exported_at_iso` in the meta record.
