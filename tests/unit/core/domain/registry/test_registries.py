"""Tests for the ClientProviderRegistry class to verify custom provider registration and instantiation."""

import pytest

from assets_guardian.core.domain.ports.client import IClientProvider
from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry


def test_client_provider_registry():
    """Verify that a client provider can be registered, retrieved, and instantiated successfully."""

    class MockProvider(IClientProvider):
        def __init__(self, config):
            self.config = config

        def instantiate_client(self):
            return None

        def health_check(self) -> bool:
            return True

    # Test register decorator
    decorator = ClientProviderRegistry.register("test_src")
    decorator(MockProvider)

    # Test instantiation
    instance = ClientProviderRegistry.instantiates_clientprovider("test_src", {"k": "v"})
    assert isinstance(instance, MockProvider)
    assert instance.config == {"k": "v"}

    # Test missing provider raises KeyError
    with pytest.raises(KeyError):
        ClientProviderRegistry.instantiates_clientprovider("unknown", {})

    # Test overwrite logs warning or successfully registers duplicate
    ClientProviderRegistry.register("test_src")(MockProvider)
