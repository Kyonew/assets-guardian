"""Unit tests for the audit CLI command module."""

import pytest

from assets_guardian.cli.audit import run_audit_command


def test_run_audit_command_prints_message(capsys: pytest.CaptureFixture[str]) -> None:
    """The audit command prints its placeholder message to stdout."""
    run_audit_command()

    captured = capsys.readouterr()
    assert captured.out == "Audit command.\n"
    assert captured.err == ""
