# FEAT_PERCENT_RANK — Cross-Section Normalization (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_PERCENT_RANK
status: canonical
population_definition: "eligible universe after hard gates with non-NaN feature value"
output_range: [0.0, 1.0]
tie_handling: average_rank
formula:
  rank: "(count_less + 0.5*count_equal) / N"
```

## Purpose
`percent_rank` normalisiert Featurewerte über die relevante Population (Universe), um Setup-Regeln mit robusten Schwellen zu ermöglichen.

## Population (canonical)
- Population = alle Kandidaten **nach Hard Gates**, die für das jeweilige Feature einen gültigen Wert besitzen (nicht NaN).
- Nicht die “shortlist”.

## Tie handling (canonical)
Für aktuellen Wert `x` und Population `P` (N Elemente):
- `count_less = |{p in P : p < x}|`
- `count_equal = |{p in P : p == x}|`
- `rank = (count_less + 0.5*count_equal) / N`  (Range: 0..1)

## Determinismus
- “Equal” ist numerisch equality gemäß Implementierung; falls rounding/quantization genutzt wird, muss es explizit dokumentiert werden.
