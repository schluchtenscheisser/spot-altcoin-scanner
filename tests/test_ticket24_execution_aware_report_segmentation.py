from scanner.runners.daily import _build_execution_aware_report_payload


class _Bucket:
    def __init__(self, value: str):
        self.value = value


class _Decision:
    def __init__(self, bucket: str):
        self.decision_bucket = _Bucket(bucket)


class _Ranked:
    def __init__(self, symbol: str, bucket: str):
        self.symbol = symbol
        self.decision = _Decision(bucket)


def _diag(symbol: str, *, category: str, excluded: bool, status, attempted, execution_pass, priority_score=1.0):
    return {
        "symbol": symbol,
        "decision": {"priority_score": priority_score},
        "execution_attempted": attempted,
        "execution_status_raw": status,
        "execution_reason_raw": "r",
        "execution_pass": execution_pass,
        "universe": {
            "universe_category": category,
            "universe_category_confidence": "low",
            "universe_category_reason": "reason",
            "candidate_excluded": excluded,
            "candidate_exclusion_reason": category if excluded else None,
        },
    }


def test_execution_aware_payload_classifies_and_excludes_candidate_excluded() -> None:
    ranked = [
        _Ranked("A", "confirmed_candidates"),
        _Ranked("B", "confirmed_candidates"),
        _Ranked("C", "early_candidates"),
        _Ranked("D", "watchlist"),
        _Ranked("E", "late_monitor"),
        _Ranked("X", "confirmed_candidates"),
    ]
    diagnostics = [
        _diag("A", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=5.0),
        _diag("B", category="classic_crypto", excluded=False, status="tranche_ok", attempted=True, execution_pass=True, priority_score=4.0),
        _diag("C", category="classic_crypto", excluded=False, status="marginal", attempted=True, execution_pass=False, priority_score=3.0),
        _diag("D", category="classic_crypto", excluded=False, status="unknown", attempted=True, execution_pass=None, priority_score=2.0),
        _diag("E", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=1.0),
        _diag("X", category="stable_or_cash_proxy", excluded=True, status="direct_ok", attempted=True, execution_pass=True, priority_score=100.0),
    ]
    payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)

    assert payload["execution_aware_summary"]["total_structural_candidates"] == 5
    assert payload["execution_aware_summary"]["total_executable"] == 3
    assert payload["execution_aware_summary"]["total_unknown_execution"] == 1
    assert payload["execution_counts_by_bucket"]["confirmed_candidates"]["direct_ok"] == 1
    assert payload["execution_counts_by_bucket"]["confirmed_candidates"]["tranche_ok"] == 1
    assert payload["execution_counts_by_bucket"]["early_candidates"]["marginal"] == 1
    assert payload["execution_counts_by_bucket"]["watchlist"]["unknown_execution"] == 1
    assert [item["symbol"] for item in payload["execution_aware_candidate_segments"]["confirmed_executable"]] == ["A", "B"]
    assert payload["execution_aware_candidate_segments"]["watchlist_direct_ok"] == []
    assert [item["symbol"] for item in payload["execution_aware_candidate_segments"]["late_monitor_direct_ok"]] == ["E"]


def test_execution_aware_payload_unexpected_and_not_attempted() -> None:
    ranked = [
        _Ranked("A", "confirmed_candidates"),
        _Ranked("B", "early_candidates"),
        _Ranked("C", "confirmed_candidates"),
    ]
    diagnostics = [
        _diag("A", category="classic_crypto", excluded=False, status="marginal", attempted=True, execution_pass=True, priority_score=2.0),
        _diag("B", category="classic_crypto", excluded=False, status=None, attempted=False, execution_pass=None, priority_score=1.0),
        _diag("C", category="classic_crypto", excluded=False, status=None, attempted=True, execution_pass=None, priority_score=float("nan")),
    ]

    payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
    assert payload["execution_aware_summary"]["total_unexpected_execution_state"] == 2
    assert payload["execution_aware_summary"]["total_not_attempted"] == 1
    assert payload["execution_aware_summary"]["total_unknown_execution"] == 0
    assert [item["symbol"] for item in payload["execution_aware_candidate_segments"]["confirmed_structural"]] == ["A", "C"]
    assert [item["symbol"] for item in payload["execution_aware_candidate_segments"]["confirmed_unknown_execution"]] == []
    assert [item["symbol"] for item in payload["execution_aware_candidate_segments"]["confirmed_unexpected_execution_state"]] == ["A", "C"]


def test_contradictory_statuses_classified_as_unexpected() -> None:
    ranked = [
        _Ranked("F", "confirmed_candidates"),
        _Ranked("U", "confirmed_candidates"),
        _Ranked("D", "confirmed_candidates"),
        _Ranked("M", "confirmed_candidates"),
    ]
    diagnostics = [
        _diag("F", category="classic_crypto", excluded=False, status="fail", attempted=True, execution_pass=True),
        _diag("U", category="classic_crypto", excluded=False, status="unknown", attempted=True, execution_pass=True),
        _diag("D", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=False),
        _diag("M", category="classic_crypto", excluded=False, status="marginal", attempted=True, execution_pass=None),
    ]
    payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
    counts = payload["execution_counts_by_bucket"]["confirmed_candidates"]
    assert counts["unexpected_execution_state"] == 4
    assert counts["failed"] == 0
    assert counts["unknown_execution"] == 0
    assert counts["direct_ok"] == 0
    assert counts["marginal"] == 0
    assert counts["executable"] == 0


def test_priority_score_sanitization_in_emitted_segments() -> None:
    ranked = [
        _Ranked("NAN", "confirmed_candidates"),
        _Ranked("INF", "confirmed_candidates"),
        _Ranked("NINF", "confirmed_candidates"),
        _Ranked("ZERO", "confirmed_candidates"),
        _Ranked("POS", "confirmed_candidates"),
    ]
    diagnostics = [
        _diag("NAN", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=float("nan")),
        _diag("INF", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=float("inf")),
        _diag("NINF", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=float("-inf")),
        _diag("ZERO", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=0.0),
        _diag("POS", category="classic_crypto", excluded=False, status="direct_ok", attempted=True, execution_pass=True, priority_score=1.25),
    ]
    payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
    emitted = {item["symbol"]: item["priority_score"] for item in payload["execution_aware_candidate_segments"]["confirmed_executable"]}
    assert emitted["NAN"] is None
    assert emitted["INF"] is None
    assert emitted["NINF"] is None
    assert emitted["ZERO"] == 0.0
    assert emitted["POS"] == 1.25
