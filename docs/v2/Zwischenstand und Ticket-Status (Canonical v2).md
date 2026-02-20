# Ticket-Status (Canonical v2)

**Referenz-Tickets:** `docs/v2/30_IMPLEMENTATION_TICKETS.md`

---

## ✅ Erledigt

- **T1.1 – Global Ranking berechnen**
  - Implementiert via `compute_global_top20(...)` inkl. Gewichte, `best_setup_type`, confluence, Deduplizierung je Symbol.
- **T1.2 – Excel Sheet „Global Top 20“**
  - Neues Sheet **Global Top 20** ist im Excel-Export enthalten.
- **T1.3 – JSON/Markdown `global_top20`**
  - JSON enthält `setups.global_top20`; Markdown enthält den Global-Top-20-Block.
- **T2.1 – Proxy-Liquidity Score**
  - `proxy_liquidity_score` (percent-rank, tie average) im Shortlist-Schritt vorhanden.
- **T2.2 – Orderbook nur Top-K**
  - Top-K-Selection + Budget-Calls implementiert (`liquidity.orderbook_top_k`).
- **T2.3 – Slippage-Berechnung**
  - `spread_bps`, `slippage_bps`, `liquidity_grade`, `liquidity_insufficient` aus Orderbook implementiert.
- **T2.4 – Re-Rank Regel**
  - Global tie-break nutzt `global_score` desc, `slippage_bps` asc (None = +inf), `proxy_liquidity_score` desc.
- **T3.1 – percent_rank Population = Hard-Gate Universe**
  - Generischer Cross-Section-Mechanismus implementiert (`scanner/pipeline/cross_section.py`) mit deterministischem average-tie Ranking gegen die volle Population.
  - Proxy-Liquidity-Verdrahtung nutzt nun den zentralen Mechanismus; Population bleibt explizit das Hard-Gate-Universe (nicht Shortlist).
  - Regression-Tests ergänzt (`tests/test_t31_percent_rank_population.py`) und bestehende Verdrahtungs-Tests bleiben grün.
- **T3.2 – Mindesthistorie-Gate (funktional)**
  - Setup-spezifische History-Schwellen (Breakout/Pullback/Reversal) sind in Scorern umgesetzt.
- **T4.1 – Risk Flags (denylist/unlock_overrides)**
  - `config/denylist.yaml` und `config/unlock_overrides.yaml` eingebunden.
  - Hard Exclude für Denylist + `major_unlock_within_14d` aktiv im Universe-Filter.
  - Soft Penalty `minor_unlock_within_14d` wird als Faktor an die Scorer durchgereicht und als `risk_flags` im Setup-Output ausgewiesen.
  - Zusätzlich: `liquidity_grade=D` wird als Hard-Gate vor OHLCV/Scoring entfernt.
- **T5.1 – Trade Levels (Output-only, deterministisch)**
  - `analysis.trade_levels` je SetupResult implementiert (Breakout/Pullback/Reversal).
  - `breakout_level_20` deterministisch aus 20D-prior-high-Definition abgeleitet.
  - Ohne Einfluss auf Score-/Ranking-Reihenfolge (output-only).

- **T6.1 – Discovery Tag (date_added / first_seen_ts)**
  - Discovery-Logik implementiert (primary: CMC `date_added`, fallback: `first_seen_ts` aus ältester 1D-Candle).
  - Setup-Outputs enthalten `discovery`, `discovery_age_days`, `discovery_source`.
  - Gating erfüllt: Tag erscheint nur bei validen (gescorten) Setups.


- **T7.1 – Backtest E2-K**
  - `scanner/pipeline/backtest_runner.py` von Stub auf lauffähige E2-K-Implementierung erweitert.
  - Canonical-Regeln umgesetzt: Trigger-Suche über 1D-Close in `[t0 .. t0+T_trigger_max]`, Entry auf Trigger-Close, Hits via `max(high[trigger+1 .. trigger+T_hold])` für 10%/20%.
  - Deterministische Aggregation (`by_setup`) + Event-Outputs implementiert, inkl. In-Memory- und History-Runner.
  - Parameter `t_hold`, `t_trigger_max`, `thresholds_pct` in `config/config.yml` ergänzt (Legacy-Backtest-Felder bleiben kompatibel).
  - Tests ergänzt: `tests/test_t71_backtest_runner.py`.


- **T8.4 – Backtest Golden Fixtures**
  - Golden-Fixture-Regression für den E2-K-Runner ergänzt (`tests/test_t84_backtest_golden.py`).
  - Deterministisches Fixture + Expected Snapshot hinzugefügt (`tests/golden/fixtures/backtest_t84_snapshots.json`, `tests/golden/backtest_t84_expected.json`).
  - Deckt Trigger trifft/verfehlt und Thresholds 10/20 reproduzierbar ab.

- **Schema-Cleanup**
  - `SCHEMA_CHANGES.md` ergänzt und Report-Meta-Version auf **1.5** gesetzt.

---

## 🟡 Teilweise erledigt / Restarbeit nötig

- **T8.3 – Global Ranking Determinismus**
  - Grundlegende Tests vorhanden.
  - **Offen:** nicht alle v2-Konsistenzfälle (z. B. umfassende tie-matrix/confluence edge-cases) als Golden-Suite ausgebaut.

---

## ❌ Offen

- **T8.1**
  - Indicator-Drift-Guard (EMA/ATR) als v2-umfangreiche Suite noch offen.

---

## Wichtige fachliche Abweichungen/Spannungen für nächste Session

- **History-Gate Semantik vs Tickettext**
  - Aktuell „skippt“ der Scorer bei zu wenig History.
  - Tickettext fordert zusätzlich:
    - `is_valid_setup = False`
    - `reason_invalid = "insufficient history"`
    - inkl. Watchlist-relevanter Spur
- **Schema-Version-Konvention**
  - Report `meta.version` ist jetzt **1.5**.
  - Beim nächsten schema-relevanten Schritt wieder sauber bumpen + `SCHEMA_CHANGES.md` fortführen.

---

## Tests, die den aktuellen Ausbau absichern

- Top-K-Budget + deterministic selection: `tests/test_t82_topk_budget.py`
- Slippage/insufficient depth + rerank tie-break: `tests/test_t23_slippage_metrics.py`
- Global ranking/report integration: `tests/test_t11_global_ranking.py`
- Setup History Gates: `tests/test_t32_min_history_gate.py`
- Proxy population explicitness (Population != Shortlist-Nachweis): `tests/test_phase0_config_wiring.py`
- Backtest Golden-Fixture (Trigger trifft/verfehlt, Hit10/20): `tests/test_t84_backtest_golden.py`

---

## Empfohlener Startpunkt für die nächste Session (konkret)

1. **T8.3** Golden-Suite für tie-matrix/confluence edge-cases ausbauen
2. **T8.1** Indicator-Drift-Guard (EMA/ATR) vervollständigen
3. Optionaler Review: weitere percent_rank-Anwendungsfälle bei neuen Features konsequent über den zentralen Cross-Section-Helper führen.
