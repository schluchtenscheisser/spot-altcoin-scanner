# CODEX-Implementierungs-Spezifikation (Phasen 0–4)
**Projekt:** `schluchtenscheisser/spot-altcoin-scanner`  
**Ziel:** Die inhaltlichen Änderungen so präzise beschreiben, dass GPT-Codex ohne Interpretationsspielraum implementieren kann.  
**Datenquellen:** Keine neuen Datenquellen (nur CMC + MEXC wie bisher).  
**Verbindlich:** `config/config.yml` ist **Single Source of Truth** für Parameter (Gewichte, Schwellen, Limits). Keine Hardcodes außer exakt identischen Defaults zur Abwärtskompatibilität.

---

## Globale Implementierungsregeln (gelten für alle Phasen)
1. **Score-Skalen**
   - Jeder Setup-Score und jeder Component-Score ist im Bereich **[0.0 … 100.0]**.
   - Endscore: auf **2 Dezimalstellen** runden.
   - Clamping: nach jeder Score- und Penalty-Berechnung `score = max(0.0, min(100.0, score))`.

2. **Weights**
   - Weights werden aus `config/config.yml` gelesen (Setup-spezifisch).
   - Wenn Weight-Summe ≠ 1.0: **normalisieren** (jede Weight durch Summe teilen).
   - Wenn Weights fehlen: **Fallback exakt auf die derzeitigen Code-Defaults** (nur zur Abwärtskompatibilität), aber **Logwarnung** ausgeben.

3. **Penalties**
   - Penalties sind **multiplikative Faktoren** auf den Raw-Score:  
     `final_score = raw_score * Π(penalty_factor_i)`
   - Zusätzlich im Output:
     - `penalty_multiplier = Π(penalty_factor_i)` (float)
     - `raw_score` (float)
     - `final_score` (identisch zu `score`)

4. **Missing Data**
   - Wenn ein für einen Component-Score benötigter Feature-Wert `None` ist: Component-Score = **0.0** und Flag `missing_<feature>` setzen (z.B. `missing_breakout_dist_20`).
   - Setup darf nicht crashen, sondern läuft sauber mit 0.0-Teilscore weiter.

5. **Zeitanker (keine Intrabar-Verfälschung)**
   - FeatureEngine arbeitet **ausschließlich auf der letzten vollständig geschlossenen Kerze** pro Timeframe (keine Partial-Candles).

---

# Phase 0 — Konfigurations-Wiring & Konsistenz-Fixes (höchster Impact)

## Ziel
Sicherstellen, dass Pipeline-Logik und Scorer **tatsächlich die Werte aus `config/config.yml`** verwenden (statt stiller Defaults).

## 0.1 UniverseFilters: Config-Struktur korrekt auslesen
**Datei:** `scanner/pipeline/filters.py`  
**Klasse:** `UniverseFilters`

### Soll-Zustand
- `UniverseFilters` muss **primär** aus `root["universe_filters"]` lesen.
- Abwärtskompatibilität: wenn `filters` existiert, darf es als Legacy-Fallback dienen.

### Konkrete Mapping-Regeln
Aus `config/config.yml`:
- Market Cap: `universe_filters.market_cap.min_usd`, `universe_filters.market_cap.max_usd`
- 24h Quote Volume: `universe_filters.volume.min_quote_volume_24h`
- Historie: `universe_filters.history.min_history_days_1d`
- Pair-Restriction: `universe_filters.include_only_usdt_pairs`
- Exclusions: `exclusions.*` (stablecoins / wrapped / leveraged / synthetic)

**Regel:** Wenn ein Block fehlt → fallback auf bisherige Defaults (exakt wie aktueller Code).

### Acceptance Criteria
- Wenn YAML-Werte geändert werden, ändern sich Filter-Ergebnisse sichtbar (z.B. mehr/weniger Coins).
- Keine breaking changes für alte Configs (Legacy-Schlüssel funktionieren noch).

---

## 0.2 ShortlistSelector: shortlist_size korrekt auslesen
**Datei:** `scanner/pipeline/shortlist.py`  
**Klasse:** `ShortlistSelector`

### Soll-Zustand
- Primär lesen: `general.shortlist_size`
- Legacy-Fallback: `shortlist.max_size` (wenn vorhanden)

### Acceptance Criteria
- `general.shortlist_size: 50` führt zu exakt max. 50 Kandidaten nach Shortlisting.

---

## 0.3 OhlcvFetcher: Lookback korrekt auslesen
**Datei:** `scanner/pipeline/ohlcv.py`  
**Klasse:** `OhlcvFetcher`

### Soll-Zustand
Primär aus YAML:
- `general.lookback_days_1d`
- `general.lookback_days_4h`

**Umrechnung in Candle-Limit (exakt):**
- Für Timeframe `1d`: `limit = lookback_days_1d`
- Für Timeframe `4h`: `limit = lookback_days_4h * 6`  (24h / 4h = 6)

**Min Candles:**
- `min_candles` bleibt Default **50**, aber zusätzlich:
  - Für `1d` muss `len(bars_1d) >= universe_filters.history.min_history_days_1d` gelten, sonst Coin ausfiltern.

### Acceptance Criteria
- `general.lookback_days_4h = 10` resultiert in `limit=60` bei 4h.
- Coins mit < `min_history_days_1d` werden vor FeatureEngine/Scoring entfernt.

---

## 0.4 Scorer-Weights: vollständig Config-driven
**Dateien:**
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`

### Soll-Zustand
- Weights müssen aus YAML gelesen werden:
  - `scoring.breakout.weights`
  - `scoring.pullback.weights`
  - `scoring.reversal.weights`
- Wenn Weights fehlen → Legacy-Default aus Code verwenden, aber **Logwarnung**: `"Using legacy default weights; please define config.scoring.<setup>.weights"`

### Acceptance Criteria
- Änderung der Weights in YAML verändert Scores messbar ohne Codeänderung.

---

# Phase 1 — FeatureEngine: Volume-Baseline pro Timeframe

## Ziel
Volume-Spike sauberer und timeframe-gerecht: bei 4h schneller, bei 1d stabiler.

## Änderung: Volume-SMA-Perioden je Timeframe
**Datei:** `scanner/pipeline/features.py`  
**Klasse:** `FeatureEngine`

### Config-Schema (Erweiterung, Abwärtskompatibel)
In `config/config.yml` unter `features` hinzufügen:

```yaml
features:
  volume_sma_periods:
    1d: 14
    4h: 7
```

**Fallback-Regel:**
- Wenn `features.volume_sma_periods` fehlt:
  - verwende `features.volume_sma_period` als globale Periodenlänge für alle Timeframes (Legacy).
- Wenn beide fehlen:
  - fallback auf aktuellen Code-Default (14), mit Logwarnung.

### Exakte Berechnung (pro Timeframe)
- `volume_sma = SMA(volume, period, include_current=False)`
- `volume_spike = current_volume / volume_sma`  
  - Wenn `volume_sma` = 0 oder None → `volume_spike = 1.0`
- Gleiches für Quote-Volume (wenn vorhanden):
  - `volume_quote_sma`
  - `volume_quote_spike`

### Output-Keys (präzise)
Pro Timeframe (z.B. `features["1d"]`):
- `volume_sma` (float)
- `volume_sma_period` (int)
- `volume_spike` (float)
- `volume_quote_sma` (float oder None)
- `volume_quote_spike` (float oder None)

**Kompatibilität:**
- Bestehende Keys dürfen **nicht entfernt** werden ohne gleichzeitiges Update der Golden-Tests.
- Wenn aktuell Keys wie `volume_sma_14` existieren: beibehalten und zusätzlich neue Keys ausgeben (Cleanup später).

### Acceptance Criteria
- Bei gleicher Historie erzeugt 4h deutlich „reaktiveres“ Volume-Spike als 1d.
- Keine Regression: FeatureEngine läuft für Coins ohne Quote-Volume weiterhin.

---

# Phase 2 — Reversal: Base-/Drawdown-/Reclaim-Logik strikt und config-getrieben

## Ziel
Reversal-Setups sollen weniger „Dead Cats“ und weniger „zu früh“ signalisieren. Fokus: echte Bodenbildung + Reclaim.

## 2.1 BaseScore in FeatureEngine (Scorer konsumiert nur Features)
**Datei:** `scanner/pipeline/features.py`

### Konfigurationsquelle
Ausschließlich YAML:
- `scoring.reversal.base_lookback_days`
- `scoring.reversal.min_base_days_without_new_low`
- `scoring.reversal.max_allowed_new_low_percent_vs_base_low`

### Exakte Base-Definition (1d)
- Window `L = base_lookback_days`
- Recent-Segment `K = min_base_days_without_new_low`
- Es müssen mindestens `L` 1d-Kerzen existieren (sonst `base_score=None`)

**Berechnung:**
1. `older = last L candles excluding last K candles`
2. `recent = last K candles`
3. `base_low = min(low in older)`
4. `recent_low = min(low in recent)`
5. Toleranz: `tol = max_allowed_new_low_percent_vs_base_low / 100`
6. **No-new-low-Condition:**
   - `recent_low >= base_low * (1 - tol)`  → PASS
   - sonst FAIL

**Stability / Range:**
- `range_pct = ((max(close in recent) - min(close in recent)) / min(close in recent)) * 100`
- `stability_score = max(0, 100 - range_pct)`

**Final BaseScore:**
- Wenn PASS: `base_score = stability_score`
- Wenn FAIL: `base_score = 0`

**Zusatzfelder (Debug/Transparenz):**
- `base_low`
- `base_recent_low`
- `base_range_pct`
- `base_no_new_lows_pass` (bool)

### Acceptance Criteria
- Coins mit weiter fallenden Lows erhalten BaseScore 0.
- Enge Seitwärtsphase nach Low führt zu BaseScore > 60.

---

## 2.2 ReversalScorer: Weights & Penalties config-driven
**Datei:** `scanner/pipeline/scoring/reversal.py`

### Komponenten
- `drawdown`
- `base`
- `reclaim`
- `volume`

### DrawdownScore (exakt)
- `dd = drawdown_from_ath` (negativ in %)
- `dd_pct = abs(dd)`
- Wenn `dd is None` oder `dd >= 0` → 0.0
- Wenn `dd_pct < min_drawdown_pct` → 0.0
- Wenn `ideal_drawdown_min <= dd_pct <= ideal_drawdown_max` → 100.0
- Wenn `dd_pct < ideal_drawdown_min`:
  - `ratio = (dd_pct - min_drawdown_pct) / (ideal_drawdown_min - min_drawdown_pct)`
  - `score = 50 + ratio*50`
- Wenn `dd_pct > ideal_drawdown_max`:
  - `excess = dd_pct - ideal_drawdown_max`
  - `penalty = min(excess/20, 0.5)`
  - `score = 100 * (1 - penalty)`

### VolumeScore (Quote bevorzugen, linear)
- Spike:
  - `spike_1d = volume_quote_spike if not None else volume_spike`
  - `spike_4h = volume_quote_spike if not None else volume_spike`
  - `max_spike = max(spike_1d, spike_4h)`
- Wenn `max_spike < min_volume_spike` → 0
- Wenn `max_spike >= 3.0` → 100
- Sonst:
  - `ratio = (max_spike - min_volume_spike) / (3.0 - min_volume_spike)`
  - `score = ratio*100`

### ReclaimScore (exakt)
- Start `score=0`
- `dist_ema20_pct > 0` → +30
- `dist_ema50_pct > 0` → +30
- `hh_20 == True` → +20
- Momentum-Term:
  - `momentum_score = clamp((r_7 / 10) * 100, 0, 100)`
  - `score += 0.2 * momentum_score`
- Cap: `score = min(score, 100)`

### Weights & Penalties
- Weights aus `scoring.reversal.weights` (Legacy-Fallback + Logwarnung)
- Penalties aus `scoring.reversal.penalties`:
  - Overextension:
    - wenn `dist_ema50_pct > overextension_threshold_pct` → Faktor `overextension_factor`, Flag `overextended`
  - Low liquidity:
    - wenn `quote_volume_24h < low_liquidity_threshold` → Faktor `low_liquidity_factor`, Flag `low_liquidity`

### Output erweitern
- `raw_score`
- `penalty_multiplier`

### Acceptance Criteria
- Parameteränderungen in YAML ändern Reversal-Scores deterministisch.
- Quote-Volume-Spike wird bevorzugt genutzt, sofern vorhanden.

---

# Phase 3 — Breakout & Pullback: Scoring-Formeln deterministisch und config-getrieben

## 3.1 BreakoutScorer
**Datei:** `scanner/pipeline/scoring/breakout.py`

### Komponenten
- `breakout` (Price Break / „Freshness“)
- `volume`
- `trend`
- `momentum`

### BreakoutScore (exakt; piecewise)
Input: `dist = breakout_dist_20` (in %; kann negativ sein)

Parameter aus YAML:
- `breakout_curve.floor_pct`
- `breakout_curve.fresh_cap_pct`
- `breakout_curve.overextended_cap_pct`
- `min_breakout_pct`
- `ideal_breakout_pct`
- `max_breakout_pct`

**Funktion:**
1. Wenn `dist is None` → 0
2. Wenn `dist <= floor_pct` → 0
3. Wenn `floor_pct < dist < 0`:
   - `score = 30 * (dist - floor_pct) / (0 - floor_pct)`
4. Wenn `0 <= dist < min_breakout_pct`:
   - `score = 30 + 40 * (dist - 0) / (min_breakout_pct - 0)`
5. Wenn `min_breakout_pct <= dist <= ideal_breakout_pct`:
   - `score = 70 + 30 * (dist - min_breakout_pct) / (ideal_breakout_pct - min_breakout_pct)`
6. Wenn `ideal_breakout_pct < dist <= max_breakout_pct`:
   - `score = 100 * (1 - (dist - ideal_breakout_pct) / (max_breakout_pct - ideal_breakout_pct))`
7. Wenn `dist > max_breakout_pct` → 0

**Zusatzflag (nur Info):**
- wenn `dist > overextended_cap_pct` → Flag `overextended_breakout_zone`

### TrendScore (exakt)
- `dist_ema20_pct > 0` → +40, wenn zusätzlich `>5` → +10 extra
- `dist_ema50_pct > 0` → +40, wenn zusätzlich `>5` → +10 extra
- Cap 100

### MomentumScore (linear)
- `momentum_score = clamp((r_7 / r7_divisor) * 100, 0, 100)`

### VolumeScore (Quote bevorzugen, linear)
- Spike wie in Phase 2
- Parameter:
  - `min_volume_spike`
  - `ideal_volume_spike`
- Wenn `< min` → 0
- Wenn `>= ideal` → 100
- Sonst: `100 * (spike - min)/(ideal - min)`

### Weights & Penalties
- Weights aus `scoring.breakout.weights` (Legacy-Fallback + Logwarnung)
- Penalties aus `scoring.breakout.penalties`:
  - `max_overextension_ema20_percent` & `overextension_factor` (multiplikativ)
  - `low_liquidity_threshold` & `low_liquidity_factor` (multiplikativ)

### Acceptance Criteria
- `tests/test_critical_findings.py::test_breakout_momentum_is_continuous_linear_scaling` bleibt grün.

---

## 3.2 PullbackScorer
**Datei:** `scanner/pipeline/scoring/pullback.py`

### Komponenten
- `trend`
- `pullback`
- `rebound`
- `volume`

### ReboundScore: Continuous r7-Komponente MUSS bleiben
- `momentum_score = clamp((r_7 / r7_divisor) * 100, 0, 100)`
- `rebound += 0.2 * momentum_score`

### VolumeScore (Quote bevorzugen; diskret + linear)
- Spike wie in Phase 2
- Parameter: `min_volume_spike`
- Wenn `< min` → 0
- Wenn `>= 2.5` → 100
- Wenn `>= 2.0` → 80
- Sonst:
  - `ratio = (spike - min)/(2.0 - min)`
  - `score = ratio * 70`

*(Schwellen 2.0/2.5 bleiben exakt wie im aktuellen Code, außer spätere Parametrisierung.)*

### Trend/Pullback-Formeln
- Bestehende Logik beibehalten, aber:
  - Alle Schwellen/Weights aus YAML lesen (kein Hardcode mehr)
  - Penalties:
    - `broken_trend_factor`
    - `low_liquidity_factor`

### Acceptance Criteria
- `tests/test_critical_findings.py::test_pullback_rebound_includes_continuous_r7_component` bleibt grün.

---

# Phase 4 — Output/Transparenz/Validierung

## Ziel
Jeder Score muss nachvollziehbar sein („Warum rankt Coin A höher als Coin B?“).

## 4.1 Scoring Output erweitern (alle 3 Scorer)
**Dateien:** `scanner/pipeline/scoring/*.py`

### Output-Felder (zusätzlich zu heute)
Pro Coin/Setup-Resultat:
- `raw_score` (float, 2 decimals)
- `penalty_multiplier` (float, 4 decimals)
- `score` bleibt Finalscore (raw * multiplier, geclamped)

### Penalty-Objektstruktur
`penalties` bleibt dict `{name: factor}`, zusätzlich:
- `penalty_multiplier` als Produkt dieser Faktoren (oder 1.0 wenn keine)

---

## 4.2 ReportGenerator/Output: Komponententabellen konsistent
**Datei:** `scanner/pipeline/output.py`

### Muss-Zustand
- In Markdown/JSON-Reports sollen pro Setup sichtbar sein:
  - `score`, `raw_score`, `penalty_multiplier`
  - `components` (alle Komponentenwerte)
  - `flags`

**Keine Layout-Interpretation:**  
Wenn Tabellenbreite zu groß wird:
- JSON: vollständig
- Markdown: nur `score/raw_score/penalty_multiplier` + 2–3 wichtigste Komponenten, Rest in „details“-Block oder separat als JSON-Datei (falls schon vorgesehen).

---

## 4.3 validate_features Tool: Scoring-Plausibilität erweitern
**Datei:** `scanner/tools/validate_features.py`

### Erweiterung (exakt)
Zusätzlich prüfen:
- `score` und `raw_score` müssen in **[0..100]** liegen
- Jede Komponente in `components` muss in **[0..100]** liegen
- `penalty_multiplier` muss in **(0..1]** liegen (Penalties schwächen ab)

---

# PR-Splitting (empfohlen)
Damit „max 3 Dateien / PR“ und „kleine Diffs“ eingehalten werden:

- **Phase 0** in 3 PRs:
  1) `filters.py` + `shortlist.py`  
  2) `ohlcv.py`  
  3) `scoring/*.py` Weights config-driven (je Setup ggf. 1 PR)

- **Phase 1** in 1 PR:
  - `features.py` + `config/config.yml` (+ ggf. Golden-Test Update)

- **Phase 2** in 2 PRs:
  1) `features.py` BaseScore v2  
  2) `reversal.py` Score/Weights/Penalties + Output raw_score

- **Phase 3** in 2 PRs:
  1) `breakout.py` Breakout-Formel + Tests  
  2) `pullback.py` YAML-driven + Tests bleiben grün

- **Phase 4** in 2 PRs:
  1) `output.py` Report-Erweiterung  
  2) `validate_features.py` Validierungslogik

---

## Definition of Done (für jede Phase)
- `pytest` grün
- Keine neuen externen Datenquellen
- Keine Hardcodes für Parameter, die in YAML existieren (außer identische Legacy-Fallbacks)
- Report zeigt `raw_score` + `penalty_multiplier` + `components`
