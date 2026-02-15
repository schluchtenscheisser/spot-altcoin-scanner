# Decision Manifest — Phase 5 Overhaul (Spot Altcoin Scanner)

**Generated:** 2026-02-15 (Europe/Berlin)  
**Purpose:** Freeze all “decision points” so Codex can implement Phase‑5 backlog items **without** making implicit strategy changes or guessing.

> ✅ **Current state:** This manifest is pre-filled with **recommended** decisions (Trader-centric).  
> If you want different choices, edit the **FINAL** values below and keep the rest as-is.

---

## Quick copy block (for Codex)

```
D1=C
D2=B
D3=A
D4=A
D5=A
D6=A
D7=A
D8=B2
D9=B
D10=A
D11=B
D12=B
D13=A
D14=C
D15=A
D16=C1
D17=B
BONUS=C
```

---

## Stable definitions

- **“Canonical keys”** = the new, documented, non-legacy weight keys.
- **“Legacy aliases”** = old/alternate config keys supported for backward compatibility.
- **“No silent drift”** = same inputs should produce the same scores/rankings unless a change is explicitly versioned.

---

## Decisions

### D1 — Weight Parser default mode
**Question:** Default mode when parsing weights (`strict` vs `compat`).  
**FINAL:** **C** — Auto: `strict` if canonical keys are present, otherwise `compat`.  
**Why:** Minimizes breakage while preventing mixed/migrated configs from silently changing behavior.

---

### D2 — Partial weights (some keys set, others missing)
**Question:** How to fill missing weights without changing explicitly-set ratios.  
**FINAL:** **B** — Keep explicit weights **exact**, assign the remaining weight mass **only** across missing keys (proportional distribution among missing keys).  
**Why:** Preserves trader-intended tuning and avoids silent rebalancing.

---

### D3 — Conflict: canonical + legacy aliases both present
**Question:** Which wins when both appear simultaneously.  
**FINAL:** **A** — Canonical wins; legacy ignored; log a warning.  
**Why:** Prevents ambiguous merged configs; encourages clean migration.

---

### D4 — Must weight sum ≈ 1.0?
**Question:** Enforce weight sums to prevent scaling/clamp drift.  
**FINAL:** **A** — Enforce sum ~ 1.0 (within tolerance). In `strict`: fail. In `compat`: fail or very hard warning (no auto-fix).  
**Why:** Sum≠1 changes score scaling → ranking drift.

---

### D5 — Strict-transparency validator output format
**Question:** “Machine-readable” error format.  
**FINAL:** **A** — Single JSON object: `{ ok, errors:[{path, code, msg, got, expected}, ...] }`  
**Why:** Best for CI, stable diffs, automation.

---

### D6 — Canonical numeric ranges for `components` and `raw_score`
**Question:** Docs show conflicts (0–1 vs 0–100). Choose canonical.  
**FINAL:** **A** — Canonical: **0–100** for `components.*` and `raw_score` (and `score`).  
**Why:** Most interpretable for traders; aligns with typical scoring/report conventions; avoids mixed semantics.

---

### D7 — `base_score = NaN` handling
**Question:** Should NaN become 0, 50, or trigger re-weighting?  
**FINAL:** **A** — NaN ⇒ **0** (component effectively not achieved).  
**Why:** 50 would fabricate “neutral bases”; re-normalizing causes silent per-asset weight drift.

---

### D8 — Drawdown lookback: convert days → bars
**Question:** How to map day-based lookback to timeframe bars, and rounding.  
**FINAL:** **B2** — Parse timeframe generically, compute bars-per-day, use **ceil**.  
**Why:** Generic mapping prevents future bugs; `ceil` is conservative (no undercounted lookbacks).

---

### D9 — Pullback Uptrend Guard: `dist_ema50_pct == 0` allowed?
**Question:** Is price exactly at EMA50 still “uptrend”?  
**FINAL:** **B** — Allow `dist_ema50_pct >= 0`.  
**Why:** EMA50 touch is a common pullback/support behavior; strict `>0` drops valid setups.

---

### D10 — Legacy exclusions override scope (empty list disables)
**Question:** If `filters.exclusion_patterns` exists (even `[]`), what does it override?  
**FINAL:** **A** — Legacy key presence overrides all new exclusion logic; empty list means “no exclusions”.  
**Why:** “Explicit config wins” principle; deterministic behavior; easiest to debug.

---

### D11 — Lookback priority: `general.lookback_days_*` vs `ohlcv.lookback`
**Question:** Which has precedence when both provided.  
**FINAL:** **B** — Keep `ohlcv.lookback` as an override; `general.*` is default.  
**Why:** Fetch limits are operational controls; traders want targeted overrides without changing global defaults.

---

### D12 — Meaning of `ohlcv.lookback`
**Question:** Is it days or bars (API limit)?  
**FINAL:** **B** — Treat as **bars/limit** (direct fetch limit).  
**Why:** Operationally unambiguous; avoids unit confusion.

---

### D13 — `include_only_usdt_pairs=false`: which quotes are included?
**Question:** Include non‑USDT pairs without breaking comparability.  
**FINAL:** **A** — Include **stablecoin-quoted** pairs; exclude BTC/ETH quoted pairs (no FX conversion).  
**Why:** Keeps liquidity/volume comparable without complex conversions (avoids trash rankings).

**Stable-quote allowlist (initial):**  
`USDT, USDC, DAI, TUSD, FDUSD, USDP, BUSD`  
(Adjust list if exchange reality changes; keep deterministic.)

---

### D14 — Reason text vs scoring: spike “truth source”
**Question:** Which spike value is presented and used in reasoning.  
**FINAL:** **C** — Show both quote-spike and base-spike, and explicitly label which one was used for scoring.  
**Why:** Prevents “reason lies” while keeping debug value.

---

### D15 — Setup object score fields
**Question:** Which score fields are mandatory to avoid ambiguity.  
**FINAL:** **A** — Always include: `score`, `raw_score`, `penalty_multiplier` (no `final_score` redundant field).  
**Why:** Minimizes redundancy and “which is correct?” confusion.

---

### D16 — Snapshot vs runtime-meta storage
**Question:** Directory/layout strategy and whether to auto-migrate files.  
**FINAL:** **C1** — Separate folders **and** regex whitelist for snapshot discovery; **do not** auto-move old files (ignore them).  
**Why:** Max robustness; avoids hidden file mutations that complicate audits.

---

### D17 — Fallback policy for API/Quota outages
**Question:** Should run fail, degrade, or use cache?  
**FINAL:** **B** — Use last known cache if available and **mark run as degraded/stale**; otherwise fail.  
**Why:** Traders prefer a clearly-labeled “stale-but-usable” research output over silence, but provenance must be explicit.

---

## BONUS — Add `rank` / `normalized` to JSON output
**Question:** Should JSON include `rank` and/or `normalized`?  
**FINAL:** **C** — Add **rank only** (no normalized).  
**Why:** Rank is useful for reading and regression checks; normalized often adds confusion (0–1 vs 0–100 debate).

---

## Notes for Codex implementation

1. **No silent behavior changes:** If any FINAL decision forces a behavior shift, version it and document it.
2. **Deterministic output:** Same input → same output. Sort orders must be stable.
3. **Transparency parity:** “Reason” output must never contradict the scoring computation.
4. **Degraded runs:** If D17 triggers cache fallback, metadata must show freshness timestamps and degraded flag.
