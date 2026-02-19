# Overhaul Backlog (PR #5–#19)

Ziel: Offene Risiken aus den analysierten PR-Reviews systematisch abbauen.

## Priorisierung

- **P1 (sofort):** R12, R15
- **P2 (kurzfristig):** R6, R7, R8, R9, R10, R13, R14, R16
- **P3 (stabilisierend):** R1, R3, R4, R5, R11

---

## Ticket 1 — Scorer-Weights ohne unbeabsichtigte Renormalisierung anwenden (R12)

**Problem**  
Aktuelle Weight-Loader-Logik ergänzt fehlende Defaults und normalisiert danach; konfigurierte Gewichtsverhältnisse werden ungewollt verschoben.

**Zielzustand**
- Explizit konfigurierte Keys bleiben unverändert.
- Legacy-Aliase werden unterstützt, aber nur als Mapping.
- Fehlende Keys werden nur dann ergänzt, wenn das Verhalten klar dokumentiert ist.

**Umsetzung**
- Gemeinsame Hilfsfunktion für Weight-Parsing (`scanner/pipeline/scoring/*`).
- Modus definieren:
  - `strict`: alle kanonischen Keys müssen vorhanden sein.
  - `compat`: Legacy-Aliase erlaubt, aber keine stillen Ratio-Änderungen.
- Bei widersprüchlicher Config: Warnung + deterministischer Fallback.

**Akzeptanzkriterien**
- Konfigurierte Gewichte bleiben numerisch erhalten (bis auf Rundungsfehler).
- Regressionstest für Legacy- und Canonical-Config vorhanden.

---

## Ticket 2 — Validator auf „strict transparency“ umstellen (R15)

**Problem**  
`raw_score` und `penalty_multiplier` werden nicht strikt als Pflichtfelder validiert.

**Zielzustand**
- Validator schlägt fehl, wenn required score-transparency Felder fehlen.
- Exit-Code bleibt deterministisch (`0` ok, `1` fail).

**Umsetzung**
- Pflichtfeldprüfung in `scanner/tools/validate_features.py` ergänzen.
- Plausibilitätschecks erzwingen:
  - `score`, `raw_score`, `components.*` in `[0,100]`
  - `penalty_multiplier` in `(0,1]`
- Fehlermeldungen maschinenlesbar strukturieren.

**Akzeptanzkriterien**
- Missing-field Report führt reproduzierbar zu Exit-Code `1`.
- Valid Report führt reproduzierbar zu Exit-Code `0`.

---

## Ticket 3 — `base_score` robust gegen `NaN` machen (R6)

**Zielzustand**
- `NaN` wird als fehlender Wert behandelt, niemals als `100`.

**Akzeptanzkriterien**
- Unit-Test: `base_score=np.nan` resultiert in neutral/0-Score-Komponente.

---

## Ticket 4 — Drawdown-Lookback korrekt timeframe-basiert umrechnen (R7)

**Zielzustand**
- Day-basierter Lookback wird pro Timeframe in Bar-Anzahl übersetzt.

**Akzeptanzkriterien**
- 1d und 4h ergeben bei gleicher Lookback-Day-Config konsistente Semantik.
- Tests prüfen korrekte Fensterlänge je Timeframe.

---

## Ticket 5 — Pullback-Uptrend-Guard schärfen (R8)

**Zielzustand**
- Klare Semantik, ob `dist_ema50_pct == 0` zulässig ist (Default: nicht zulässig).

**Akzeptanzkriterien**
- Testfälle für `<0`, `==0`, `>0` vorhanden.
- Doku (`docs/scoring.md`) entspricht Implementierung.

---

## Ticket 6 — Legacy-Exclusions: leere Liste als explizit respektieren (R9)

**Zielzustand**
- `filters.exclusion_patterns: []` deaktiviert Exclusions deterministisch.

**Akzeptanzkriterien**
- Key-Presence statt Truthiness.
- Backward-Compatibility-Test vorhanden.

---

## Ticket 7 — Config-Priorität bei Lookback klären und durchsetzen (R10)

**Zielzustand**
- Neue `general.lookback_days_*` sind primär.
- Legacy `ohlcv.lookback` nur fallback, wenn primäre Keys fehlen.

**Akzeptanzkriterien**
- Prioritätsmatrix in `docs/config.md` dokumentiert.
- Tests decken alle Mischkonfigurationen ab.

---

## Ticket 8 — `include_only_usdt_pairs` technisch erzwingen (R13)

**Zielzustand**
- Flag beeinflusst Universe-Filter tatsächlich.

**Akzeptanzkriterien**
- Bei `true` werden Non-USDT-Paare zuverlässig ausgeschlossen.
- Bei `false` bleiben sie erhalten.

---

## Ticket 9 — Reason-Text und Score-Datenpfad vereinheitlichen (R14)

**Zielzustand**
- Begründungstext nutzt exakt denselben Spike-Wert/Fallback wie Scoring.

**Akzeptanzkriterien**
- Kein Widerspruch mehr zwischen Komponentenwert und Erklärung.

---

## Ticket 10 — Score-Details bis in Report-Payload propagieren (R16)

**Zielzustand**
- `raw_score` und `penalty_multiplier` werden in alle relevanten Setup-Objekte übertragen.

**Akzeptanzkriterien**
- Markdown enthält „Score Details“ in realen Pipeline-Reports.
- Test mit End-to-End-ähnlichem Setup-Payload vorhanden.

---

## Ticket 11 — Snapshot vs Runtime Meta sauber trennen (R1)

**Zielzustand**
- Kein Schema-Mix bei Snapshot-Discovery.

**Akzeptanzkriterien**
- Runtime-Meta liegt in separatem Namespace.
- Snapshot-Listing ignoriert fremde JSON-Schemata robust.

---

## Ticket 12 — Governance & CI-Härtung (R3, R4, R5, R11)

**Zielzustand**
- Stabilere PR-Qualität und reproduzierbare CI.

**Umsetzung**
- Minimal-Review-Checklist einführen.
- CI-Abhängigkeiten explizit (inkl. `pytest`) installieren.
- Test-/Dev-Dependencies klar dokumentieren.
- Umgang mit Bot-/Quota-Ausfällen definieren (Fallback-Prozess).

**Akzeptanzkriterien**
- PR-Template enthält Risiko- und Transparenz-Checks.
- CI läuft ohne implizite Runner-Annahmen.

---

## Definition of Done (für jedes Ticket)

- Code + Tests + Dokumentation konsistent.
- Kein stilles Fallback, das Semantik ändert.
- Relevante Regressionstests vorhanden und grün.
