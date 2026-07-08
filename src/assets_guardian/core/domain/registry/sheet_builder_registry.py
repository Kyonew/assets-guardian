import logging
from typing import Any, ClassVar

from assets_guardian.core.domain.ports.sheet_builders import ISheetBuilder

logger = logging.getLogger(__name__)


class SheetBuilderRegistry:
    """Registry for Excel sheet builders.

    Attributes:
        __builders: Dictionary mapping a source name to its builder class.
    """

    __builders: ClassVar[dict[str, type[ISheetBuilder]]] = {}

    @classmethod
    def register(cls, source_name: str) -> Any:
        """Decorator to register a builder in the registry.

        Args:
            source_name: Unique name of the source (e.g., 'gitlab', 'm365').

        Returns:
            The decorator function that registers the class.
        """

        def decorator(builder_cls: type[ISheetBuilder]) -> type[ISheetBuilder]:
            if source_name in cls.__builders:
                logger.warning(
                    "Builder for source '%s' is already registered and will be overwritten.",
                    source_name,
                )
            cls.__builders[source_name] = builder_cls
            # Dynamically inject the source name into the class
            builder_cls.source_name = source_name.lower()
            logger.debug("SheetBuilder registered for source: %s", source_name)
            return builder_cls

        return decorator

    @classmethod
    def get_builders(cls) -> list[ISheetBuilder]:
        """Instantiates and returns all registered builders.

        Returns:
            list[ISheetBuilder]: List of ready-to-use builder instances.
        """
        return [builder_cls() for builder_cls in cls.__builders.values()]

    @classmethod
    def list_sources(cls) -> list[str]:
        """Returns the list of registered sources.

        Returns:
            list[str]: List of source names (e.g., ['gitlab', 'm365']).
        """
        return list(cls.__builders.keys())
