from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from assets_guardian.core.domain.models.finding import Finding


class IPDFBuilder(ABC):
    """Contract that each plugin implements to render
    its section in the PDF audit report.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the source ('gitlab', 'm365', 'dolibarr')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def section_title(self) -> str:
        """Title of the section in the PDF report.
        E.g., 'GitLab - gitlab.com'
        """
        raise NotImplementedError

    @abstractmethod
    def render(self, pdf: Any, findings: Iterable[Finding]) -> None:
        """Renders the PDF section for this source.

        Args:
            pdf: The PDF object currently being built (FPDF or equivalent).
            findings: List of Finding elements filtered for this source,
                      already grouped by severity by the calling PDFWriter.
        """
        raise NotImplementedError
