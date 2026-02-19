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
- **T3.2 – Mindesthistorie-Gate (funktional)**
  - Setup-spezifische History-Schwellen (Breakout/Pullback/Reversal) sind in Scorern umgesetzt.
- **T4.1 – Risk Flags (denylist/unlock_overrides)**
  - `config/denylist.yaml` und `config/unlock_overrides.yaml` eingebunden.
  - Hard Exclude für Denylist + `major_unlock_within_14d` aktiv im Universe-Filter.
  - Soft Penalty `minor_unlock_within_14d` wird als Faktor an die Scorer durchgereicht und als `risk_flags` im Setup-Output ausgewiesen.
  - Zusätzlich: `liquidity_grade=D` wird als Hard-Gate vor OHLCV/Scoring entfernt.
- **Schema-Cleanup**
  - `SCHEMA_CHANGES.md` ergänzt und Report-Meta-Version auf **1.4** gesetzt.

---

## 🟡 Teilweise erledigt / Restarbeit nötig

- **T3.1 – percent_rank Population = Hard-Gate Universe**
  - Für Proxy-Liquidity sichtbar gemacht (`proxy_liquidity_population_n`).
  - Population wird vor Shortlist-Trunkierung berechnet.
  - **Offen:** noch nicht als allgemeines Cross-Section-Pattern über alle relevanten Features implementiert.
- **T8.3 – Global Ranking Determinismus**
  - Grundlegende Tests vorhanden.
  - **Offen:** nicht alle v2-Konsistenzfälle (z. B. umfassende tie-matrix/confluence edge-cases) als Golden-Suite ausgebaut.

---

## ❌ Offen

- **T5.1 – Trade Levels (Output-only, deterministisch)**
  - `analysis.trade_levels` / `breakout_level_20` noch nicht umgesetzt.
- **T6.1 – Discovery Tag (date_added / first_seen_ts)**
  - Noch nicht implementiert.
- **T7.1 – Backtest E2-K**
  - `backtest_runner.py` ist weiterhin stub/docstring.
- **T8.1 / T8.4**
  - Indicator-Drift-Guard und Backtest-Golden-Fixtures als v2-umfangreiche Suite noch offen.

---

## Wichtige fachliche Abweichungen/Spannungen für nächste Session

- **History-Gate Semantik vs Tickettext**
  - Aktuell „skippt“ der Scorer bei zu wenig History.
  - Tickettext fordert zusätzlich:
    - `is_valid_setup = False`
    - `reason_invalid = "insufficient history"`
    - inkl. Watchlist-relevanter Spur
- **Schema-Version-Konvention**
  - Report `meta.version` ist jetzt **1.4**.
  - Beim nächsten schema-relevanten Schritt wieder sauber bumpen + `SCHEMA_CHANGES.md` fortführen.

---

## Tests, die den aktuellen Ausbau absichern

- Top-K-Budget + deterministic selection: `tests/test_t82_topk_budget.py`
- Slippage/insufficient depth + rerank tie-break: `tests/test_t23_slippage_metrics.py`
- Global ranking/report integration: `tests/test_t11_global_ranking.py`
- Setup History Gates: `tests/test_t32_min_history_gate.py`
- Proxy population explicitness (Population != Shortlist-Nachweis): `tests/test_phase0_config_wiring.py`

---

## Empfohlener Startpunkt für die nächste Session (konkret)

1. **T5.1** umsetzen (deterministische trade levels, output-only)
2. Danach **T6.1** (discovery tag inkl. fallback)
3. Danach **T7.1** + **T8.4** (Backtest runner + golden fixtures)
4. Parallel **T3.1** abschließen: percent_rank cross-section als allgemeiner Mechanismus, nicht nur Proxy-Liquidity
5. T8.3 Golden-Suite für tie-matrix/confluence edge-cases ausbauen
