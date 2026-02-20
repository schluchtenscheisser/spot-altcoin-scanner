# PR7 — percent_rank_average_ties: Tests für ties/unsorted/deterministisch

## Kontext
Implementierung existiert: `scanner/pipeline/cross_section.py:percent_rank_average_ties()`
Sie wird in `scanner/pipeline/shortlist.py` verwendet.

## Ziel
- Explizite Unit-Tests für:
  - unsortierten Input
  - ties (gleiches value)
  - deterministische Ausgabe (stabile Reihenfolge/identisches Ergebnis)

## Nicht-Ziele
- Keine Änderung an Implementierung, außer Tests zeigen echten Bug.

## Fundstellen
- scanner/pipeline/cross_section.py
  - percent_rank_average_ties(...)
- scanner/pipeline/shortlist.py
  - Nutzung für liquidity_rank_percent

## Neue Tests (Test-first)
Neuer Testfile z. B. `tests/test_percent_rank_average_ties.py`:
- Case 1: distinct values unsorted
  - input: [("A", 10), ("B", 30), ("C", 20)] unsorted
  - assert ranks monotonic & expected mapping
- Case 2: ties
  - input: [("A", 10), ("B", 10), ("C", 20), ("D", 20)]
  - assert:
    - A und B bekommen identisches percent_rank
    - C und D identisch
    - und tie rank ist average-rank (nicht min/max)
- Case 3: determinism
  - gleiche inputs mehrfach -> exakt gleiche outputs (dict equality)

## Akzeptanzkriterien
- Tests grün
- Kein Code-Change nötig, außer Tests decken Bug auf
