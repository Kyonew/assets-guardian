import logging
import os
from pathlib import Path
from typing import Any

import click

from assets_guardian.core.config.loader import load_json, load_yaml_config
from assets_guardian.core.config.validator import validate_config
from assets_guardian.core.domain.models.context import AssetsGuardianMode, Context
from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry

logger = logging.getLogger(__name__)


LABELS = {
    "config": "Configuration (config.yml)",
    "employees": "Employees (employees.json)",
    "excel": "Excel Rules (excel_config.json)",
    "rules_config": "Audit Rules (rules_config.yml)",
    "pdf": "PDF Rules (pdf_config.json)",
    "folders": "System folders",
}


class CheckEngine:
    """Validation engine for connectivity and configurations."""

    def __init__(self) -> None:
        self.details: dict[str, Any] = {}

    def run(self, ctx: Context) -> bool:
        """Runs global system checks and returns True if no errors are detected.

        Args:
            ctx: The application context.

        Returns:
            bool: True if all configurations and connections are operational, False otherwise.
        """
        self.details = self.run_details(ctx)
        self.__log_report(ctx)
        return self.__is_overall_valid(ctx)

    def __log_report(self, ctx: Context) -> None:
        """Prints the detailed check report to the console.

        Args:
            ctx: The application context containing execution options.
        """
        self.__log_details_to_file()

        if ctx.mode != AssetsGuardianMode.CHECK:
            return

        box_width = 60
        self.__print_header(box_width)
        self.__print_system_checks(box_width)

        instances_status = self.details.get("instances", {})
        self.__print_instances_checks(instances_status, box_width)
        self.__print_bilan(instances_status, box_width)

    def __log_details_to_file(self) -> None:
        """Logs the raw report details at the DEBUG level."""
        logger.debug("--- Detailed Check Report ---")
        for key, label in LABELS.items():
            if key in self.details:
                status = "OK" if self.details[key] else "ERR"
                logger.debug("%s: %s", label, status)

        instances_status = self.details.get("instances", {})
        logger.debug("Instances connectivity:")
        for instance_key, status in instances_status.items():
            logger.debug("  - %s: %s", instance_key, "Accessible" if status else "Inaccessible")

        success = sum(1 for status in instances_status.values() if status)
        total = len(instances_status)
        logger.debug("Health check summary: %d/%d operational source(s).", success, total)

    def __print_header(self, box_width: int) -> None:
        """Prints the check report header.

        Args:
            box_width: The total box width in characters.
        """
        title = "ASSETS GUARDIAN - HEALTH CHECK"
        padded_title = title.center(box_width)

        click.echo()
        click.secho(f" ┌{'─' * box_width}┐", fg="cyan")
        click.secho(f" │{padded_title}│", fg="cyan", bold=True)
        click.secho(f" └{'─' * box_width}┘", fg="cyan")
        click.echo()

    def __print_system_checks(self, box_width: int) -> None:
        """Prints system and configuration check statuses.

        Args:
            box_width: The total box width in characters.
        """
        click.secho("  CONFIGURATION & SYSTEM CHECKS", fg="cyan", bold=True)
        click.secho("  " + "─" * box_width, fg="cyan")

        ok_sym = click.style("✔", fg="green", bold=True)
        err_sym = click.style("✘", fg="red", bold=True)
        ok_tag = click.style("[OK]", fg="green", bold=True)
        err_tag = click.style("[ERR]", fg="red", bold=True)

        for key, label in LABELS.items():
            if key in self.details:
                status_ok = self.details[key]
                symbol = ok_sym if status_ok else err_sym
                tag = ok_tag if status_ok else err_tag
                dots_count = max(3, box_width - len(label) - 10)
                dots = click.style("." * dots_count, fg="white", dim=True)
                click.echo(f"  {symbol}  {label} {dots} {tag}")

    def __print_instances_checks(self, instances_status: dict[str, bool], box_width: int) -> None:
        """Prints the connectivity status of configured instances.

        Args:
            instances_status: Dictionary containing connectivity statuses.
            box_width: The total box width in characters.
        """
        click.echo()
        click.secho("  INSTANCES CONNECTIVITY", fg="cyan", bold=True)
        click.secho("  " + "─" * box_width, fg="cyan")

        ok_sym = click.style("✔", fg="green", bold=True)
        err_sym = click.style("✘", fg="red", bold=True)
        accessible_tag = click.style("[ACCESSIBLE]", fg="green", bold=True)
        inaccessible_tag = click.style("[INACCESSIBLE]", fg="red", bold=True)

        if not instances_status:
            click.echo("  No instances configured.")
        else:
            for instance_key, status_ok in instances_status.items():
                symbol = ok_sym if status_ok else err_sym
                tag = accessible_tag if status_ok else inaccessible_tag
                dots_count = max(3, box_width - len(instance_key) - 18)
                dots = click.style("." * dots_count, fg="white", dim=True)
                click.echo(f"  {symbol}  {instance_key} {dots} {tag}")

    def __print_bilan(self, instances_status: dict[str, bool], box_width: int) -> None:
        """Prints the final connectivity summary.

        Args:
            instances_status: Dictionary containing connectivity statuses.
            box_width: The total box width in characters.
        """
        click.echo()
        click.secho("  " + "─" * box_width, fg="cyan")

        total = len(instances_status)
        success = sum(1 for status in instances_status.values() if status)

        if total > 0:
            if success == total:
                bilan_color = "green"
            elif success > 0:
                bilan_color = "yellow"
            else:
                bilan_color = "red"
            bilan_text = f"{success}/{total} operational source(s)"
            styled_bilan = click.style(bilan_text, fg=bilan_color, bold=True)
            click.echo(f"  Connectivity report: {styled_bilan}")
        else:
            click.echo("  Connectivity report: No sources configured.")

    def __is_overall_valid(self, ctx: Context) -> bool:
        """Determines if the global system state is valid and logs/prints the final verdict.

        Args:
            ctx: The application context containing execution options.

        Returns:
            bool: True if all validation steps and connectivity are successful, False otherwise.
        """
        instances_status = self.details.get("instances", {})
        steps_valid = all(status for name, status in self.details.items() if name != "instances")
        instances_valid = all(instances_status.values())
        overall_valid = steps_valid and instances_valid

        if overall_valid:
            logger.debug("Global verification: EVERYTHING IS OPERATIONAL")
        else:
            logger.debug("Global verification: ERRORS HAVE BEEN DETECTED")

        if ctx.mode == AssetsGuardianMode.CHECK:
            box_width = 60
            if overall_valid:
                msg = "VERDICT: EVERYTHING IS OPERATIONAL"
                padded_msg = msg.center(box_width)
                click.secho(f"  ┌{'─' * box_width}┐", fg="green", bold=True)
                click.secho(f"  │{padded_msg}│", fg="green", bold=True)
                click.secho(f"  └{'─' * box_width}┘", fg="green", bold=True)
            else:
                msg = "VERDICT: ERRORS HAVE BEEN DETECTED"
                padded_msg = msg.center(box_width)
                click.secho(f"  ┌{'─' * box_width}┐", fg="red", bold=True)
                click.secho(f"  │{padded_msg}│", fg="red", bold=True)
                click.secho(f"  └{'─' * box_width}┘", fg="red", bold=True)
            click.echo()

        return overall_valid

    def run_details(self, ctx: Context) -> dict[str, Any]:
        """Generates a summary dictionary of all checks depending on the context mode.

        Args:
            ctx: The application context containing the configuration.

        Returns:
            dict[str, Any]: Dictionary containing the status of each validation check.
        """
        details: dict[str, Any] = {}

        # YAML Config
        details["config"] = self.__check_config_yaml(ctx)

        # Employees JSON
        details["employees"] = self.__check_employees_json(ctx)

        # Excel JSON
        details["excel"] = self.__check_excel_json(ctx)

        # Mode-dependent checks
        is_audit = ctx.mode == AssetsGuardianMode.AUDIT
        is_check = ctx.mode in (AssetsGuardianMode.CHECK, AssetsGuardianMode.UNRECOGNIZED)

        if is_audit or is_check:
            details["rules_config"] = self.__check_rules_config_yaml(ctx)
            details["pdf"] = self.__check_pdf_json(ctx)

        # System folders check
        details["folders"] = self.__check_folders(ctx)

        # Instances connectivity checks
        instances_status = {}
        for source_name, instances in ctx.app_config.integrations.items():
            for instance_id, params in instances.items():
                if params is None:
                    params = {}
                if "instance_id" not in params:
                    params["instance_id"] = instance_id

                key = f"{source_name}:{instance_id}"
                try:
                    client_provider = ClientProviderRegistry.instantiates_clientprovider(
                        source_name, params
                    )
                    status = client_provider.health_check()
                    instances_status[key] = status
                except Exception:
                    logger.exception(
                        "Connectivity error on instance %s:%s",
                        source_name,
                        instance_id,
                    )
                    instances_status[key] = False
        details["instances"] = instances_status

        return details

    def __check_config_yaml(self, ctx: Context) -> bool:
        """Validates the config.yml file against its reference template.

        Args:
            ctx: The application context.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """
        try:
            config_path = Path(ctx.app_config.paths.config_path.clean_path)
            template_path = config_path.parent / f"template.{config_path.name}"
            if not template_path.exists():
                logger.error("Config template file not found: %s", template_path)
                return False
            config_parameters = load_yaml_config(str(config_path))
            config_template = load_yaml_config(str(template_path))
            validate_config(config_parameters, config_template)
        except Exception:
            logger.exception("Verification of config.yml failed")
            return False
        else:
            return True

    def __check_rules_config_yaml(self, ctx: Context) -> bool:
        """Validates the rules_config.yml file.

        Args:
            ctx: The application context.

        Returns:
            bool: True if audit rules configuration is valid, False otherwise.
        """
        try:
            path = ctx.app_config.paths.rules_config.clean_path
            load_yaml_config(path)
        except Exception:
            logger.exception("Verification of rules_config.yml failed")
            return False
        else:
            return True

    def __check_employees_json(self, ctx: Context) -> bool:
        """Validates the employees.json file.

        Args:
            ctx: The application context.

        Returns:
            bool: True if the employees data is valid, False otherwise.
        """
        try:
            path = ctx.app_config.paths.employees.clean_path
            load_json(path)
        except Exception:
            logger.exception("Verification of employees.json failed")
            return False
        else:
            return True

    def __check_excel_json(self, ctx: Context) -> bool:
        """Validates the excel_config.json file.

        Args:
            ctx: The application context.

        Returns:
            bool: True if the Excel rules configuration is valid, False otherwise.
        """
        try:
            path = ctx.app_config.paths.excel_config.clean_path
            load_json(path)
        except Exception:
            logger.exception("Verification of excel_config.json failed")
            return False
        else:
            return True

    def __check_pdf_json(self, ctx: Context) -> bool:
        """Validates the pdf_config.json file.

        Args:
            ctx: The application context.

        Returns:
            bool: True if the PDF rules configuration is valid, False otherwise.
        """
        try:
            path = ctx.app_config.paths.pdf_config.clean_path
            load_json(path)
        except Exception:
            logger.exception("Verification of pdf_config.json failed")
            return False
        else:
            return True

    def __check_folders(self, ctx: Context) -> bool:
        """Validates the existence and permissions of required system directories.

        Args:
            ctx: The application context.

        Returns:
            bool: True if all required folders exist (or are successfully created) and have
                correct permissions, False otherwise.
        """
        folders_to_check = [
            ("logs", "r+w"),
            ("config", "r"),
            ("outputs", "r+w"),
            (ctx.app_config.cache.cache_dir, "r+w"),
        ]

        folders_valid = True
        for path_str, perm_type in folders_to_check:
            path = Path(path_str)
            if not path.exists():
                if perm_type == "r+w":
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        logger.exception(
                            "Directory does not exist and cannot be created: %s", path_str
                        )
                        folders_valid = False
                        continue
                else:
                    logger.error("Directory does not exist: %s", path_str)
                    folders_valid = False
                    continue

            # Check permissions
            if not os.access(path, os.R_OK):
                logger.error("Directory is not readable: %s", path_str)
                folders_valid = False
            if perm_type == "r+w" and not os.access(path, os.W_OK):
                logger.error("Directory is not writable: %s", path_str)
                folders_valid = False

        return folders_valid
