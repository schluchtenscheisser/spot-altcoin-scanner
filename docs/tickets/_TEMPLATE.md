# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

## Implementation Notes
### Ticket-Autor Checkliste (No-Guesswork, Pflicht bei Code-Tickets)

> Ziel: Codex soll nicht interpretieren müssen. Deshalb müssen Defaults, Missing-Keys, Nullability und “nicht evaluiert” vs “evaluiert aber fehlgeschlagen” explizit im Ticket stehen und getestet werden.

#### A) Defaults / Config-Semantik (Pflicht, wenn Config gelesen/validiert wird)
- [ ] **Kein raw-dict Default drift:** Wenn dieses Ticket Config-Werte liest/validiert, muss es **dieselben Defaults** verwenden wie `ScannerConfig` (oder die zentrale Config-Accessor-Logik).  
      **Regel:** *fehlender Key ≠ invalid* — Missing muss entweder Default sein oder explizit als Failure spezifiziert sein.
- [ ] **Missing vs Invalid getrennt:** Für jeden geprüften Config-Key ist das Verhalten für:
  - (1) Key fehlt
  - (2) Key vorhanden aber ungültig
  - (3) Key vorhanden und gültig  
  explizit beschrieben.
- [ ] **Keine “silent fallbacks”:** Wenn Fallbacks erlaubt sind, sind sie explizit dokumentiert + getestet. Andernfalls: bei ungültigen Werten klarer Fehler.

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [ ] **Nullable Felder explizit:** Für jedes Output-Feld ist klar definiert, wann es `null` sein darf/muss (z. B. “unevaluable → null, nicht False erzwingen”).
- [ ] **Kein bool()-Coercion:** Es darf kein implizites `bool(x)` oder “falsy → False” geben, wenn `null` semantisch wichtig ist.

#### C) Edgecases, die oft übersehen werden (Pflicht, wenn relevant)
- [ ] **Nicht evaluiert ≠ evaluiert aber fail:** z. B. “nicht gefetched (Budget)” vs “gefetched aber malformed/outage”.
- [ ] **Namespace/Kollisionen:** Wenn IDs/Dateinamen aus Zeitstempeln abgeleitet werden: Kollisionen bei gleicher Minute/Sekunde sind adressiert.
- [ ] **Strict/Preflight Atomizität:** Wenn `--strict-*` existiert: Preflight prüft alles *vor* Writes, und Failure hinterlässt **0 Partial Writes**.

#### D) Tests (Pflicht bei Logikänderungen)
- [ ] Mindestens 1 Test: **Missing key → Default greift** (oder bewusstes Fail, wenn so spezifiziert)
- [ ] Mindestens 1 Test: **Invalid value → klarer Fehler/Reason**
- [ ] Mindestens 1 Test: **Edgecase**, der im Ticket neu geregelt wird (z. B. “not fetched vs fetched fail”, “strict preflight atomic”)

---

## Title
[P?] Kurz, konkret, verifizierbar

## Context / Source (optional)
- Why is this change needed?
- Links to prior analysis, runs, or legacy context (if any)

## Goal
Was soll nach der Änderung möglich/anders sein?

## Scope
Welche Module/Dateien dürfen geändert werden? (Allowlist, optional but helpful)
- ...

## Out of Scope
Was explizit nicht?
- ...

## Canonical References (important)
List the canonical documents that define/are affected by this change.
(Do not link to legacy as authority.)

- docs/canonical/...
- docs/canonical/...

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary):
- Before:
- After:
- Edge cases:
- Backward compatibility impact:

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

> Diese Sektion ist eine **Ausführungsanweisung** für Codex. Wenn hier etwas nicht eindeutig ist, muss das Ticket angepasst werden (kein Raten).

- **Config/Defaults:** Wenn Config-Werte gelesen/validiert werden: **ScannerConfig-Defaults** verwenden (oder zentrale Accessors). *Missing key ≠ invalid*, außer ausdrücklich so spezifiziert.
- **Nullability:** Keine implizite `bool(...)`-Coercion für Felder, die `null` sein dürfen/müssen. `None` bleibt `null`.
- **Strict/Preflight:** Wenn `--strict-*` existiert: Preflight vor allen Writes; bei Failure **0 Partial Writes** (atomar).
- **Not-evaluated vs failed:** “nicht evaluiert” (z. B. Budget/Not fetched) ist strikt getrennt von “evaluiert aber fail” (z. B. malformed/outage).
- **Determinismus:** stabile Sortierung, klare Tie-breaker, keine zufälligen Suffixe ohne Spec.

## Implementation Notes (optional but useful)
- Dataflow / pipeline stage impacts
- Determinism (sorting, tie-breaks, NaN policies, closed-candle/no-lookahead)
- Performance / budgets (Top-K, API calls)
- Output/schema impacts (new fields, removed fields)

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.
1) ...
2) ...
3) ...

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria/Test(s).
> Jeder ❌ muss entweder “nicht relevant” sein oder als Follow-up Ticket eingeplant werden.

- **Config Defaults (Missing key → Default):** ✅/❌ (AC: #__ ; Test: __)
- **Config Invalid Value Handling:** ✅/❌ (AC: #__ ; Test: __)
- **Nullability / kein bool()-Coercion:** ✅/❌ (AC: #__ ; Test: __)
- **Not-evaluated vs failed getrennt:** ✅/❌ (AC: #__ ; Test: __)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅/❌ (AC: #__ ; Test: __)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅/❌ (AC: #__ ; Test: __)
- **Deterministische Sortierung/Tie-breaker:** ✅/❌ (AC: #__ ; Test: __)
> Hinweis: Bei Tickets, wo ein Punkt nicht relevant ist: markiere ✅ und schreibe “N/A” statt AC/Test (damit klar ist, dass es geprüft wurde, aber nicht gilt), z. B.
✅ (N/A – Ticket liest keine Config)

## Tests (required if logic changes)
- Unit:
- Integration:
- Golden fixture / verification:
  - If scoring/threshold/curve changes: update `docs/canonical/VERIFICATION_FOR_AI.md`

## Constraints / Invariants (must not change)
Examples:
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges clamp to 0..100
- Timestamp unit = ms

- [ ] ...
- [ ] ...

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` (if logic/params/outputs changed)
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if any scoring/threshold/curve behavior changed
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-25T22:42:57Z"
priority: P2
type: feature|bugfix|refactor|docs
owner: codex
related_issues: []
```
