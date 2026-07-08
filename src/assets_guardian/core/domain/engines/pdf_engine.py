import logging
from typing import Any

from assets_guardian.core.domain.models.context import Context
from assets_guardian.core.domain.registry.pdf_builder_registry import PDFBuilderRegistry
from assets_guardian.core.reporting.pdf.writer import PDFWriter

logger = logging.getLogger(__name__)


class PdfEngine:
    """Engine responsible for generating the audit PDF report."""

    def generate(self, data: Any, ctx: Context) -> None:
        """Generates the audit PDF report from the audit findings.

        Args:
            data: Audit results (dictionary or iterable of Report).
            ctx: The application context.
        """
        builders = PDFBuilderRegistry.get_builders()

        pdf_writer = PDFWriter(
            pdf_builders=builders,
            rules_file_path=ctx.app_config.paths.pdf_config.clean_path,
        )

        output_path = ctx.app_config.paths.pdf.clean_path

        reports = data.values() if isinstance(data, dict) else data

        logger.info("Launching PDF report generation...")
        pdf_writer.write(reports, output_path)
        logger.info("PDF report generation completed successfully.")
