> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# [P1] Activate setup-type weights in global ranking (breakout: 1.0 / pullback: 0.9 / reversal: 0.8)

> `2026-03-13__P1__activate-global-ranking-setup-weights.md`

---

## Ticket-Autor Checkliste (No-Guesswork)

### A) Defaults / Config-Semantik
- [x] **Kein raw-dict Default drift:** Gewichte werden aus dem kanonischen Pfad `setup_weights_by_category` gelesen (nach Umbenennung von `setup_weights_by_category_reserved_for_future`). **Kein neuer `global_ranking.*`-Ast in config.yml** — Variante A: Gewichte bleiben an der bestehenden kanonischen Stelle. Fehlender Key → Default `1.0`, kein Fehler.
- [x] **Missing vs Invalid getrennt:**
  - Key fehlt → Default `1.0` (kein Penalty auf unbekannte Typen)
  - Key vorhanden, Wert ungültig (nicht-numerisch, NaN, ≤ 0) → klarer Fehler
  - Key vorhanden, Wert gültig → wird angewendet
- [x] **Keine silent fallbacks:** Default `1.0` bei missing ist explizit dokumentiert und getestet.

### B) Nullability / Schema / Output
- [x] `global_score` bleibt nicht-nullable. Semantik ändert sich: `global_score = final_score × weight` statt `= final_score`.
- [x] `setup_weight` im Output-Row spiegelt das tatsächlich angewendete Gewicht wider (bisher immer hardcoded `1.0`).
- [x] Kein `bool()`-Coercion: Gewichtswerte als `float` behandelt.

### C) Edgecases
- [x] **Unbekannter setup_type:** Lookup findet keinen Eintrag → Default `1.0`, kein Fehler.
- [x] **Bestehender Test bricht bewusst:** `test_global_top20_prefers_higher_final_score_over_weighted_setup_type` prüft aktuell dass reversal(99) > breakout(90) gewinnt. Nach Aktivierung: reversal×0.8=79.2 < breakout×1.0=90.0 → Breakout gewinnt. Test muss explizit umgekehrt werden — kein silent Skip.
- [x] **`confluence` / `valid_setups` unverändert:** beschreiben Anzahl Setup-Typen pro Coin, unabhängig von Gewichtung.

### D) Tests
- [x] Missing-weight-key → Default 1.0, kein Fehler
- [x] Breakout (score=50) schlägt Reversal (score=60): 50×1.0=50 > 60×0.8=48
- [x] `setup_weight` im Output-Row = tatsächlich angewendetes Gewicht
- [x] Determinismus: identische Inputs → identischer `global_score`
- [x] Bestehender Test `test_global_top20_prefers_higher_final_score_over_weighted_setup_type` explizit angepasst

---

## Preflight-Checkliste (anwendbare Punkte)

**1. Referenz- und Scope-Check**
- [x] Aktuelle alleinige Referenz: `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- [x] Scope: genau 1 PR — `global_ranking.py` + Canonical Doc + Tests
- [x] Keine benachbarten PRs werden mitgezogen

**2. Canonical-Collision-Check**
- [x] `setup_weights_active: false` → `true` ist eine explizit vorgesehene Canonical-Änderung, keine zweite Wahrheit
- [x] `setup_weights_by_category_reserved_for_future` → aktiver Block, muss im Canonical Doc reflektiert werden
- [x] `setup_id_to_weight_category_active` enthält aktuell nur Breakout-IDs. Pullback und Reversal haben dort keinen Eintrag → Lookup muss `setup_type` als direkten Fallback verwenden

**11. Repo-Reality-Check**
- [x] `scanner/pipeline/global_ranking.py` existiert. Zeile `weighted = setup_score` ist der einzige Code-Fix-Point.
- [x] Der Code liest `setup_weights_active` aktuell **nicht aus** — die Gewichtungslogik ist vollständig unimplementiert. Ein Config-Change allein würde nichts bewirken.
- [x] `tests/test_t11_global_ranking.py` existiert, hat relevante Tests die angepasst werden müssen
- [x] Golden fixture `tests/golden/fixtures/global_ranking_t83_snapshots.json` referenziert bereits `"setup_weights": {"breakout": 1.0, "pullback": 0.9, "reversal": 0.8}` — konsistent mit diesem Ticket

**14. Test-Schärfe**
- [x] Konkreter Gewichtungs-Test: breakout×1.0 schlägt reversal×0.8 bei passenden Scores
- [x] Konkreter Missing-Key-Test: unbekannter setup_type → Default 1.0
- [x] Konkreter Invalid-Value-Test: Gewicht ≤ 0 oder NaN → klarer Fehler
- [x] Konkreter Output-Test: `setup_weight` im Row = tatsächlich angewendetes Gewicht
- [x] Konkreter Determinismus-Test: identische Inputs → identische global_scores

---

## Title
[P1] Activate setup-type weights in global ranking (breakout: 1.0 / pullback: 0.9 / reversal: 0.8)

---

## Context / Source

- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md` definiert Setup-Gewichte bereits seit Beginn, aber als Phase-1-Placeholder mit `setup_weights_active: false`.
- Der Code in `scanner/pipeline/global_ranking.py` liest diesen Flag **nicht aus**. Die relevante Zeile ist `weighted = setup_score` — hardcoded, kein Multiplikator.
- Aktuelle Runs zeigen die Folge: Breakout-Kandidaten (HYPE: final_score ~30) verlieren strukturell immer gegen Reversal-Kandidaten (TAO: final_score ~93), weil die Score-Skalen der Scorer fundamental verschieden sind und keine Kompensation aktiv ist.
- Die Gewichte (breakout_trend: 1.0, pullback: 0.9, reversal: 0.8) sind bereits kanonisch vorgesehen und im Golden Fixture referenziert.
- Dieses Ticket ist Enabling-Schritt für Ticket C (Breakout-Score-Kalibrierung): ohne aktive Gewichte wäre C operativ wirkungslos.

> Wenn die aktuelle alleinige Referenz, Canonical und bestehender Code kollidieren, gewinnen die autoritativen Vorgaben. Bei zusätzlichem Klärungsbedarf Ticket ergänzen oder User fragen statt interpretieren.

---

## Goal

Nach dieser Änderung:
- `compute_global_top20` wendet die kanonisch definierten Gewichte auf `final_score` an, bevor der globale Score-Vergleich stattfindet
- Ein Breakout mit `final_score=60` hat `global_score=60.0` (×1.0) und schlägt einen Reversal mit `final_score=70` (`global_score=56.0`, ×0.8)
- `setup_weight` im Output-Row spiegelt das tatsächlich angewendete Gewicht wider
- Canonical Doc beschreibt `setup_weights_active: true` als aktiven Zustand

---

## Scope

- `scanner/pipeline/global_ranking.py` — Gewichtungslogik implementieren
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md` — `setup_weights_active: true`, Gewichte aktivieren, pullback/reversal zu `setup_id_to_weight_category_active` ergänzen
- `docs/canonical/CHANGELOG.md`
- `tests/test_t11_global_ranking.py` — bestehende Tests anpassen + neue Tests
- `tests/golden/fixtures/global_ranking_t83_snapshots.json` — falls Fixture-Assertions betroffen

## Out of Scope

- Keine Änderungen an Scorer-Dateien (reversal.py, pullback.py, breakout_trend_1_5d.py)
- Keine Änderungen an Decision-Layer oder Tradeability-Gates
- Keine Anpassung der Score-Komponenten innerhalb der Scorer (das ist Ticket C)
- Kein Umbenennen bestehender Config-Keys
- `phase1_single_setup_type` und Dedup-Verhalten bleiben unverändert

---

## Canonical References

- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md` ← primäre Autorität
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed Change (high-level)

**Vor:**
```python
# global_ranking.py — aktueller Stand
weighted = setup_score   # hardcoded, kein Gewicht angewendet
```

**Nach:**
```python
# global_ranking.py — nach diesem Ticket
weight = _resolve_setup_weight(setup_type, setup_id, root)
weighted = setup_score * weight
```

Gewichts-Lookup-Reihenfolge (deterministisch):

`setup_type` ist der Loop-Key aus `for setup_type, entries in setup_map.items()` in `compute_global_top20`. Es ist kein Dict-Feld im Entry — es wird vom Caller kontrolliert. Zulässige Werte: exakt `"breakout"`, `"pullback"`, `"reversal"`. Codex darf diesen Wert nicht aus dem Entry-Dict lesen.

1. Direkter Lookup: `setup_weights_by_category.<setup_type>` (z.B. `"reversal": 0.8`)
2. Falls kein Treffer: `setup_id_to_weight_category_active.<setup_id>` → Kategorie → `setup_weights_by_category.<kategorie>` (für Breakout-setup_ids, die Kategorienamen tragen)
3. Fallback: `1.0`

Canonical Doc-Änderung:
- `setup_weights_active: false` → `true`
- `setup_weights_by_category_reserved_for_future` → `setup_weights_by_category` (Umbenennung, kein neuer Pfad)
- pullback und reversal zu `setup_id_to_weight_category_active` ergänzen
- **Kein neuer `global_ranking.*`-Config-Key** in config.yml — Variante A

Edge cases:
- Ungültiges Gewicht (≤ 0, NaN, non-numeric) → klarer Fehler
- Fehlender Key → Default `1.0`, kein Fehler
- Unbekannter setup_type → Default `1.0`, kein Fehler

Backward compatibility impact:
- `global_score` ändert seinen Wert für Reversal- und Pullback-Kandidaten — gewollt, muss in CHANGELOG dokumentiert werden
- Bestehende Tests mit altem Verhalten müssen explizit angepasst werden

---

## Codex Implementation Guardrails (No-Guesswork, Pflicht)

- **Feature-Flag-Guard (Pflicht):** Die Gewichtungslogik wird nur ausgeführt, wenn `phase_policy.setup_weights_active == true`. Bei `false` gilt unverändert `weight = 1.0` für alle Setup-Typen — exakt das bisherige Verhalten. Der Flag muss am Eingang von `_resolve_setup_weight` (oder im Caller) geprüft werden, nicht im inneren Lookup. Das macht späteres Deaktivieren trivial.
- **Config-Lesepfad (Variante A):** Gewichte werden aus `setup_weights_by_category` gelesen — das ist `setup_weights_by_category_reserved_for_future` nach Umbenennung. Kein neuer `global_ranking.*`-Ast in config.yml. Config-Lesemuster: `config.raw if hasattr(config, "raw") else config` — identisch zum bestehenden `_config_get`-Pattern in `global_ranking.py`.
- **Missing key ≠ invalid:** fehlender Key → Default `1.0`, kein Fehler. Ungültiger Wert (≤ 0, NaN) → klarer Fehler (ValueError oder äquivalent).
- **`setup_type`-Herkunft:** `setup_type` ist der Loop-Key aus `for setup_type, entries in setup_map.items()` — es ist kein Feld im Entry-Dict. Zulässige Werte: exakt `"breakout"`, `"pullback"`, `"reversal"`. Codex darf diesen Wert nicht aus `entry.get("setup_type")` lesen.
- **Lookup-Priorität:** direkt per `setup_type` in `setup_weights_by_category` zuerst, dann per `setup_id` → Kategorie, dann Default `1.0`. Keine andere Reihenfolge.
- **`weighted = setup_score × weight`:** nur diese eine Zeile ändert sich im Kern-Algorithmus. Alle anderen Felder (`confluence`, `valid_setups`, `best_setup_type`, Dedup-Logik, Tie-Breaker) bleiben exakt unverändert.
- **`setup_weight`-Field im Row:** `agg["setup_weight"] = weight` (tatsächliches Gewicht), nicht mehr hardcoded `1.0`.
- **Determinismus:** bei identischem Input und identischer Config müssen `global_score`, Ranking-Reihenfolge und alle Tie-Breaker identisch sein.
- **Kein Refactoring:** nur die Gewichtungslogik implementieren. Empfehlung: private Hilfsfunktion `_resolve_setup_weight(setup_type, setup_id, root) -> float`, keine weiteren Abstraktionen.
- **Umbenennung ist atomar:** `setup_weights_by_category_reserved_for_future` → `setup_weights_by_category` ist eine Umbenennung, kein Alias. Nach dem PR darf nur noch `setup_weights_by_category` existieren — kein Dual-Path, kein Fallback auf den alten Namen. Codex muss beide Vorkommen (Canonical Doc YAML-Header + Code-Lesepfad) in einem Commit anpassen.

---

## Implementation Notes

Empfohlene Hilfsfunktion:

```python
def _resolve_setup_weight(setup_type: str, setup_id: str, root: dict) -> float:
    """
    setup_type: Loop-Key aus compute_global_top20 — exakt "breakout", "pullback" oder "reversal".
                NICHT aus entry.get("setup_type") lesen.
    Missing key -> 1.0. Invalid value (<=0, NaN, non-numeric) -> ValueError.
    """
    # setup_weights_by_category ist der umbenannte setup_weights_by_category_reserved_for_future
    weights = _config_get(root, ["setup_weights_by_category"], {})

    # 1. Direkter Lookup per setup_type ("reversal" -> 0.8 etc.)
    if setup_type in weights:
        return _validate_weight(weights[setup_type], f"setup_weights_by_category.{setup_type}")

    # 2. Lookup per setup_id -> Kategorie (für Breakout-setup_ids mit Kategorienamen)
    cat_map = _config_get(root, ["setup_id_to_weight_category_active"], {})
    category = cat_map.get(setup_id)
    if category and category in weights:
        return _validate_weight(weights[category], f"setup_weights_by_category.{category}")

    return 1.0   # Default bei unbekanntem Typ


def _validate_weight(val, path: str) -> float:
    try:
        f = float(val)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid setup weight at {path}: {val!r}")
    if not math.isfinite(f) or f <= 0:
        raise ValueError(f"Invalid setup weight at {path}: must be finite and > 0, got {f}")
    return f
```

Einfügepunkt in `compute_global_top20`: nach `setup_score = float(entry.get(...))`, vor `weighted = setup_score`.

---

## Acceptance Criteria (deterministic)

1. `compute_global_top20` wendet das konfigurierte Gewicht an: `global_score = round(final_score × weight, 6)`. Das `round(..., 6)` ist das bestehende Repo-Pattern (bereits in aktuellem Code), keine neue Verhaltensänderung.
1a. Die Gewichtungslogik wird nur angewendet wenn `phase_policy.setup_weights_active == true`. Bei `false` verhält sich der Code exakt wie bisher: `weight = 1.0` für alle Setup-Typen, keine Änderung am `global_score`.
2. `setup_weight` im Output-Row enthält das tatsächlich angewendete Gewicht.
3. Breakout(`final_score=50`) schlägt Reversal(`final_score=60`) bei Gewichten `breakout=1.0, reversal=0.8` (`50.0 > 48.0`).
4. Fehlender Gewichts-Key → Default `1.0`, kein Fehler.
5. Ungültiger Gewichtswert (≤ 0, NaN, non-numeric) → klarer Fehler.
6. `confluence`, `valid_setups`, `best_setup_type` und Dedup-Logik sind unverändert.
7. Canonical Doc `GLOBAL_RANKING_TOP20.md` beschreibt `setup_weights_active: true` und listet alle drei Kategorien als aktiv.
8. Bestehender Test `test_global_top20_prefers_higher_final_score_over_weighted_setup_type` ist explizit angepasst (nicht geskippt), Assertion korrekterweise umgekehrt.
9. Identischer Input + identische Config → identische `global_score`-Werte und Ranking-Reihenfolge.

---

## Default-/Edgecase-Abdeckung (Pflicht)

- **Config Defaults (Missing key → Default):** ✅ Default `1.0` bei fehlendem Key; Test: unbekannter setup_type → weight=1.0
- **Config Invalid Value Handling:** ✅ Wert ≤ 0 oder NaN → ValueError; Test: expliziter Invalid-Value-Test
- **Nullability / kein bool()-Coercion:** ✅ `global_score` bleibt float, kein bool-Coercion
- **Not-evaluated vs failed getrennt:** ✅ N/A — keine nullable Gewichtsfelder
- **Deterministische Sortierung/Tie-Breaker:** ✅ AC #9; Test: identische Inputs → identisches Ranking

---

## Tests (required)

Unit:
- `test_setup_weight_applied_to_global_score`: breakout(50) > reversal(60) nach Gewichtung → breakout gewinnt
- `test_setup_weights_inactive_flag_bypasses_weights`: bei `setup_weights_active: false` → `global_score == final_score` für alle Setup-Typen, Gewichte aus Config werden ignoriert
- `test_setup_weight_missing_key_defaults_to_1`: unbekannter setup_type → `global_score == final_score`, `setup_weight == 1.0`
- `test_setup_weight_invalid_value_raises`: Gewicht=-1 → ValueError; Gewicht=NaN → ValueError
- `test_setup_weight_field_in_output_row`: `setup_weight` im Row = konfiguriertes Gewicht, nicht 1.0
- `test_global_score_deterministic`: zwei identische Aufrufe → identische Ergebnisse
- `test_global_top20_prefers_higher_final_score_over_weighted_setup_type` **anpassen**: reversal(99)×0.8=79.2 wird von breakout(90)×1.0=90.0 geschlagen → breakout gewinnt

Integration:
- `test_confluence_unaffected_by_weights`: Symbol in Reversal und Breakout → `confluence=2` unabhängig von Gewichtung
- Golden fixture `global_ranking_t83_snapshots.json` prüfen und ggf. Assertions anpassen

---

## Constraints / Invariants (must not change)

- Dedup-Logik (per_symbol_max_rows, prefer_setup_id_order) bleibt unverändert
- Tie-Breaker-Reihenfolge (global_score desc, setup_preference desc, symbol asc) bleibt unverändert
- `confluence` und `valid_setups` bleiben unverändert
- Kein Scorer-Code wird angefasst
- `phase1_single_setup_type` bleibt unverändert

- [ ] Preserve existing dedup semantics exactly
- [ ] Preserve existing tie-breaker order exactly
- [ ] Preserve existing config/default resolution behavior (`config.raw` pattern)

---

## Definition of Done

- [ ] Code-Änderung in `scanner/pipeline/global_ranking.py` per Acceptance Criteria
- [ ] `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md` auf `setup_weights_active: true` aktualisiert
- [ ] `docs/canonical/CHANGELOG.md` aktualisiert
- [ ] Bestehende Tests angepasst, neue Tests ergänzt, alle grün
- [ ] PR erstellt: genau **1 Ticket → 1 PR**
- [ ] Ticket nach PR-Erstellung nach `docs/legacy/tickets/` verschoben

---

## Metadata

```yaml
created_utc: "2026-03-13T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
