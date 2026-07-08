import logging

from assets_guardian.core.cache.cache import CacheManager
from assets_guardian.core.domain.engines.audit_engine import AuditEngine
from assets_guardian.core.domain.engines.check_engine import CheckEngine
from assets_guardian.core.domain.engines.pdf_engine import PdfEngine
from assets_guardian.core.domain.models.context import Context
from assets_guardian.core.domain.registry.collector_factory import instantiate_collectors

logger = logging.getLogger(__name__)


def run_audit_command(ctx: Context) -> None:
    """Executes the IAM compliance audit process and generates a report.

    This function orchestrates the following technical flow:
    1. Global execution of CheckEngine before proceeding.
    2. Loading and validating active collectors.
    3. Initializing the audit engine (AuditEngine) with its cache manager.
    4. Running the audit (data collection, rule evaluation, and detection).
    5. Generating the PDF report via PdfEngine.
    6. Final cleanup of the temporary audit cache.

    Args:
        ctx: The application context containing the configuration and parameters.

    Raises:
        RuntimeError: If the environment verification fails (CheckEngine).
    """
    logger.info("Launching source audit...")

    # Global execution of CheckEngine before proceeding
    check_engine = CheckEngine()
    if not check_engine.run(ctx):
        logger.error("Environment check failed. Stopping the audit.")
        raise RuntimeError("Configuration error, see assets-guardian check for more details.")

    # Instantiating and validating active collectors.
    collectors = list(instantiate_collectors(ctx.app_config.integrations).values())

    # Running the audit engine
    audit_engine = AuditEngine(cache=CacheManager(config=ctx.app_config.cache))
    try:
        results = audit_engine.run(collectors, ctx)

        logger.debug("Audit engine executed successfully.")

        # Generating the PDF report
        pdf_engine = PdfEngine()
        pdf_engine.generate(results, ctx)

    finally:
        # Cleanup after the audit
        audit_engine.cache.cleanup("audit", env=ctx.app_config.env)
        logger.debug("Audit cache cleanup completed.")
