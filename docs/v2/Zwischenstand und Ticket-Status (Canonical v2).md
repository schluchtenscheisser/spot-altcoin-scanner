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

- **T8.3 – Global Ranking Determinismus**
  - Golden-Suite für tie-matrix/confluence edge-cases ergänzt (`tests/test_t83_global_ranking_determinism.py`).
  - Neue deterministische Fixtures/Snapshots für Ranking-Reihenfolge, stable ties, Einmaligkeit pro Symbol und Confluence-Aggregation (`tests/golden/fixtures/global_ranking_t83_snapshots.json`, `tests/golden/t83_global_ranking_expected.json`).



- **T8.2 – Top-K Budget Test (Orderbook)**
  - Regression-Test für Top-K-Orderbook-Budget geschärft (`tests/test_t82_topk_budget.py`).
  - Verifiziert explizit: bei Universe > K werden nur K Orderbooks via Mock geladen; alle übrigen Symbole bleiben im Payload mit `None`.
  - Keine Netzwerkanfragen im Testpfad (Dummy-Client/Mock-only).

- **T8.1 – Indicator Tests (EMA/ATR)**
  - Neue deterministische Drift-Guard-Suite für EMA und ATR ergänzt (`tests/test_t81_indicator_ema_atr.py`).
  - Fixtures mit bekannten Referenzwerten + Edge Cases hinzugefügt (`tests/golden/fixtures/t81_indicator_cases.json`).
  - Abgedeckt: SMA-Initialisierung (EMA), Wilder-Smoothing (ATR), kurze Reihen (insufficient history), NaN-Seed-Window (EMA) sowie `close<=0`-Fallback (ATR).

- **Schema-Cleanup**
  - `SCHEMA_CHANGES.md` ergänzt und Report-Meta-Version auf **1.5** gesetzt.

---

## ❌ Offen


- **Canonical-v2 Kern-Tickets (T1–T8)**
  - Im Dokumentstand weiterhin als erledigt geführt.

- **Neue Codex-PR-Tickets (C1–C8)**
  - Diese Tickets sind neu aufgenommen (aus den zusammengeführten PR-Kommentaren) und müssen als separate PRs umgesetzt werden:
- **C1 – Orderbook Top-K: pro Symbol soft-fail (kein Pipeline-Crash)**
  - Pro Symbol try/except um `mexc_client.get_orderbook(...)` (Top-K).
  - Fehlerhafte Symbole bleiben `orderbooks[symbol]=None`, Pipeline läuft weiter; Warning-Log mit `exc_info`.
  - Neue Tests: erweitert/neu auf Basis `tests/test_t82_topk_budget.py` (Exception-Szenario + Calls==K).

- **C2 – Closed-Candle Gate: None => insufficient_history (Reversal Scoring)**
  - Wenn `_closed_candle_count(...)` `None` liefert, muss das als `insufficient_history` gelten (kein “Durchrutschen”).
  - Neue Tests: `tests/test_reversal_closed_candle_gate.py` (None-Fall + Boundary-Fall == min_history).

- **C3 – Unlock Overrides: defensives Parsing von `days_to_unlock`**
  - Ungültige Werte (None/""/"7d"/negativ) dürfen nicht crashen; Eintrag ignorieren + Warning.
  - Neue Tests: `tests/test_unlock_overrides_parsing.py` (mix valid/invalid, keine Exception).

- **C4 – lookback_days_1d vs min_history_*: Konsistenzregel + Tests**
  - Off-by-one durch offene Tageskerze sauber lösen (Regel definieren & implementieren).
  - Neue Tests: reproduzieren 120 lookback vs 119 closed; nach Fix konsistentes Verhalten.

- **C5 – Backtest E2-K: Kalender-Tage statt Snapshot-Index**
  - `t_trigger_max`/`t_hold` als Kalendertage interpretieren; fehlende Tage nicht “komprimieren”.
  - Neue Tests: `tests/test_backtest_calendar_days.py` (Snapshots mit Lücken; 2026-01-05 darf nicht in Trigger-Window rutschen).

- **C6 – Tests: Fixture Paths robust (relativ zu `__file__`)**
  - Fix mindestens `tests/test_t81_indicator_ema_atr.py` (und ggf. weitere), sodass Fixtures CWD-unabhängig geladen werden.
  - Optionaler Zusatztest nur falls sinnvoll; primär refactor + bestehende Tests grün.

- **C7 – percent_rank_average_ties: explizite Tests (ties/unsorted/deterministisch)**
  - Neue Tests: `tests/test_percent_rank_average_ties.py` (unsorted, ties, determinism).

- **C8 – Schema-Versioning: `schema_version` im finalen Output + docs/SCHEMA_CHANGES.md**
  - `schema_version` als explizites Feld im finalen Report/JSON ausgeben; zentral definieren.
  - `docs/SCHEMA_CHANGES.md` entsprechend erweitern + Version bump.
  - Neue Tests: minimaler Writer/Output-Test oder Golden-Update.


---

## Wichtige fachliche Abweichungen/Spannungen für nächste Session


- **History-Gate Semantik / Closed-Candle Realität**
  - `None` bei closed-candle count darf nicht “durchrutschen” (**C2**).
  - Off-by-one zwischen `lookback_days_1d` und `min_history_*` muss klar geregelt werden (**C4**).

- **Orderbook-Robustheit**
  - Einzelne API-/Orderbook-Fehler dürfen den Run nicht abbrechen (**C1**).

- **Backtest Zeit-Semantik**
  - `t_trigger_max`/`t_hold` sollen Kalendertage sein; Missing-days dürfen nicht komprimiert werden (**C5**).

- **Schema-Version-Konvention**
  - `schema_version` muss explizit im finalen Output auftauchen + `docs/SCHEMA_CHANGES.md` fortführen (**C8**).

---

## Tests, die den aktuellen Ausbau absichern

- Top-K-Budget + deterministic selection: `tests/test_t82_topk_budget.py`
- Slippage/insufficient depth + rerank tie-break: `tests/test_t23_slippage_metrics.py`
- Global ranking/report integration: `tests/test_t11_global_ranking.py`
- Setup History Gates: `tests/test_t32_min_history_gate.py`
- Proxy population explicitness (Population != Shortlist-Nachweis): `tests/test_phase0_config_wiring.py`
- Backtest Golden-Fixture (Trigger trifft/verfehlt, Hit10/20): `tests/test_t84_backtest_golden.py`
- Global Ranking Determinismus Golden-Fixture (ties/confluence/einmalig): `tests/test_t83_global_ranking_determinism.py`
- (neu geplant) Orderbook soft-fail: erweitert `tests/test_t82_topk_budget.py` oder neuer Test
- (neu geplant) Reversal closed-candle None-gate: `tests/test_reversal_closed_candle_gate.py`
- (neu geplant) Unlock overrides parsing: `tests/test_unlock_overrides_parsing.py`
- (neu geplant) Backtest Kalender-Tage: `tests/test_backtest_calendar_days.py`
- (neu geplant) percent_rank tie/unsorted determinism: `tests/test_percent_rank_average_ties.py`
- (neu geplant) schema_version Output: (neuer minimaler Writer/Output-Test oder Golden-Update)

---

## Empfohlener Startpunkt für die nächste Session (konkret)


1. **C1** Orderbook Top‑K soft‑fail (Stabilität, verhindert Pipeline‑Crash).
2. **C2** Closed‑candle Gate: `None` => insufficient_history (Korrektheit).
3. **C3** Unlock overrides defensives Parsing (Stabilität).
4. **C4** lookback/min_history Konsistenzregel + Tests (fachliche Konsistenz).
5. **C5** Backtest Kalender‑Tage (fachliche Semantik).
6. **C6** Test‑Fixtures CWD‑unabhängig (Robustheit).
7. **C7** percent_rank Tests (Robustheit/Regression‑Guard).
8. **C8** schema_version im Output + SCHEMA_CHANGES (Governance/Schema).
