# Roadmap_LowCost_Automation_ImpactFirst — FOLLOW-UP BACKLOG (nach Ticket-Schnitt)

**Stand:** 2026-02-27T00:00:00Z  
**Leitplanken:** maximal automatisiert, keine/geringe Zusatzkosten (≤ 20 USD/Monat), deterministisch, closed-candle-only, keine Lookahead-Leaks.  
**Datenbasis (default):** MEXC (Spot OHLCV + Orderbook) + CMC (Mapping + Market Cap + basic meta).  
**Optionale Free Bridges (feature-flag):** RSS (Announcements), CoinGecko (Meta/Tags, nur soft).

---

## Bereits in Tickets überführt (aus dieser Roadmap entfernt)
Diese Themen sind **bereits** in konkrete Codex-Tickets überführt und gehören **nicht** mehr in den offenen Backlog:
- Canonical Update: MODEL_E2 Reason Codes + Precedence
- Snapshot Schema: `meta.btc_regime` persistieren + `snapshot.meta.version` → 1.1
- Canonical Doc: Evaluation Dataset JSONL Spec + Snapshot Field Mapping
- Implementierung: `scanner/backtest/e2_model.py` + Tests
- Implementierung: Evaluation Dataset Exporter (JSONL, meta-record + candidate_setup records)
- Tools: Backfill `btc_regime` für alte Snapshots
- Tools: Backfill fehlender Snapshots (date range; minimal default; optional full) inkl. Backfill-Meta-Flags

> Hinweis: Canonical-Dokumente bilden den **aktuellen** Stand ab; wenn Verbesserungen aus der Roadmap abweichen, wird die Dokumentation **vor** der Implementierung entsprechend angepasst (per eigenem Ticket).

---

## Phase 0 — Stop-the-bleeding (bereits umgesetzt)
**Status:** DONE (laut Nutzer; Tickets aus `2026-02-26__Stop_the_bleeding_tickets.md` wurden umgesetzt).

Diese Fixes sind Voraussetzung für verlässliche Automatisierung:
- Orderbook Top-K robust (kein Run-Abbruch bei Single-Symbol-Fehlern; kein `None`-Orderbook für non-selected Symbole; Budget-safe Top-K Calls).
- Closed-candle gates konsistent (Breakout/Pullback behandeln fehlenden `last_closed_idx` als insufficient history).
- Proxy-liquidity percent-rank Regression-Tests (unsortierter Input, ties, Monotonie).
- Schema-/Snapshot-Disziplin (Schema-Version bump + `SCHEMA_CHANGES`; Scoring-Text bleibt im Snapshot-Workflow erhalten).
- Tests: Fixture-Pfade CWD-unabhängig.

---

## Phase A — Messbarkeit + Zielkopplung (ohne neue Datenquellen)
Ziel: Das System misst objektiv „liefert Kandidat X +10%/+20% innerhalb 1–5 Tagen?“ und kann Rankings kalibrieren.

### A3 — Ranking Quality Metrics (für Research/Iteration)
Standard-Analytics, die Ranking-Systeme professionell machen:
- Precision@K (K=10/20) auf `hit_10_5d`, `hit_20_5d`
- Score→Return correlation (score vs `mfe_pct`, score vs `hit_10_5d`)
- Rank monotonicity diagnostics: Hit-rate pro Score-Bin; reporte monotone violations.

**Erwarteter Output (minimal):**
- CLI/Script, das ein/mehrere Dataset-JSONL Dateien einliest (glob).
- Ergebnisse als Markdown/JSON (deterministisch) inkl. Run-Range, Sample-N, Setup-Filter.

### A4 — Score-Kalibrierung (ohne ML) + Daily Output
- Score-Bins (Default 10er) → empirische Hit-Rates je Setup/Regime.
- Daily Reports enthalten:
  - `p_hit_10_5d_calibrated`, `p_hit_20_5d_calibrated`
  - `calibration_sample_n`, `calibration_version`
- Fallback: wenn Kalibrierung fehlt, Run läuft weiter und markiert degraded.

**Wichtige Fragen, die beim Ticket-Schnitt geklärt werden müssen:**
- Welche Binning-Strategie: feste 10er Bins vs quantile Bins?
- Welche Mindest-Sample-N je Bin/Setup/Regime bevor „calibrated“ gesetzt wird?
- Wie wird „calibration_version“ versioniert (Date, Git SHA, SemVer)?

---

## Phase B — Trader-Briefing Outputs (ohne neue Datenquellen)
Ziel: tägliche Report-Ausgabe ist „tradeable“ (Trigger/Invalidation/TP/SL), nicht nur ein Ranking.

### B1 — Standardisierte Trade-Plan-Felder (deterministisch, pro Setup)
Pro Kandidat:
- `trigger_price`
- `entry_zone_low/high`
- `invalidation_price`
- `stop_loss_price`
- `tp1_price`, `tp2_price`
- `risk_reward_tp1`, `risk_reward_tp2`
- `trade_plan_notes`

Start mit: `breakout_immediate_1_5d`, `breakout_retest_1_5d`, dann Pullback/Reversal.

### B2 — Setup-Validity + Reason Codes + Near-Miss Watchlist
- Explizite Validity-Schicht statt impliziter Early Returns
- `invalid_reason_code` + optional `invalid_details`
- Near-miss watchlist (knapp invalide, aber beobachtenswert): `near_miss_metric` + `distance_to_threshold`

---

## Phase C — Beta/Alpha Layer (MEXC-only) als Filter + Multiplikator im Ranking
Ziel: pro Coin unterscheiden zwischen „BTC-Hebel“ und „idiosynkratischem Move“.  
**Entscheidung:** Beta/Alpha soll **im Ranking** wirken (Filter + Multiplikator).

### C1 — Beta/Alpha Features berechnen
Inputs: MEXC OHLCV 1D (optional 4H) für Coin und Benchmark (`BTCUSDT`, optional `ETHUSDT`).

Outputs (Minimum):
- `beta_to_btc_60d` (rolling cov/var)
- `alpha_r3_vs_btc`, `alpha_r7_vs_btc`
- optional `beta_to_eth_60d`, alpha vs ETH
- quality flags: `beta_window_n`, `beta_insufficient_history`

### C2 — Ranking Adjustments (konfigurierbar, deterministisch)
- **Risk-Off Filter** (Beispiel):
  - require `alpha_r7_vs_btc > 0`
  - optional cap `beta_to_btc < 1.5`
- **Multiplikator** (clamped), applied auf `global_score`:
  - `mult = clamp(1 + w7*alpha_r7 + w3*alpha_r3 - wβ*max(0, beta-β0), lo, hi)`
- Output: `adjusted_global_score` + Diagnosefelder (`beta_alpha_multiplier`, components).
- Tie-break deterministisch: `adjusted_global_score` desc, `slippage_bps` asc, `proxy_liquidity_score` desc, `symbol` asc.

---

## Phase D — Automatisierung mit Free/Low-Cost Quellen (optional, feature-flag)
Ziel: zusätzliche Kontextsignale ohne manuellen Pflegeaufwand.

### D1 — Exchange Status / Maintenance / Delist Risk aus MEXC (0 USD)
- API Endpoints (falls verfügbar) → `risk_flags` + hard exclude wenn Trading disabled / maintenance.
- Graceful degrade wenn Endpoint nicht verfügbar.

### D2 — CoinGecko Free Tier: Meta/Tags/Events als **soft** Signal (0 USD, caching)
- Nur Tags/Soft penalties, keine hard excludes in V1.
- Daily caching + rate limiting.

### D3 — RSS Announcements: Listing/Delisting/Maintenance Tagging (0 USD)
- Keyword-based tagging, report-only in V1.

---

## Phase E — Signalqualität aus bestehenden Daten (ohne neue Quellen)
Diese Punkte kommen aus internen Notizen und sind vollständig MEXC/CMC-basiert.

### E1 — Robust Statistics
- median/trimmed mean statt mean-only
- robuste Z-Scores
- percentile ranks (cross-sectional und per symbol)

### E2 — Candle Structure + wick-robust logic
- body/wicks/range/efficiency metrics
- false-breakout flags
- wick-robuste Breakout-Definitionen (vermeidet „one-wick spikes“)

### E3 — Drawdown & Window Semantik schärfen
- mehrere Drawdown-Horizonte (window-high vs. ATH) sauber unterscheiden
- „echtes ATH seit Listing“ bleibt paid/extern (siehe Paid Backlog), aber window-high kann verbessert werden

### E4 — Unify Base Logic (kanonische Base-Definition über Setups)
- eine Base-Definition, konsumiert von Breakout/Pullback/Reversal
- BaseScore Verbesserungen (contraction, range metrics, nichtlineare Skalierung)

### E5 — Config-driven Parameter Audit
- thresholds/weights strikt aus `config/config.yml` mit Legacy fallback + Logwarnung
- CI-/Tests, die config wiring regressions verhindern

### E6 — Drift/Health Monitoring (0 USD)
- missing candles / abnormal volumes / feature distribution checks
- Run manifest mit Warnings + Input-Freshness-Meta

---

## Phase G — Research Tools (ohne Execution)
### G1 — Snapshot Replay CLI
- Timeline aus Snapshots/Features/Scores pro Symbol/Date-Range (text/markdown)
- Unterstützt Debugging ohne UI

### G2 — Golden Fixtures + deterministische Integrationstests
- offline fixtures, Ranking-Reihenfolge + key fields prüfen

### G3 — Canonical Compliance Tests
- slippage rounding, rerank sort keys, global dedup tie-break, closed-candle policy

---

## Phase H — ML Overlay (optional, ohne neue Datenquellen)
ML ist ein Overlay und wird erst nach stabiler Messbarkeit & Datenqualität empfohlen.
- Trainingsdatensatz Export (features + labels aus Snapshots + E2)
- Baseline GBM offline + calibration (time-based split / walk-forward)
- Keine Live-Integration bis klarer Gewinn vs. Rules+Calibration
