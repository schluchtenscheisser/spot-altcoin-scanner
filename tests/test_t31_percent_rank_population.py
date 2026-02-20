from scanner.pipeline.cross_section import percent_rank_average_ties


def test_percent_rank_average_ties_uses_sorted_population_not_input_order() -> None:
    values = [100.0, 10.0, 10.0, 1_000.0]

    out = percent_rank_average_ties(values)

    assert out == [66.66666666666666, 16.666666666666664, 16.666666666666664, 100.0]


def test_percent_rank_population_differs_from_shortlist_local_rerank() -> None:
    full_universe = [100.0, 1_000.0, 10_000.0, 100_000.0]
    shortlisted_subset = [10_000.0, 100_000.0]

    full_scores = percent_rank_average_ties(full_universe)
    subset_scores = percent_rank_average_ties(shortlisted_subset)

    # In full population, 10_000 is 66.66... percentile (3rd of 4);
    # in subset-only rerank, it would incorrectly collapse to 0.
    assert full_scores[2] == 66.66666666666666
    assert subset_scores[0] == 0.0
