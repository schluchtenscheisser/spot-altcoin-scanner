# PR11 — CI/Automation: Separate concurrency lock for PR CI (avoid blocking main-branch automations)

## Kurze Erläuterung
In `.github/workflows/pr-ci.yml` wird aktuell die gleiche `concurrency.group` (z.B. `pr-automation-serial`) verwendet wie bei Write-Back Automations (z.B. `gpt-snapshot`, `update-code-map`). Dadurch kann ein lang laufender PR-Testlauf Automations auf `main` komplett blockieren (unnötiger Bottleneck / DoS-Pfad). PR CI schreibt keine generierten Docs zurück und darf daher nicht mit den Write-Back Workflows serialisiert werden.

## Scope
- Nur Workflow-Dateien anpassen.
- Keine Code-Änderungen im Scanner.
- Ziel: PR CI darf parallel zu `main`-Automations laufen.

## Files to change
- `.github/workflows/pr-ci.yml` (und ggf. eine zentrale Workflow-Datei, falls Gruppen dort definiert sind)

---

## Required changes (exact)

### 1) PR CI bekommt eine eigene Concurrency-Group
In `pr-ci.yml`:
- Ersetze die aktuelle `concurrency.group: pr-automation-serial` durch eine PR-spezifische Gruppe, die **nicht** mit main-Automations geteilt wird.

Empfohlen (deterministisch, isoliert):
```yaml
concurrency:
  group: pr-ci-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

Alternative (falls PR-Nummer nicht verfügbar, z.B. workflow_dispatch):
```yaml
concurrency:
  group: pr-ci-${{ github.ref }}
  cancel-in-progress: true
```

### 2) Write-Back Automations behalten ihre eigene Serialisierung
- Keine Änderung an `gpt-snapshot` / `update-code-map` Concurrency-Gruppen in diesem PR.
- Ziel ist ausschließlich Entkopplung von PR CI.

---

## Tests / Validation
- Keine Unit-Tests. Validierung erfolgt über Workflow-Runs:
  1) Starte einen PR CI Run (oder simuliere via PR).
  2) Stelle sicher, dass parallel ein main-Workflow (z.B. Snapshot) starten kann und **nicht** wartet.

## Acceptance criteria
- PR CI verwendet **nicht** mehr die gleiche Concurrency-Group wie main Write-Back Automations.
- Main-branch automations werden nicht durch PR CI blockiert.
- Workflow YAML ist syntaktisch gültig.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
