> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# [P1] Upgrade GitHub Actions workflow dependencies to Node-24-compatible action versions

## Context / Source
- GitHub Actions warnt im aktuellen Daily Run am Job-Ende:
  - `Warning: Node.js 20 actions are deprecated. The following actions are running on Node.js 20 and may not work as expected: actions/checkout@v4, actions/setup-python@v5.`
- Im Repo verwenden aktuell mehrere Workflows genau diese veralteten Action-Versionen.
- Betroffene Dateien im aktuellen Repo:
  - `.github/workflows/daily.yml`
  - `.github/workflows/pr-ci.yml`
  - `.github/workflows/generate-gpt-snapshot.yml`
  - `.github/workflows/update-code-map.yml`

## Goal
Alle vorhandenen GitHub-Workflow-Dateien im Repo sollen auf die Node-24-kompatiblen offiziellen Action-Versionen angehoben werden, damit die Deprecation-Warnung verschwindet und die Workflows vor der GitHub-Umstellung robust bleiben.

## Scope
Erlaubte Änderungen nur in diesen Dateien:
- `.github/workflows/daily.yml`
- `.github/workflows/pr-ci.yml`
- `.github/workflows/generate-gpt-snapshot.yml`
- `.github/workflows/update-code-map.yml`

Optional nur falls zur Repo-Konsistenz zwingend nötig:
- keine weiteren Dateien

## Out of Scope
- Keine Änderungen an Scanner-Logik, Python-Code, Konfigurationen oder Outputs
- Keine Änderungen an Cron-Schedules
- Keine Änderungen an Workflow-Triggern
- Keine Änderungen an Job-Namen, Step-Namen, Permissions oder Secrets-Verwendung
- Kein Hinzufügen temporärer Opt-in-/Opt-out-Flags wie:
  - `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`
  - `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`
- Keine zusätzlichen Refactorings oder Cleanup-Arbeiten an Workflow-Dateien
- Keine Änderungen an Canonical-Dokumenten, sofern sich nur Action-Versionen ändern und keinerlei fachliche Logik/Parameter/Outputs betroffen sind

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/AGENTS.md`

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary):
- Before:
  - Mehrere Repo-Workflows verwenden `actions/checkout@v4` und `actions/setup-python@v5`
  - GitHub meldet dafür eine Node-20-Deprecation-Warnung
- After:
  - Alle betroffenen Workflows verwenden ausschließlich:
    - `actions/checkout@v5`
    - `actions/setup-python@v6`
- Edge cases:
  - Wenn ein Workflow bereits andere `uses:`-Einträge hat, bleiben diese unverändert
  - Wenn einzelne Workflows unterschiedliche Step-Namen haben, wird nur der Versionssuffix in `uses:` geändert, nicht die umgebende Struktur
- Backward compatibility impact:
  - Keine Änderung an Scanner-Fachlogik, Datenmodell, Report-Schema oder Pipeline-Reihenfolge
  - Nur Maintenance-Änderung an CI-/Automation-Definitionen

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Repo reality first:** Verwende die existierenden Dateien und ändere nur die konkret vorhandenen `uses:`-Zeilen in den vier Workflow-Dateien. Keine neuen Workflow-Dateien anlegen.
- **Exact replacements only:** Ersetze nur diese offiziellen Action-Versionen:
  - `actions/checkout@v4` → `actions/checkout@v5`
  - `actions/setup-python@v5` → `actions/setup-python@v6`
- **No scope creep:** Keine anderen `uses:`-Versionen, keine Umbenennungen, keine YAML-Reformatierung nur aus Stilgründen.
- **No temporary toggles:** Füge **keine** Environment-Variablen für Node-24-Opt-in/Opt-out hinzu. Ziel dieses Tickets ist die saubere Versionsanhebung, nicht ein temporärer Workaround.
- **Determinism:** Bei identischem Repo-Stand müssen nach dem PR exakt dieselben Workflow-Strukturen bestehen, abgesehen von den zwei Versions-Upgrades pro betroffenem Workflow.
- **Docs rule:** Da dieses Ticket keine fachliche Logik, keine Schwellenwerte, keine Outputs und keine Canonical-Verträge ändert, dürfen Canonical-Dokumente **nicht** angepasst werden. Im PR-Body muss ausdrücklich begründet werden: `Docs not required because: CI-only action version maintenance; no logic/params/outputs changed.`
- **One ticket, one PR:** Genau ein PR für dieses Ticket gemäß `docs/canonical/WORKFLOW_CODEX.md`.

## Implementation Notes (optional but useful)
- Diese Änderung betrifft keine Python-Implementierung, sondern nur GitHub-Workflow-YAML.
- Relevante Verifikation ist daher:
  1. statische Prüfung der vier Dateien auf die neuen `uses:`-Versionen
  2. bestehende Test-Suite weiterhin grün
- Da `ubuntu-latest` verwendet wird, sind in diesem Ticket keine zusätzlichen Runner-Migrationsschritte umzusetzen.
- Keine Änderung an `python-version: '3.12'`.

## Acceptance Criteria (deterministic)
1) In `.github/workflows/daily.yml` ist jeder Vorkommensfall von
   - `actions/checkout@v4` auf `actions/checkout@v5`
   - `actions/setup-python@v5` auf `actions/setup-python@v6`
   umgestellt.

2) In `.github/workflows/pr-ci.yml` ist jeder Vorkommensfall von
   - `actions/checkout@v4` auf `actions/checkout@v5`
   - `actions/setup-python@v5` auf `actions/setup-python@v6`
   umgestellt.

3) In `.github/workflows/generate-gpt-snapshot.yml` ist jeder Vorkommensfall von
   - `actions/checkout@v4` auf `actions/checkout@v5`
   - `actions/setup-python@v5` auf `actions/setup-python@v6`
   umgestellt.

4) In `.github/workflows/update-code-map.yml` ist jeder Vorkommensfall von
   - `actions/checkout@v4` auf `actions/checkout@v5`
   - `actions/setup-python@v5` auf `actions/setup-python@v6`
   umgestellt.

5) Im gesamten Repo verbleibt unter `.github/workflows/` kein Vorkommensfall von:
   - `actions/checkout@v4`
   - `actions/setup-python@v5`

6) Kein Workflow enthält neu hinzugefügte temporäre Node-Migrations-Flags:
   - `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`
   - `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true`

7) Job-Trigger, Schedules, Secrets, Step-Reihenfolge und Workflow-Permissions bleiben unverändert.

8) `python -m pytest -q` läuft weiterhin erfolgreich.

9) Im PR-Body steht explizit:
   - ursprünglicher Ticket-Pfad
   - Docs-Impact-Zusammenfassung
   - `Verification updated: no`
   - Begründung, dass keine Canonical-Doku geändert wurde, weil nur CI-Action-Versionen aktualisiert wurden.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria/Test(s).
> Jeder ❌ muss entweder „nicht relevant“ sein oder als Follow-up Ticket eingeplant werden.

- **Config Defaults (Missing key ⇒ Default):** ✅ (N/A – Ticket liest/ändert keine Scanner-Konfiguration; AC: #7)
- **Config Invalid Value Handling:** ✅ (N/A – Ticket führt keine neue Config-Validierung ein; AC: #7)
- **Nullability / kein bool()-Coercion:** ✅ (N/A – keine nullable Output-/Config-Felder betroffen; AC: #7)
- **Not-evaluated vs failed getrennt:** ✅ (N/A – keine Pipeline-/Statuslogik betroffen; AC: #7)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – kein Strict-/Write-Pfad im Anwendungscode betroffen; AC: #7)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A – keine neuen IDs/Artifacts/Dateinamen erzeugt; AC: #7)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (N/A – keine Ranking-/Sortierlogik betroffen; AC: #7)

## Tests (required if logic changes)
- Unit:
  - Keine neuen Python-Unit-Tests erforderlich, da keine Scanner-Logik geändert wird.
- Integration:
  - `python -m pytest -q`
- Golden fixture / verification:
  - Nicht erforderlich, da keine Scoring-/Threshold-/Output-Verhaltensänderung
- Zusätzliche Repo-Verifikation:
  - Statische Prüfung, dass unter `.github/workflows/` keine alten Versionen mehr vorkommen:
    - kein `actions/checkout@v4`
    - kein `actions/setup-python@v5`
  - Statische Prüfung, dass keine temporären Node-24-Flags neu eingeführt wurden

## Constraints / Invariants (must not change)
- Closed-candle-only: nicht relevant
- No lookahead: nicht relevant
- Deterministic ordering with stable tie-breakers: nicht relevant
- Score ranges clamp to 0..100: nicht relevant
- Timestamp unit = ms: nicht relevant

- [ ] Workflow-Trigger bleiben unverändert
- [ ] Cron in `daily.yml` bleibt unverändert
- [ ] Scanner-Commandlines und Env/Secrets bleiben unverändert
- [ ] Keine Canonical-Dokumente werden geändert
- [ ] Keine zusätzlichen Workflows oder Jobs werden eingeführt

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] No canonical docs changed because no logic/params/outputs changed
- [ ] `docs/canonical/VERIFICATION_FOR_AI.md` unchanged because not relevant
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-12T00:00:00Z"
priority: P1
type: refactor
owner: codex
related_issues: []
```
