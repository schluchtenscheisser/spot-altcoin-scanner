from __future__ import annotations

from pathlib import Path

import pytest

from scripts import _runner_guard


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("print('ok')\n", encoding="utf-8")


def test_accepts_existing_python_file_under_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _touch(tmp_path / "scripts" / "foo.py")
    monkeypatch.chdir(tmp_path)

    assert _runner_guard.validate_script_path("scripts/foo.py") == "scripts/foo.py"


def test_accepts_existing_nested_python_file_under_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _touch(tmp_path / "scripts" / "analysis" / "foo.py")
    monkeypatch.chdir(tmp_path)

    assert (
        _runner_guard.validate_script_path("scripts/analysis/foo.py")
        == "scripts/analysis/foo.py"
    )


def test_rejects_missing_argument() -> None:
    rc = _runner_guard.main([])
    assert rc == 1


@pytest.mark.parametrize("value", ["", "   "])
def test_rejects_empty_or_whitespace_string(value: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        _runner_guard.validate_script_path(value)


def test_rejects_absolute_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError):
        _runner_guard.validate_script_path("/tmp/foo.py")


@pytest.mark.parametrize(
    "value",
    [
        "../scripts/foo.py",
        "scripts/../foo.py",
        "scripts/subdir/../../foo.py",
        "docs/foo.py",
        "reports/analysis/foo.py",
        "evaluation/exports/foo.py",
    ],
)
def test_rejects_traversal_and_outside_scripts_paths(
    value: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _touch(tmp_path / "scripts" / "foo.py")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        _runner_guard.validate_script_path(value)


def test_rejects_missing_file_under_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        _runner_guard.validate_script_path("scripts/missing.py")


def test_rejects_directory_under_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "scripts" / "analysis").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        _runner_guard.validate_script_path("scripts/analysis")


def test_rejects_non_python_file_under_scripts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "scripts" / "foo.sh"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("echo hi\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        _runner_guard.validate_script_path("scripts/foo.sh")


def test_cli_emits_exactly_one_stdout_line_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _touch(tmp_path / "scripts" / "analysis" / "foo.py")
    monkeypatch.chdir(tmp_path)

    rc = _runner_guard.main(["scripts/analysis/foo.py"])
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.out == "script_path=scripts/analysis/foo.py\n"
    assert captured.err == ""
    assert captured.out.count("\n") == 1


def test_cli_emits_error_to_stderr_and_nonzero_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    rc = _runner_guard.main(["docs/foo.py"])
    captured = capsys.readouterr()

    assert rc == 1
    assert captured.out == ""
    assert "Invalid script_path" in captured.err
