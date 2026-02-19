# Phase‑5 Decision Manifest (Supplement to OVERHAUL_BACKLOG_PHASE5.md)

**Purpose**  
This document freezes all **strategy/semantics decisions** that are *not fully specified* in the Phase‑5 backlog, so Codex can implement the work **without guessing** and without introducing **silent ranking/score drift**.

**How to use**  
- Treat each item below as a **hard requirement** unless explicitly superseded by a later, versioned spec change.
- If you disagree with any requirement, **edit this file** and keep it in the repo alongside the backlog.

---

## Definitions (binding)

- **No silent drift:** Same input data + same config ⇒ same computed features/scores/rankings (except when a change is explicitly versioned and documented).
- **Canonical weight keys:** The non‑legacy weight keys documented for current scoring.
- **Legacy weight aliases:** Any historical/alternate config keys that map to canonical keys.
- **Degraded run:** A run that proceeds with cached/stale inputs or partial data must be explicitly flagged in metadata and reports.

---

## DEC‑01 — Weight parsing mode (default behavior)

**Requirement**  
- If canonical weight keys are present in the config, parse weights in **strict canonical mode**.  
- If canonical keys are absent but legacy aliases are present, parse weights in **compatibility mode**.

**Rationale**  
Prevents mixed/migrated configs from silently changing behavior while avoiding unnecessary breakage of legacy configs.

---

## DEC‑02 — Partial weights must not change explicit ratios

**Requirement**  
If a weights config specifies only a subset of canonical keys:
- The explicitly provided weights must remain **exact** (no renormalization over all keys).
- The **remaining** weight mass (1.0 minus the sum of explicit weights) is distributed **only** across missing keys (proportionally using their defaults).

**Rationale**  
Preserves intentional tuning and prevents hidden rebalancing that would alter rankings.

---

## DEC‑03 — Conflict resolution: canonical + legacy weights both provided

**Requirement**  
If both canonical keys and legacy aliases are provided for the same conceptual weight:
- **Canonical values take precedence.**
- Legacy values are ignored.
- Emit a clear warning indicating the conflict and which side won.

**Rationale**  
Avoids ambiguous merged behavior and encourages clean migration.

---

## DEC‑04 — Weight sums must be ~1.0 (no auto-fix)

**Requirement**  
- The effective weight sum must be approximately **1.0** (within a small tolerance, e.g. 1e‑6).  
- If not, treat as a configuration error. Do **not** silently renormalize.

**Rationale**  
Sum≠1 changes score scaling and can alter clamping/threshold effects, producing silent ranking drift.

---

## DEC‑05 — Strict-transparency validator output must be machine-readable JSON

**Requirement**  
Validator output format must be a single JSON object like:

```json
{
  "ok": false,
  "errors": [
    {"path": "setups.reversals[0].raw_score", "code": "RANGE", "msg": "...", "got": 123, "expected": "[0,100]"}
  ]
}
```

**Rationale**  
Stable, diffable, CI-friendly, and easy for tools to consume.

---

## DEC‑06 — Canonical numeric scale for scoring outputs

**Requirement (canonical output semantics)**  
- `score` is **0–100** (final score used for ranking).  
- `raw_score` is **0–100** (pre-penalty score on same scale).  
- `components.*` are **0–100**.

**Rationale**  
Directly interpretable for traders; avoids mixed 0–1 vs 0–100 semantics in outputs.

---

## DEC‑07 — Handling missing/NaN base_score

**Requirement**  
If `base_score` is NaN/missing in a context where it would otherwise be used:
- Treat it as **0** (component not achieved).  
- Do not treat as “neutral 50”.
- Do not remove/reweight the component per‑asset (no per‑asset renormalization due to missing values).

**Rationale**  
Neutral defaults fabricate setups; per-asset renormalization creates silent weight drift between assets.

---

## DEC‑08 — Drawdown lookback conversion (days → bars)

**Requirement**  
- Drawdown lookback is defined in **days** at config/spec level.  
- Convert days to bars by parsing the timeframe generically (e.g., `4h` ⇒ 6 bars/day).  
- Use **ceil** when converting (ensure the bar window is not shorter than the day window).

**Rationale**  
Avoids undercounting lookback windows and keeps behavior consistent across timeframes.

---

## DEC‑09 — Pullback uptrend guard at EMA50 boundary

**Requirement**  
For the pullback “uptrend guard” based on distance to EMA50:
- Consider uptrend valid when `dist_ema50_pct >= 0` (touching EMA50 is allowed).

**Rationale**  
EMA50 “touch” is a common pullback/support behavior; excluding equality would drop legitimate setups.

---

## DEC‑10 — Legacy exclusions override semantics (empty list disables exclusions)

**Requirement**  
If the legacy key `filters.exclusion_patterns` is present:
- It overrides the newer exclusions mechanism entirely.
- If it is an empty list, it explicitly means **“no exclusions”** (do not apply default exclusions).

**Rationale**  
“Explicit config wins” is required for deterministic behavior and debuggability.

---

## DEC‑11 — Lookback precedence: general vs OHLCV fetch override

**Requirement**  
- `general.lookback_days_*` defines defaults.  
- `ohlcv.lookback` (if provided) is an explicit override for OHLCV fetching behavior.

**Rationale**  
Fetch limits are operational controls; traders need targeted overrides without changing global defaults.

---

## DEC‑12 — Units for `ohlcv.lookback`

**Requirement**  
- `ohlcv.lookback[timeframe]` is interpreted as **bars/limit** (API fetch limit), not days.

**Rationale**  
Avoids unit confusion and aligns with fetch mechanics.

---

## DEC‑13 — Non‑USDT universe behavior

**Requirement**  
If the universe is configured to include non‑USDT pairs:
- Only include pairs quoted in **stablecoins** (no BTC/ETH quoted pairs unless full FX conversion is implemented and versioned).
- Stablecoin quote allowlist (initial):  
  `USDT, USDC, DAI, TUSD, FDUSD, USDP, BUSD`

**Rationale**  
Keeps liquidity/volume comparable without FX conversion; prevents “trash rankings” caused by mixed quote currencies.

---

## DEC‑14 — Reason text must not contradict scoring (volume spike)

**Requirement**  
- If scoring uses a specific spike metric (quote or base), reasons must report the same **used** value.  
- For transparency, report both metrics when available, but explicitly label which one was used for scoring.

**Rationale**  
Reasons must never “lie”; traders rely on reasons to validate signals quickly.

---

## DEC‑15 — Required score detail fields in setup objects

**Requirement**  
Every setup entry in machine-readable output must include:
- `score` (final, 0–100)
- `raw_score` (0–100)
- `penalty_multiplier` (0–1]

Do not introduce redundant alternative “final_score” fields unless explicitly versioned and justified.

**Rationale**  
Prevents ambiguity and keeps reports auditable.

---

## DEC‑16 — Snapshot vs runtime-meta separation

**Requirement**  
- Store snapshots and runtime-meta in **separate namespaces** (prefer separate folders).  
- Snapshot discovery must whitelist only valid snapshot files (e.g., strict date-based naming).  
- Do **not** auto-move historical files as a side effect of runs; ignore legacy runtime-meta files if encountered.

**Rationale**  
Prevents accidental ingestion, keeps replay/backtests clean, avoids hidden filesystem mutations.

---

## DEC‑17 — Outage/quota fallback policy

**Requirement**  
- If live data sources fail (API/quota):
  - Use last-known cache **only if available**.
  - Mark the run as **degraded** with freshness timestamps in metadata.
  - If no cache is available, fail rather than silently producing partial/unknown-quality output.

**Rationale**  
A clearly-labeled stale run can still be useful; unlabeled degradation destroys trader trust.

---

## Optional output enhancement: rank field in JSON report

**Requirement**  
Include an explicit `rank` field per setup entry (based on sorted `score`). Do not add `normalized` unless explicitly needed and versioned.

**Rationale**  
Rank improves usability and regression testing without adding scale confusion.

---

**End of manifest.**
