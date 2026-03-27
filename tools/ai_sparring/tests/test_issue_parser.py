import pytest

from tools.ai_sparring.issue_parser import CommandType, parse_comment_command


def test_parse_commands_with_first_token_rule() -> None:
    assert parse_comment_command(" /continue")
    assert parse_comment_command("abc\n/continue") is None
    assert parse_comment_command("/sparring start").type == CommandType.START


def test_focus_requires_nonempty_text() -> None:
    with pytest.raises(ValueError):
        parse_comment_command("/focus")
    with pytest.raises(ValueError):
        parse_comment_command("/focus   ")
    cmd = parse_comment_command("/focus narrow on risk")
    assert cmd and cmd.type == CommandType.FOCUS
    assert cmd.focus_text == "narrow on risk"
