"""Unit tests for the sync CLI command module."""

import pytest

from assets_guardian.cli.sync import run_sync_command


def test_run_sync_command_prints_message(capsys: pytest.CaptureFixture[str]) -> None:
    """The sync command prints its placeholder message to stdout."""
    run_sync_command()

    captured = capsys.readouterr()
    assert captured.out == "Sync command.\n"
    assert captured.err == ""
