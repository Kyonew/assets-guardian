import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from assets_guardian.core.config.logging_config import LoggingConfig

_RESET = "\033[0m"
_BOLD = "\033[1m"
_LEVEL_COLORS = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[34m",  # blue
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[35m",  # magenta
}


class ColorFormatter(logging.Formatter):
    """Formatter that colors the levelname with ANSI codes (bold + color)."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        original = record.levelname
        if color:
            record.levelname = f"{_BOLD}{color}{original}{_RESET}"
        try:
            return super().format(record)
        finally:
            record.levelname = original


def init_logging(logging_config: LoggingConfig) -> None:
    """Initializes logging configuration.

    Creates a rotating file handler for logging,
    and a console handler with a configurable level.

    Args:
        logging_config: The logging configuration.
    """

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{logging_config.file_basename}.log"

    # Standard rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=logging_config.max_size,
        backupCount=logging_config.max_files,
    )
    file_handler.setLevel(logging_config.file_level)

    # File log message format
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()

    # Clear existing handlers to prevent duplicate logs on re-initialization
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Set root logger level to the lower of file and console levels
    root_logger.setLevel(min(logging_config.file_level, logging_config.console_level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_config.console_level)
    # Concise format for console, with colors if TTY
    fmt = "%(levelname)s - %(message)s"
    console_formatter: logging.Formatter = (
        ColorFormatter(fmt) if sys.stderr.isatty() else logging.Formatter(fmt)
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Attach file handler to the root logger
    root_logger.addHandler(file_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)  # Reduce asyncio noise
    logging.getLogger("faker.factory").setLevel(logging.WARNING)  # Reduce faker noise

    root_logger.debug(
        "Logging initialized (File: %s, Console: %s)",
        logging.getLevelName(logging_config.file_level),
        logging.getLevelName(logging_config.console_level),
    )


def get_plugin_logger(source_name: str) -> logging.Logger:
    """Returns a specific logger for a plugin, as a child of the root logger.

    Using a hierarchy (assets_guardian.plugins.xxx) makes it easy to differentiate
    log origins while inheriting from the root logger configuration.

    Example:
        logger = get_plugin_logger('gitlab')
        logger.info("Start collection")

    Args:
        source_name (str): Name of the plugin.

    Returns:
        logging.Logger: Logger instance specific to the plugin.
    """
    return logging.getLogger(f"assets_guardian.plugins.{source_name}")
