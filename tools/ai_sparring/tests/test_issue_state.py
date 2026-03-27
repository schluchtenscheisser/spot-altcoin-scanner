from tools.ai_sparring.issue_state import PointerState, decode_pointer, encode_pointer, latest_valid_pointer_comment


def _state(status: str = "awaiting_continue") -> PointerState:
    return PointerState(
        state_version=1,
        session_id="issue-12",
        issue_number=12,
        status=status,
        rounds_requested=3,
        rounds_completed=1,
        current_focus="",
        latest_run_id=77,
        latest_artifact_name="ai-sparring-issue-12-r1",
    )


def test_pointer_payload_roundtrip_base64_contract() -> None:
    encoded = encode_pointer(_state())
    decoded = decode_pointer(encoded)
    assert decoded == _state()


def test_latest_valid_pointer_comment_is_selected_deterministically() -> None:
    comments = [
        {"id": 10, "body": "ignore"},
        {"id": 11, "body": encode_pointer(_state())},
        {"id": 12, "body": encode_pointer(_state(status="completed"))},
    ]
    latest = latest_valid_pointer_comment(comments)
    assert latest is not None
    assert latest.status == "completed"
