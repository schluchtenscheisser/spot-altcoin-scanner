# FEAT_PERCENT_RANK — Cross-Section Normalization (Canonical)

## Machine Header (YAML)
```yaml
id: FEAT_PERCENT_RANK
status: canonical
type: cross_section_rank
population_definition: "eligible universe after hard gates with non-NaN feature value"
output_range: [0.0, 100.0]
tie_handling: average_rank
equality: ieee754_exact
rounding_before_compare: none
formula:
  rank01: "(count_less + 0.5*count_equal) / N"
  percent_rank: "100 * rank01"
```

## Purpose
`percent_rank` normalizes feature values across the eligible universe (not shortlist) for cross-sectional gating/scoring.

## Population (canonical)
- Population = all candidates **after hard gates** that have a valid (non-NaN) feature value.
- Shortlist membership must not affect the population.

## Tie handling (canonical, average-rank)
For current value `x` and population `P` (N elements):
- `count_less  = |{p in P : p < x}|`
- `count_equal = |{p in P : p == x}|`
- `rank01 = (count_less + 0.5*count_equal) / N`  (range 0..1)
- `percent_rank = 100 * rank01` (range 0..100)

## Equality rule (canonical)
- Equality is **exact IEEE-754 float equality** on the computed values.
- No rounding/quantization is applied before equality comparisons.

## NaN policy (canonical)
- NaNs are excluded from the population.
- If `x` is NaN, percent_rank is NaN.

## Determinism
- Stable ordering is required for iteration, but the formula itself is order-independent.
