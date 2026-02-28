> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## 2026-02-27__03_P1__gpt_snapshot_canonical_include_list_fix.md

### Title
[P1] Docs: Canonical Scoring Contracts vollständig in GPT Snapshot Include-List aufnehmen

### Context / Problem
Die neue Canonical Include-List enthält nicht alle Scoring Contracts, die in `docs/canonical/INDEX.md` definiert sind. Dadurch fehlen Regeln (z. B. setup validity, discovery semantics) im auto-generierten `docs/GPT_SNAPSHOT.md`. fileciteturn1file0

### Goal
Stelle sicher, dass alle Canonical Scoring Contracts, die für korrektes Verständnis von Validity/Discovery/Ranking relevant sind, in der Include-List enthalten sind, damit GPT_SNAPSHOT modell-konsistent bleibt.

### Scope
- Die Datei/Mechanik, die die GPT_SNAPSHOT Include-List definiert (z. B. docs/canonical/AUTHORITY.md oder ein include yaml/md; je nach Repo-Stand)
- docs/canonical/INDEX.md (als Authority)
- (Optional) tests/… falls es bereits Snapshot-generation Tests gibt

### Out of Scope
- Änderung der Scoring-Logik
- Dataset/Backtest Code

### Implementation Requirements
- Include-Liste muss mindestens zusätzlich enthalten:
  - `SETUP_VALIDITY_RULES.md`
  - `DISCOVERY_TAG.md`
  - plus alle weiteren scoring-relevanten docs aus `docs/canonical/INDEX.md`, sofern sie Teil des Scoring Contracts sind.
- Wenn es ein Skript gibt, das GPT_SNAPSHOT generiert: ggf. Update + Regression-Test, dass die Liste nicht schrumpft.

### Acceptance Criteria
- Nach Regeneration enthält `docs/GPT_SNAPSHOT.md` die oben genannten Contracts.
- Keine Canonical-Regeln werden “versehentlich” aus Model-Kontext entfernt.

### Definition of Done
- [ ] Docs/Include list updated
- [ ] (falls vorhanden) generation check/test
- [ ] 1 PR
