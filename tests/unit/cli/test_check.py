"""Unit tests for the check CLI command module."""

import pytest

from assets_guardian.cli.check import run_check_command


def test_run_check_command_prints_message(capsys: pytest.CaptureFixture[str]) -> None:
    """The check command prints its placeholder message to stdout."""
    run_check_command()

    captured = capsys.readouterr()
    assert captured.out == "Check command.\n"
    assert captured.err == ""
