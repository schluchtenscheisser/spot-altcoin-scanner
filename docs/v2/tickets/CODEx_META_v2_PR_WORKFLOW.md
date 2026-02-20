# Codex META — v2 PR Workflow (Spot Altcoin Scanner)

## Repo-Regeln (aus docs/AGENTS.md)
- Precedence: v2 > auto-docs > legacy
- One ticket per PR
- Tests first (golden/unit), then code
- CI must pass:
  ```bash
  pip install -r requirements.txt -r requirements-dev.txt
  python -m pytest -q
  ```

## Pflichtlektüre vor Änderungen
1) docs/v2/AUTHORITY.md
2) docs/v2/20_FEATURE_SPEC.md
3) docs/v2/30_IMPLEMENTATION_TICKETS.md

## PR-Disziplin
- Jede PR implementiert exakt EIN Thema (Ticket).
- Keine opportunistischen Refactors.
- Minimalinvasiv: nur das ändern, was für das Ticket nötig ist.
- Neue Tests: Ticket-spezifisch, deterministisch, kein Netzwerk.
- Wenn Schema/Output Felder geändert werden: `schema_version` bump + docs/SCHEMA_CHANGES.md aktualisieren.

## Logging/Fehlerhandling
- Hard fail nur wenn unvermeidbar.
- Bei recoverable Problemen: warn-level log + weiterlaufen.

## Review-Checkliste
- Neue Tests vorhanden & grün
- Bestehende Tests grün
- Keine ungewollten Formatänderungen in JSON-Strukturen
