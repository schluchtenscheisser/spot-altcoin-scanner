> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## 2026-02-27__01_P0__e2_spec_and_impl_corrections.md

### Title
[P0] E2: Spec/Impl-Korrekturen (invalid_entry_price gating, nullable hits, param aliases, thresholds guard)

### Context / Problem
Codex meldet mehrere E2-bezogene Korrektheitsthemen:
- `invalid_entry_price` macht `no_trigger` unerreichbar, wenn entry_price bei no-trigger erwartungsgemäß `null` ist. fileciteturn1file0
- `hit_*`/`hits` müssen für nicht evaluierbare Fälle (z. B. insufficient forward history) **undefiniert/null** sein, sonst werden Labels verfälscht. fileciteturn1file0
- E2 akzeptiert nicht die im Repo üblichen Config-Keys (`t_hold`, `t_trigger_max` etc.) und fällt still auf Defaults zurück. fileciteturn1file0
- thresholds parsing ist brittly bei `null` / non-iterable input. fileciteturn1file0

### Goal
1) Canonical E2 Regeln so präzisieren, dass `no_trigger` korrekt bleibt und Hits in unevaluable Fällen nicht erzwungen werden.  
2) `scanner/backtest/e2_model.py` so anpassen, dass:
   - param aliases unterstützt werden (ohne silent fallback),
   - thresholds robust sind,
   - hit-Felder in unevaluable Fällen `None` bleiben.

### Scope
- docs/canonical/BACKTEST/MODEL_E2.md
- scanner/backtest/e2_model.py
- tests/test_e2_model.py (erweitern)

### Out of Scope
- Dataset Exporter (separates Ticket)
- Snapshot/backfill Tools (separates Ticket)

### Required Canonical Updates
1) **invalid_entry_price gating**
   - `invalid_entry_price` darf **nur** evaluiert werden, wenn `t_trigger` gefunden wurde (also wenn ein entry überhaupt existiert).
   - Falls kein Trigger gefunden wurde → reason bleibt `no_trigger` (sofern keine höhere precedence greift).

2) **Nullable Hits**
   - `hit_10`, `hit_20`, `hits`, `mfe_pct`, `mae_pct` sind **nullable**:
     - bei `reason in {insufficient_forward_history, missing_price_series, missing_trade_levels, invalid_trade_levels, invalid_entry_price, no_trigger}` → **alle** Outcome-Felder außer `reason` und Trigger/Entry-Feldern sind `null` (bzw. nur die sinnvoll vorhandenen Felder).
   - Bei `reason=ok` sind `hit_10`, `hit_20`, `hits` booleans (nicht null).

3) **Parameter-Namen (Aliases)**
   - Canonical erlaubt folgende Keys (alle äquivalent):
     - `T_trigger_max` **oder** `t_trigger_max`
     - `T_hold` **oder** `t_hold`
   - Optional (falls bereits in Config vorhanden): `*_days` Varianten ebenfalls akzeptieren (nur wenn im Repo existent; sonst weglassen).

4) **thresholds_pct Parsing**
   - Wenn thresholds_pct fehlt oder `null` ist → Defaults verwenden.
   - Wenn thresholds_pct nicht iterierbar ist → klarer ValueError mit Hinweis (keine TypeError).

### Implementation Requirements (No-Guesswork)
- In `e2_model._resolve_thresholds(thresholds_pct)`:
  - `None` → Defaults
  - list/tuple/set → normalize to sorted unique floats
  - scalar (int/float/str) → ValueError (“thresholds_pct must be list-like or null”)
- In `evaluate_e2_candidate`:
  - Wenn `reason != ok` → hit-Felder **nicht** zu bool coercen; `None` bleibt `None`.
  - `invalid_entry_price` nur prüfen, wenn Trigger existiert.

### Acceptance Criteria
- Canonical Doc enthält die oben genannten Normen (gating + nullability + aliases + thresholds rules).
- Unit tests:
  - `no_trigger` bleibt erreichbar (nicht als invalid_entry_price klassifiziert).
  - `insufficient_forward_history` → `hit_10 is None`, `hits is None` (nicht False).
  - Param-Aliases wirken: Input mit `t_hold=7` verändert Window tatsächlich.
  - thresholds_pct=None führt nicht zu Exception.

### Definition of Done
- [ ] Docs + Code + Tests umgesetzt
- [ ] pytest -q grün
- [ ] 1 PR für dieses Ticket
