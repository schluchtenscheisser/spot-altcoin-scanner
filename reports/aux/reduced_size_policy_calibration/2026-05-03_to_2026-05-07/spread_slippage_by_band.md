# Spread and Slippage by Band

## Spread

| scenario | class | derivable | missing | min | median | p75 | p90 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_20k | full | 8 | 0 | 0.0358487 | 0.0652194 | 0.136466 | 0.321725 | 0.326229 |
| current_20k | reduced_75 | 17 | 0 | 0.0146488 | 0.046436 | 0.0546001 | 0.0894606 | 0.149835 |
| current_20k | reduced_50 | 17 | 0 | 0.010657 | 0.0585309 | 0.0885347 | 0.112069 | 0.115009 |
| current_20k | reduced_25 | 34 | 0 | 0.00159994 | 0.0508369 | 0.0867886 | 0.170223 | 0.293643 |
| current_20k | observe_only | 384 | 0 | 1.24335e-05 | 0.114979 | 0.222507 | 0.499305 | 1.11374 |
| current_20k | not_evaluable | 0 | 0 | null | null | null | null | null |
| target_10k | full | 42 | 0 | 0.010657 | 0.0531775 | 0.0776956 | 0.112893 | 0.326229 |
| target_10k | reduced_75 | 11 | 0 | 0.00159994 | 0.0507357 | 0.0622841 | 0.0735565 | 0.110681 |
| target_10k | reduced_50 | 23 | 0 | 0.0100669 | 0.0518269 | 0.116506 | 0.188179 | 0.293643 |
| target_10k | reduced_25 | 48 | 0 | 0.0159783 | 0.0948257 | 0.205332 | 0.458412 | 1.11374 |
| target_10k | observe_only | 336 | 0 | 1.24335e-05 | 0.119162 | 0.223689 | 0.499672 | 0.931743 |
| target_10k | not_evaluable | 0 | 0 | null | null | null | null | null |

## Spread Threshold Sensitivity

| scenario | spread_threshold_pct | eligible_remaining_derivable_spread_only |
| --- | --- | --- |
| current_20k | 0.05 | 34 |
| current_20k | 0.1 | 61 |
| current_20k | 0.15 | 70 |
| current_20k | 0.2 | 72 |
| current_20k | 0.3 | 74 |
| target_10k | 0.05 | 46 |
| target_10k | 0.1 | 87 |
| target_10k | 0.15 | 102 |
| target_10k | 0.2 | 108 |
| target_10k | 0.3 | 115 |

## Slippage

| scenario | class | derivable | missing | derivable_share | median | p75 |
| --- | --- | --- | --- | --- | --- | --- |
| current_20k | full | 8 | 0 | 1 | 15.9782 | 16.7633 |
| current_20k | reduced_75 | 17 | 0 | 1 | 9.35377 | 13.7849 |
| current_20k | reduced_50 | 17 | 0 | 1 | 14.3592 | 17.4396 |
| current_20k | reduced_25 | 34 | 0 | 1 | 18.4636 | 30.2524 |
| current_20k | observe_only | 165 | 219 | 0.429688 | 71.6296 | 139.587 |
| current_20k | not_evaluable | 0 | 0 | null | null | null |
| target_10k | full | 42 | 0 | 1 | 12.1371 | 16.2401 |
| target_10k | reduced_75 | 11 | 0 | 1 | 18.0022 | 27.3602 |
| target_10k | reduced_50 | 23 | 0 | 1 | 19.9211 | 31.7911 |
| target_10k | reduced_25 | 48 | 0 | 1 | 31.4325 | 40.5777 |
| target_10k | observe_only | 117 | 219 | 0.348214 | 110.56 | 166.766 |
| target_10k | not_evaluable | 0 | 0 | null | null | null |

Slippage data is only partially available. T28 does not justify loosening slippage thresholds for reduced-size candidates.
