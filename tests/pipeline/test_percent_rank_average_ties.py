from scanner.pipeline.cross_section import percent_rank_average_ties


def test_percent_rank_average_ties_returns_expected_values_for_ties_and_bounds():
    values = [10.0, 10.0, 20.0, 30.0, 30.0]

    out = percent_rank_average_ties(values)

    assert len(out) == len(values)
    assert out[0] == out[1]
    assert out[3] == out[4]
    assert out == [12.5, 12.5, 50.0, 87.5, 87.5]
    assert all(0.0 <= score <= 100.0 for score in out)


def test_percent_rank_average_ties_is_monotonic_for_unique_values():
    values = [2.0, 4.0, 6.0, 8.0]

    out = percent_rank_average_ties(values)

    assert out == [0.0, 33.33333333333333, 66.66666666666666, 100.0]
    assert all(out[i] < out[i + 1] for i in range(len(out) - 1))
    assert all(0.0 <= score <= 100.0 for score in out)
