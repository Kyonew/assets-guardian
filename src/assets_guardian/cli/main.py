"""Assets Guardian CLI entry point."""

import click

from .audit import run_audit_command
from .check import run_check_command
from .sync import run_sync_command

BANNER = r"""                    ***++++*++
             *********+* ++++======  ==          ___                   __
             ********        ===  ===           /   |  _____________  / /______
            ###*               ==== ==         / /| | / ___/ ___/ _ \/ __/ ___/
            ####             ==== ===-        / ___ |(__  |__  )  __/ /_(__  )
            ####           -==++  ====       /_/  |_/____/____/\___/\__/____/  ___
             ### +**+===  ==++   .===              / ____/_  ______ __________/ (_)___ _____
             ## ##  ***====++    ====             / / __/ / / / __ `/ ___/ __  / / __ `/ __ \
             ####=    **==++     ====            / /_/ / /_/ / /_/ / /  / /_/ / / /_/ / / / /
              ####     +***     =+==             \____/\__,_/\__,_/_/   \__,_/_/\__,_/_/ /_/
               -###+    *     * +++
                ###**        **+++                            A modular IAM governance tool
                  ##***#  ####*+
                   *#########*+
                      #####*
"""


class AssetsGuardianGroup(click.Group):
    """Custom Click Group to prepend a beautiful ASCII banner to the help output."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        formatter.write(BANNER + "\n")
        super().format_help(ctx, formatter)


@click.group(cls=AssetsGuardianGroup)
@click.version_option(version="0.0.0", prog_name="assets-guardian")
@click.option(
    "--config", "_config", default="config/config.yml", help="Path to the configuration file."
)
@click.option("--dry-run", "_dry_run", is_flag=True, help="Simulation mode without side effects.")
@click.option("-v", "--verbose", "_verbose", is_flag=True, help="DEBUG logs in the console.")
@click.option("-q", "--quiet", "_quiet", is_flag=True, help="ERROR logs only.")
@click.option("--no-interaction", "_no_interaction", is_flag=True, help="Non-interactive mode.")
@click.pass_context
def cli(
    _ctx: click.Context,
    _config: str,
    _dry_run: bool,
    _verbose: bool,
    _quiet: bool,
    _no_interaction: bool,
) -> None:
    """Assets Guardian — IAM governance tool."""
    print("Run Assets Guardian.")  # noqa: T201


@cli.command()
@click.pass_context
def sync(_ctx: click.Context) -> None:
    """Synchronizes the permissions Excel repository.

    This command connects to the configured data sources to extract current permissions
    information, then updates the reference Excel file while preserving manual changes
    and specific tabs.
    """
    run_sync_command()


@cli.command()
@click.pass_context
def audit(_ctx: click.Context) -> None:
    """Executes a comprehensive IAM compliance audit.

    This command retrieves data from the Excel file and updated data to evaluate all
    configured compliance, comparison, and security matrix rules. It produces an audit report
    detailing security gaps and vulnerabilities.
    """
    run_audit_command()


@cli.command()
@click.pass_context
def check(_ctx: click.Context) -> None:
    """Verifies connectivity and status of external sources (Health Check).

    This command tests the connection and authentication with all configured APIs
    and databases to ensure their proper operational function.
    """
    run_check_command()


if __name__ == "__main__":
    cli()
