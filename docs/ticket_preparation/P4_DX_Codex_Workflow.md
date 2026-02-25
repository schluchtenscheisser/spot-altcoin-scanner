# P4 — Developer Experience (DX) für Codex + Regression Safety

Diese Tickets sind unabhängig von den anderen Batches, aber helfen massiv, dass Codex Änderungen korrekt und sicher umsetzt.

---

## P4-01 — Codex Coding Contract (Repo-spezifische Do/Don’t Regeln)

### Goal
Dokumentiere verbindliche Repo-Konventionen, damit Codex Änderungen korrekt implementiert.

### Scope
- **Neu:** `docs/dev_coding_contract_for_codex.md`

### Must Include
- Canonical Docs: Source of Truth (und Ausnahmen)
- Determinismus-Regeln (Sort/Tie-break, keine Randomness)
- Closed-candle-only policy
- Schema-Versionierung
- Testpflicht je Änderungstyp
- Keine stillen Behavior-Changes (Deviations dokumentieren)

### Acceptance Criteria
1. Dokument ist konkret, repo-spezifisch, checklistenartig.
2. Verlinkung aus `README.md` oder `docs/dev_guide.md`.

---

## P4-02 — GitHub Issue/PR Templates (codex-optimiert)

### Goal
Templates einführen, die strukturierte Specs erzwingen.

### Scope
- **Neu:** `.github/ISSUE_TEMPLATE/feature_request.yml`
- **Neu:** `.github/ISSUE_TEMPLATE/bug_report.yml`
- **Neu:** `.github/pull_request_template.md`

### Template Fields (Minimum)
- Goal / Scope / Out of Scope
- Canonical references
- Acceptance criteria
- Test plan
- Example input/output
- Schema impact (yes/no)

### Acceptance Criteria
1. Templates sind aktiv und in GitHub sichtbar.
2. PR Template fordert Canonical-Impact + Testplan explizit.

---

## P4-03 — Golden Fixtures (deterministische Regressionstests)

### Goal
Mini-Fixtures + erwartete Outputs bereitstellen, um deterministische Pipeline-Regressions zu erkennen.

### Scope
- **Neu:** `tests/fixtures/golden/`
- **Neu:** `tests/integration/test_pipeline_golden_small.py`

### Acceptance Criteria
1. Mindestens ein Fixture läuft ohne externe APIs.
2. Erwartete Outputs prüfen Ranking-Reihenfolge + Schlüssel-Felder.
3. Test schlägt zuverlässig bei Sort/Tie-break Regressionen fehl.
