"""Unit tests for the Assets Guardian CLI entry point."""

import pytest
from click.testing import CliRunner

from assets_guardian.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click test runner."""
    return CliRunner()


def test_help_displays_banner_and_commands(runner: CliRunner) -> None:
    """The help output starts with the ASCII banner and lists every command."""
    result = runner.invoke(main.cli, ["--help"])

    assert result.exit_code == 0
    assert result.output.startswith(main.BANNER)
    assert "Usage:" in result.output
    for command in ("sync", "audit", "check"):
        assert command in result.output


def test_no_args_shows_help_and_exits_with_usage_error(runner: CliRunner) -> None:
    """Invoking the CLI without a subcommand shows the help and exits with code 2."""
    result = runner.invoke(main.cli, [])

    assert result.exit_code == 2
    assert "Usage:" in result.output


def test_version_option(runner: CliRunner) -> None:
    """The --version option reports the program name and version."""
    result = runner.invoke(main.cli, ["--version"])

    assert result.exit_code == 0
    assert "assets-guardian, version 0.0.0" in result.output


@pytest.mark.parametrize(
    ("command", "run_function"),
    [
        ("sync", "run_sync_command"),
        ("audit", "run_audit_command"),
        ("check", "run_check_command"),
    ],
)
def test_command_delegates_to_run_function(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    run_function: str,
) -> None:
    """Each subcommand runs the group callback then calls its run_*_command function."""
    calls: list[str] = []
    monkeypatch.setattr(main, run_function, lambda: calls.append(command))

    result = runner.invoke(main.cli, [command])

    assert result.exit_code == 0
    assert calls == [command]
    assert "Run Assets Guardian." in result.output


def test_global_options_are_accepted(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """All global options can be combined with a subcommand without error."""
    monkeypatch.setattr(main, "run_check_command", lambda: None)

    result = runner.invoke(
        main.cli,
        [
            "--config",
            "custom.yml",
            "--dry-run",
            "--verbose",
            "--quiet",
            "--no-interaction",
            "check",
        ],
    )

    assert result.exit_code == 0
