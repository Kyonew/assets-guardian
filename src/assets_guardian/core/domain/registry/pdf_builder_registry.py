import logging
from typing import Any, ClassVar

from assets_guardian.core.domain.ports.pdf_builders import IPDFBuilder

logger = logging.getLogger(__name__)


class PDFBuilderRegistry:
    """Registry for PDF rendering builders."""

    __builders: ClassVar[dict[str, type[IPDFBuilder]]] = {}

    @classmethod
    def register(cls, source_name: str) -> Any:
        """Decorator to register a PDF builder in the registry.

        Args:
            source_name: Unique name of the source (e.g., 'gitlab', 'm365').

        Returns:
            The decorator function that registers the class.
        """

        def decorator(builder_cls: type[IPDFBuilder]) -> type[IPDFBuilder]:
            if source_name in cls.__builders:
                logger.warning(
                    "PDF builder for source '%s' is already registered and will be overwritten.",
                    source_name,
                )
            cls.__builders[source_name] = builder_cls
            logger.debug("PDFBuilder registered for source: %s", source_name)
            return builder_cls

        return decorator

    @classmethod
    def get_builders(cls) -> list[IPDFBuilder]:
        """Instantiates and returns all registered builders.

        Returns:
            List of builder instances.
        """
        return [builder_cls() for builder_cls in cls.__builders.values()]

    @classmethod
    def list_sources(cls) -> list[str]:
        """Returns the list of registered sources.

        Returns:
            List of source names.
        """
        return list(cls.__builders.keys())
