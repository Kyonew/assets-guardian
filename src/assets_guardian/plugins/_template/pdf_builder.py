from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding
from assets_guardian.core.domain.ports.pdf_builders import IPDFBuilder
from assets_guardian.core.domain.registry.pdf_builder_registry import PDFBuilderRegistry

from .constants import SOURCE_NAME


@PDFBuilderRegistry.register(SOURCE_NAME)
class TemplatePDFBuilder(IPDFBuilder):
    """Builds the custom PDF section for the template plugin findings."""

    @property
    def source_name(self) -> str:
        return SOURCE_NAME

    @property
    def section_title(self) -> str:
        return ""

    def render(self, pdf: Any, findings: Iterable[Finding]) -> None:
        """Render template-specific sections and findings inside the PDF."""
        # TODO: Implement custom PDF rendering logic if needed, or raise NotImplementedError
        # Below is standard boilerplate for rendering findings using global styles:
        pdf.apply_font("heading")

        bg = pdf.rules.get("colors", {}).get("header_bg", {"r": 240, "g": 240, "b": 240})
        pdf.set_fill_color(bg["r"], bg["g"], bg["b"])

        pdf.cell(0, 10, self.section_title, ln=True, fill=True)
        pdf.ln(5)
        pdf.apply_font("body")

        pdf.render_findings(findings)
