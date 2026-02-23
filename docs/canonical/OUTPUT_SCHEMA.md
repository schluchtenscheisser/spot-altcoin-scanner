# Output Schema — JSON / Markdown / Excel (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: 1
outputs:
  - json
  - markdown
  - excel
limits:
  global_top_n_default: 20
trade_levels:
  status: canonical_output_only
  note: "Trade levels are informational outputs; they must not affect ranking unless explicitly referenced."
```

## 1) JSON output
Canonical goal: JSON is the primary machine-readable artifact.

### 1.1 Run manifest (required)
- `commit_hash`
- `config_hash` or `config_version`
- `schema_version`
- `asof_ts_ms` (or ISO timestamp)
- `providers_used` (MEXC/CMC, etc.)

### 1.2 Candidate row (required, minimal set)
- Identity:
  - `symbol`
  - `setup_id`
- Scores:
  - `base_score`
  - `final_score`
- Core diagnostics (setup-specific required fields)
  - for Breakout Trend 1–5d: see `SCORING/SCORE_BREAKOUT_TREND_1_5D.md` section “Pflichtfelder”
- Liquidity:
  - `spread_bps` (optional if not fetched)
  - `slippage_bps` (optional if not fetched)
  - `liquidity_insufficient_depth` (bool)
  - `liquidity_grade` (A/B/C/D, if graded)
- Validity:
  - `is_valid_setup`
  - `invalid_reason` (required if invalid)

### 1.3 Ordering and limits
- Global Top list is limited to `global_top_n` (default 20).
- Any re-rank ordering must be explainable by `LIQUIDITY/RE_RANK_RULE.md`.

## 2) Trade levels (informational output, deterministic)
If trade levels are included in outputs, they must be computed deterministically from **closed candles only** and must not change ranking.

### 2.1 Required fields (if present)
- `trade_levels_enabled` (bool)
- `levels_timeframe` in {"1d","4h"} (default is implementation-defined; must be stable)
- `entry_level` (price)
- `stop_level` (price)
- `partial_target_level` (price, optional)
- `take_profit_level` (price, optional)
- `risk_R` (price distance; optional)

### 2.2 Canonical formulas (default)
These formulas are canonical **when trade levels are emitted**. If the implementation differs, it must be documented explicitly.

Let:
- `entry_level = close_last_closed` (same timeframe chosen for trade levels)
- `atr_abs = (atr_pct_last_closed/100) * close_last_closed`
- `stop_level = entry_level - 1.2 * atr_abs`
- `R = entry_level - stop_level`
- `partial_target_level = entry_level + 1.5 * R` (optional)
- `take_profit_level = entry_level + 3.0 * R` (optional)

Notes:
- If ATR% is not available (NaN), levels must be omitted or flagged as unavailable (deterministically).
- If `close_last_closed <= 0`, all levels are undefined.

### 2.3 Determinism constraints
- Only closed candles
- Stable timeframe selection per run (e.g., always 4H for breakout setups), not per-symbol ad hoc
- No lookahead (no use of future candles)
- Rounding policy (if any) must be explicit and stable

## 3) Markdown output
- Must be consistent with JSON (no contradictions).
- Typical sections:
  - Top-N table(s)
  - Quick diagnostics summary
  - Notes about as-of and determinism

## 4) Excel output
- A tabular export of the same canonical fields.
- Column order should be stable.

## 5) Schema evolution
- Any breaking change increments `schema_version`.
- Canonical changes must be reflected in docs and tests/fixtures.
