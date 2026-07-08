import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class CollectorRegistry:
    """Registry for collectors.

    Attributes:
        __collectors: Dictionary of registered collectors.
    """

    __collectors: ClassVar[dict[str, type[Any]]] = {}

    # A nested function is required to support decorator arguments
    # like @CollectorRegistry.register("gitlab").
    @classmethod
    def register(cls, source_name: str) -> Any:
        """Decorator to register a collector in the registry.

        Args:
            source_name: Unique name of the source (e.g., 'gitlab', 'm365').

        Returns:
            The decorator function that registers the class.
        """

        def decorator(collector_cls: type[Any]) -> type[Any]:
            """Registers the collector in the registry.

            Args:
                collector_cls: Collector class to register.

            Returns:
                The registered collector class.
            """
            if source_name in cls.__collectors:
                logger.warning(
                    "Collector for source '%s' is already registered and will be overwritten.",
                    source_name,
                )
            cls.__collectors[source_name] = collector_cls
            logger.debug("Collector registered for source: %s", source_name)
            return collector_cls

        return decorator

    @classmethod
    def instantiates_collector(cls, source_name: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiates and returns a collector for the specified source.

        Args:
            source_name: Name of the source.
            *args: Positional arguments for the collector's constructor.
            **kwargs: Keyword arguments for the collector's constructor.

        Returns:
            An instance of the collector.

        Raises:
            KeyError: If no collector is registered for this source name.
        """
        if source_name not in cls.__collectors:
            logger.error("No collector registered for source: %s", source_name)
            raise KeyError(f"Source '{source_name}' unrecognized in the registry.")

        collector_cls = cls.__collectors[source_name]
        return collector_cls(*args, **kwargs)

    @classmethod
    def list_sources(cls) -> list[str]:
        """Returns the list of registered sources.

        Returns:
            List of source names.
        """
        return list(cls.__collectors.keys())


# Long TODO: Future enhancement: manifest.json at plugin root could declare config parameters.
#  Currently the prefix parsing check is a bit lightweight.
