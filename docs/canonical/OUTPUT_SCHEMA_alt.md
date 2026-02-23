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

## 2) Markdown output
- Must be consistent with JSON (no contradictions).
- Typical sections:
  - Top-N table(s)
  - Quick diagnostics summary
  - Notes about as-of and determinism

## 3) Excel output
- A tabular export of the same canonical fields.
- Column order should be stable.

## 4) Schema evolution
- Any breaking change increments `schema_version`.
- Canonical changes must be reflected in docs and tests/fixtures.
