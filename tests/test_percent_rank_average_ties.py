from scanner.pipeline.cross_section import percent_rank_average_ties


def test_percent_rank_average_ties_distinct_values_unsorted() -> None:
    values = [10.0, 30.0, 20.0]

    result = percent_rank_average_ties(values)

    assert result == [0.0, 100.0, 50.0]


def test_percent_rank_average_ties_assigns_average_rank_for_ties() -> None:
    values = [10.0, 10.0, 20.0, 20.0]

    result = percent_rank_average_ties(values)

    assert result[0] == result[1]
    assert result[2] == result[3]
    assert result == [16.666666666666664, 16.666666666666664, 83.33333333333334, 83.33333333333334]


def test_percent_rank_average_ties_is_deterministic() -> None:
    values = [10.0, 20.0, 20.0, 30.0, 10.0]

    first = percent_rank_average_ties(values)
    second = percent_rank_average_ties(values)
    third = percent_rank_average_ties(list(values))

    assert first == second == third
