# AUTHORITY — Dokument-Hierarchie & Quelle der Wahrheit (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_AUTHORITY
status: canonical
canonical_root: docs/canonical
autodocs_read_only:
  - docs/code_map.md
  - docs/GPT_SNAPSHOT.md
independence_release_fachlich_authority:
  - independence_release_gesamtkonzept_final.md
  - 7_abschnittsdateien
canonical_roles:
  active_independence_release:
    - docs/canonical/ARCHITECTURE.md
    - docs/canonical/SCOPE.md
    - docs/canonical/DATA_MODEL.md
    - docs/canonical/RUNTIME_AND_OPERATIONS.md
    - docs/canonical/REPORTS.md
    - docs/canonical/SNAPSHOTS.md
    - docs/canonical/TEST_STRATEGY.md
    - docs/canonical/MIGRATION_NOTES.md
    - docs/canonical/CHANGELOG.md
    - docs/canonical/GLOSSARY.md
    - docs/canonical/WORKFLOW_CODEX.md
  legacy_reference_only_within_canonical_path:
    - docs/canonical/PIPELINE.md
    - docs/canonical/OUTPUT_SCHEMA.md
    - docs/canonical/DECISION_LAYER.md
    - docs/canonical/DATA_SOURCES.md
    - docs/canonical/CONFIGURATION.md
    - docs/canonical/VERIFICATION_FOR_AI.md
    - docs/canonical/MAPPING.md
    - docs/canonical/RISK_MODEL.md
    - docs/canonical/BUDGET_AND_POOL_MODEL.md
    - docs/canonical/SCORING/*
    - docs/canonical/LIQUIDITY/*
    - docs/canonical/FEATURES/*
    - docs/canonical/OUTPUTS/*
    - docs/canonical/BACKTEST/*
precedence_order:
  - independence_release_gesamtkonzept_final.md + 7_abschnittsdateien
  - docs/canonical/* (role-aware: active_independence_release > legacy_reference_only)
  - docs/*
  - docs/code_map.md
  - docs/GPT_SNAPSHOT.md
  - docs/legacy/*
change_process:
  - update_canonical_docs_first
  - update_tests_and_fixtures
  - regenerate_autodocs_via_ci
```

## Ziel
Diese Datei verhindert widersprüchliche “Wahrheiten” in der Doku. Für KI-Modelle gilt: **Canonical ist deterministisch und vollständig definiert.** Wenn etwas nicht definiert ist, ist es **nicht erlaubt** (kein Interpretationsspielraum).

## Fachliche Authority für Independence-Release (primär)
Für Independence-Release ist die fachliche Primär-Authority:
- `independence_release_gesamtkonzept_final.md`
- die 7 Abschnittsdateien

Die Repo-Canonical-Dokumente unter `docs/canonical/` operationalisieren diese Authority. Sie ersetzen sie nicht.

## Canonical ist role-aware (kein flacher SoT-Bucket)
`docs/canonical/` wird **nicht** als undifferenzierter SoT-Ordner behandelt.

Es gibt zwei Rollen:
1. **active_independence_release**
   - aktive, bindende Canonical-Verträge für die aktuelle Independence-Release-Architektur.
2. **legacy_reference_only**
   - historisch nützliche Legacy-Scanner-Verträge, die aus Kompatibilitäts-/Migrationsgründen weiter im Repo liegen.
   - Diese sind **nicht** aktive Independence-Release-Anforderungen.

Pflichtregel: Wenn ein Dokument `legacy_reference_only` ist, darf es nicht als aktive Independence-Release-Quelle interpretiert werden.

## Operative Doku (unterstützend)
Dokumente unter `docs/` (außer Auto-Doks) sind unterstützend (z.B. Lauf-/Dev-Infos). Bei Widerspruch zu aktiven Canonical-Dokumenten gilt Canonical.

## Auto-Dokumente (read-only)
Diese Dateien werden per GitHub Actions aktualisiert und dürfen **nicht manuell editiert** werden:
- `docs/code_map.md` (Code-Struktur/Module/Pfade)
- `docs/GPT_SNAPSHOT.md` (aktueller Lauf-/Betriebszustand)

Auto-Dokumente sind **Status/Referenz**, aber **nicht** Requirements-Quelle.

## Legacy Doku (nur Kontext)
Alles unter `docs/legacy/` ist historischer Kontext. Bei Widerspruch gilt aktive Canonical-Authority.

## Precedence (bei Widerspruch)
1) `independence_release_gesamtkonzept_final.md` + 7 Abschnittsdateien  
2) `docs/canonical/*` mit expliziter Rollenauflösung (`active_independence_release` vor `legacy_reference_only`)  
3) `docs/*` (nicht auto-generated)  
4) `docs/code_map.md`, `docs/GPT_SNAPSHOT.md` (Status/Referenz)  
5) `docs/legacy/*` (Kontext)

## Änderungsprozess (drift-frei)
Regel: Änderungen laufen **immer** über Canonical, dann Tests/Fixtures, dann Auto-Doks.
- Fachliche Änderung → zuerst relevante Canonical-Spez anpassen
- Dann Tests/Golden Fixtures aktualisieren (Determinismus & Invariants)
- Dann Code/CI laufen lassen, Auto-Doks werden aktualisiert

## Verbotene Praktiken
- “Stille” Logikänderungen ohne Canonical Update
- Fuzzy/heuristische Interpretation in der Doku (“ungefähr”, “meistens”)
- Nicht-deterministische Regeln ohne explizite Determinismus-Sektion
- Legacy-Referenzdokumente als aktive Independence-Release-Pflicht zu behandeln
