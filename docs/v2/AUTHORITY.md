# AUTHORITY – Dokument-Hierarchie & Quelle der Wahrheit

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Ziel
Diese Datei verhindert widersprüchliche “Wahrheiten” in der Doku. Für Codex gilt: **immer deterministisch**, keine Interpretation.

## Canonical v2 Suite (Soll-Zustand)
Diese Dateien sind die **Single Source of Truth** für Anforderungen, Definitionen und Implementationsgrenzen:

- `docs/v2/10_MASTER_PLAN.md`
- `docs/v2/15_PRODUKTANFORDERUNGEN.md`
- `docs/v2/20_FEATURE_SPEC.md`
- `docs/v2/30_IMPLEMENTATION_TICKETS.md`
- `docs/v2/40_TEST_FIXTURES_VALIDATION.md`
- `docs/v2/50_DATA_SOURCES.md`

## Operative Auto-Dokumente (Ist-Zustand, auto-updated)
Diese Dateien bleiben **unter `docs/`**, werden per GitHub Actions aktualisiert und dürfen **nicht** manuell editiert werden:
- `docs/code_map.md` (Code-Struktur, Module, Pfade)
- `docs/GPT_SNAPSHOT.md` (aktueller Lauf-/Betriebszustand)

Diese Auto-Dokumente sind **Referenz/Status**, aber **nicht** die Requirements-Quelle.

## Legacy Doku (nur Kontext)
Alle übrigen Docs (README, alte spec/context Dateien etc.) sind Kontext. Wenn Legacy v2 widerspricht, gilt **v2**.

## Precedence (bei Widerspruch)
1) `20_FEATURE_SPEC`  
2) `30_IMPLEMENTATION_TICKETS`  
3) `15_PRODUKTANFORDERUNGEN`  
4) `10_MASTER_PLAN`  
5) Auto-Dokumente (`code_map`, `GPT_SNAPSHOT`) als Ist-Referenz  
6) Legacy Kontext

## Änderungsprozess (drift-frei)
- Fachliche Änderung → zuerst `20_FEATURE_SPEC.md`, dann ggf. Tickets/Tests.
- Schema-/Report-Änderung → `schema_version` bump + Eintrag in `docs/SCHEMA_CHANGES.md`.
- Danach implementieren + Tests grün + Auto-Dokumente aktualisieren lassen.
