import logging

from assets_guardian.core.domain.engines.check_engine import CheckEngine
from assets_guardian.core.domain.models.context import Context

logger = logging.getLogger(__name__)


def run_check_command(ctx: Context) -> None:
    """Executes connectivity checks (Health Check) with external sources.

    This function delegates the execution of connection tests and the reporting of the
    overall operational status to the verification engine (CheckEngine).

    Args:
        ctx: The application context containing the configuration and parameters.
    """
    logger.info("Launching health check for sources...")

    # Running connection tests via the verification engine (CheckEngine)
    check_engine = CheckEngine()
    check_engine.run(ctx)
