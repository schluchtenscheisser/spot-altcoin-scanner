# Fail Sanity Check

fail_count: 735
fail_count_by_day: {'2026-05-03': 120, '2026-05-04': 150, '2026-05-05': 165, '2026-05-06': 171, '2026-05-07': 129}
fail_ratio_min_target_10k: 0.0
fail_ratio_median_target_10k: 0.00208084497761
fail_ratio_p75_target_10k: 0.008445559871350001
fail_ratio_max_target_10k: 0.049313791566
fail_ratio_max_current_20k: 0.024656895783
fail_count_reaching_reduced_25_current_20k: 0
fail_count_reaching_reduced_25_target_10k: 0

Based on the five T27-capable runs, fail remains out of scope for reduced-size execution and should stay hard-blocked in the T29 policy proposal. This is because no fail record reaches reduced_25 under the target 10k scenario.
