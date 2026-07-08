"""Tests for the CollectorRegistry class to verify custom collector registration and instantiation."""

import pytest

from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry


def test_collector_registry_register_and_get():
    """Verify that a collector can be registered and retrieved successfully."""

    # Define a mock collector class
    @CollectorRegistry.register("test_source")
    class TestCollector:
        def __init__(self, value):
            self.value = value

    # Verify that the registered source is listed in registry sources
    assert "test_source" in CollectorRegistry.list_sources()

    # Instantiate the collector using the registry class method
    instance = CollectorRegistry.instantiates_collector("test_source", value=42)
    assert isinstance(instance, TestCollector)
    assert instance.value == 42


def test_collector_registry_key_error():
    """Verify that attempting to instantiate an unregistered source raises a KeyError."""
    # Attempting to retrieve an unregistered source
    with pytest.raises(KeyError, match=r"Source 'unknown' unrecognized in the registry\."):
        CollectorRegistry.instantiates_collector("unknown")


def test_collector_registry_overwrite_warning(caplog):
    """Verify that a warning is logged when a source is registered more than once, and the newer registration overwrites the previous."""

    # Initial registration
    @CollectorRegistry.register("overwrite_test")
    class FirstCollector:
        pass

    # Re-registering the same source ID should log a warning
    with caplog.at_level("WARNING"):

        @CollectorRegistry.register("overwrite_test")
        class SecondCollector:
            pass

    assert "is already registered and will be overwritten" in caplog.text

    # Verify that the second (newer) registration is instantiated
    instance = CollectorRegistry.instantiates_collector("overwrite_test")
    assert isinstance(instance, SecondCollector)
