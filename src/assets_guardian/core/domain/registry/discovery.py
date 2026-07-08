import importlib
import logging
from pathlib import Path

from assets_guardian import DIR_PLUGINS
from assets_guardian.core.domain.models.context import AssetsGuardianMode, Context

logger = logging.getLogger(__name__)


def discover_default_rules() -> None:
    """Loads the integrated default audit rules from the plugins package.

    This function attempts to import the 'assets_guardian.plugins.default_rules' module.

    Raises:
        Exception: Logs an exception if loading fails for a reason other than a missing module.
    """

    # Default rules
    try:
        importlib.import_module("assets_guardian.plugins.default_rules")
        logger.debug("Default rules loaded.")
    except ImportError:
        logger.debug("No default rules file found.")
    except Exception:
        logger.exception("Failed to load default rules.")


def discover_all(ctx: Context) -> None:
    """Dynamically scans the plugins folder and core to register components.

    This function imports:
    - Clients (via assets_guardian.plugins.<plugin_name>.client)
    - Collectors (via assets_guardian.plugins.<plugin_name>.collector)
    - Plugin rules (via assets_guardian.plugins.<plugin_name>.rules)
    - PDF builders (via assets_guardian.plugins.<plugin_name>.pdf_builder)
    - Excel builders (via assets_guardian.plugins.<plugin_name>.sheet_builders)
    - Default rules (via assets_guardian.plugins.default_rules)

    Args:
        ctx: The execution context containing the current mode (AUDIT, SYNC, etc.).
    """

    logger.info("Starting component discovery...")

    if not DIR_PLUGINS.exists():
        logger.warning("Plugin directory not found: %s", DIR_PLUGINS)
        return

    is_audit = ctx.mode == AssetsGuardianMode.AUDIT
    is_sync = ctx.mode == AssetsGuardianMode.SYNC

    # Default rules
    if is_audit:
        discover_default_rules()

    for path in DIR_PLUGINS.iterdir():
        if path.is_dir() and not path.name.startswith(("_", ".")):
            plugin_name = path.name

            # Only load the plugin if it is present in the configuration
            if plugin_name not in ctx.app_config.integrations:
                logger.debug(
                    "Plugin %s ignored because it is absent from the configuration.", plugin_name
                )
                continue

            # Load core components
            load_client(path, plugin_name)
            load_collector(path, plugin_name)

            # Load optional/contextual components
            if is_audit:
                load_rules(path, plugin_name)
                load_pdf_builders(path, plugin_name)

            if is_sync:
                load_sheet_builders(path, plugin_name)


def load_client(path: Path, plugin_name: str) -> None:
    """Loads the client.py module of a plugin if it exists.

    Args:
        path: Path to the plugin directory.
        plugin_name: Technical name of the plugin.

    Raises:
        Exception: Logs an exception if importing fails.
    """
    try:
        module_name = f"assets_guardian.plugins.{plugin_name}.client"
        if (path / "client.py").exists():
            importlib.import_module(module_name)
            logger.debug("Client loaded for plugin: %s", plugin_name)
    except Exception:
        logger.exception("Failed to load client for %s", plugin_name)


def load_collector(path: Path, plugin_name: str) -> None:
    """Loads the collector.py module of a plugin if it exists.

    Args:
        path: Path to the plugin directory.
        plugin_name: Technical name of the plugin.

    Raises:
        Exception: Logs an exception if importing fails.
    """
    try:
        module_name = f"assets_guardian.plugins.{plugin_name}.collector"
        if (path / "collector.py").exists():
            importlib.import_module(module_name)
            logger.debug("Collector loaded for plugin: %s", plugin_name)
    except Exception:
        logger.exception("Failed to load collector for %s", plugin_name)


def load_rules(path: Path, plugin_name: str) -> None:
    """Loads the rules.py module of a plugin if it exists.

    Args:
        path: Path to the plugin directory.
        plugin_name: Technical name of the plugin.

    Raises:
        Exception: Logs an exception if importing fails.
    """
    try:
        module_name = f"assets_guardian.plugins.{plugin_name}.rules"
        if (path / "rules.py").exists():
            importlib.import_module(module_name)
            logger.debug("Rules loaded for plugin: %s", plugin_name)
    except Exception:
        logger.exception("Failed to load rules for %s", plugin_name)


def load_sheet_builders(path: Path, plugin_name: str) -> None:
    """Loads the sheet_builders.py module of a plugin if it exists.

    Args:
        path: Path to the plugin directory.
        plugin_name: Technical name of the plugin.

    Raises:
        Exception: Logs an exception if importing fails.
    """
    try:
        module_name = f"assets_guardian.plugins.{plugin_name}.sheet_builders"
        if (path / "sheet_builders.py").exists():
            importlib.import_module(module_name)
            logger.debug("Excel builders loaded for plugin: %s", plugin_name)
    except Exception:
        logger.exception("Failed to load Excel builders for %s", plugin_name)


def load_pdf_builders(path: Path, plugin_name: str) -> None:
    """Loads the pdf_builder.py module of a plugin if it exists.

    Args:
        path: Path to the plugin directory.
        plugin_name: Technical name of the plugin.

    Raises:
        Exception: Logs an exception if importing fails.
    """
    try:
        module_name = f"assets_guardian.plugins.{plugin_name}.pdf_builder"
        if (path / "pdf_builder.py").exists():
            importlib.import_module(module_name)
            logger.debug("PDF builders loaded for plugin: %s", plugin_name)
    except Exception:
        logger.exception("Failed to load PDF builders for %s", plugin_name)
