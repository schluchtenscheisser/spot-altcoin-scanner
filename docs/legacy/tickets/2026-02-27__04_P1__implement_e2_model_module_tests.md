> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Implement: scanner/backtest/e2_model.py gemäß Canonical MODEL_E2 + Tests

## Context / Source (optional)
- E2-ähnliche Logik existiert teilweise in scanner/pipeline/backtest_runner.py, aber Roadmap verlangt ein eigenständiges Modul und präzise Outputs.
- Canonical: docs/canonical/BACKTEST/MODEL_E2.md (inkl. Ticket 1 Änderungen)

## Goal
Implementiere ein eigenständiges E2 Modell-Modul, das exakt Canonical MODEL_E2 (inkl. Reason Codes/Precedence) umsetzt und deterministische Outputs liefert.

## Scope
- New: scanner/backtest/e2_model.py
- New: scanner/backtest/__init__.py (falls nötig)
- Tests: tests/test_e2_model.py (oder vergleichbare Struktur)

## Out of Scope
- Dataset Exporter
- Snapshot Änderungen

## Canonical References (important)
- docs/canonical/BACKTEST/MODEL_E2.md
- docs/canonical/OUTPUTS/EVALUATION_DATASET.md (nur Konsument; nicht Authority für E2)

## Proposed change (high-level)
Implementiere eine API (fest):
- `evaluate_e2_candidate(...) -> dict` (oder dataclass), mit Feldern:
  - reason (string)
  - t_trigger_date (YYYY-MM-DD | null)
  - t_trigger_day_offset (int | null)
  - entry_price (float | null)
  - hit_10 (bool | null)
  - hit_20 (bool | null)
  - hits (dict[str,bool] | null)
  - mfe_pct (float | null)
  - mae_pct (float | null)

Input (fest, minimal):
- t0_date (YYYY-MM-DD)
- setup_type (breakout|pullback|reversal)
- trade_levels (dict)
- price_series: mapping YYYY-MM-DD -> {close, high, low} (numerisch oder None)
- params: T_trigger_max, T_hold, thresholds_pct list

Rules:
- Trigger-Suche tolerant gegen fehlende Tage; Hold-Window strict (vollständige Abdeckung erforderlich).
- Reason Precedence strikt gemäß Canonical.
- No lookahead, closed-candle-only.

## Acceptance Criteria (deterministic)
1) Modul existiert unter scanner/backtest/e2_model.py mit stabiler, dokumentierter API.
2) Reason Codes/Precedence exakt wie Canonical.
3) thresholds_pct support: hits-map erzeugt für alle thresholds; hit_10/hit_20 immer vorhanden.
4) Hold-Window strict: fehlender high/low an irgendeinem Tag => reason=insufficient_forward_history (sofern nicht höhere precedence).
5) Determinismus: keine iteration über dict ohne sorting; Datumsiteration ist stets sortiert/kalenderbasiert.
6) Unit Tests decken mindestens ab:
   - no_trigger case
   - ok + hit_10/hit_20 true/false
   - missing_trade_levels und invalid_trade_levels je setup_type
   - missing_price_series (keine close values im Suchfenster)
   - insufficient_forward_history (fehlender day im hold window)

## Tests (required if logic changes)
- Unit: tests/test_e2_model.py
- Golden fixtures: minimal synthetic price_series dicts mit klaren expected outcomes.

## Constraints / Invariants (must not change)
- No lookahead
- Closed-candle-only
- Stable ordering

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Implementiert + Tests grün (pytest -q)
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR nach docs/legacy/tickets/ verschoben

---
## Metadata (optional)
```yaml
created_utc: "2026-02-27T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
