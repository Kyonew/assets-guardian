from unittest.mock import MagicMock, patch

from assets_guardian.core.domain.registry.client_registry import ClientProviderRegistry
from assets_guardian.core.domain.registry.collector_factory import (
    instantiate_collectors,
)
from assets_guardian.core.domain.registry.collector_registry import CollectorRegistry


def test_instantiate_collectors_success():
    mock_provider = MagicMock()
    mock_client = MagicMock()
    mock_provider.instantiate_client.return_value = mock_client

    mock_collector = MagicMock()

    with (
        patch.object(
            ClientProviderRegistry, "instantiates_clientprovider", return_value=mock_provider
        ),
        patch.object(CollectorRegistry, "instantiates_collector", return_value=mock_collector),
    ):
        config = {"gitlab": {"prod": {"url": "test"}}}
        collectors = instantiate_collectors(config)

        assert (("gitlab", "prod")) in collectors
        assert collectors[("gitlab", "prod")] == mock_collector
        mock_provider.instantiate_client.assert_called_once()


def test_instantiate_collectors_no_client_provider(caplog):
    mock_collector = MagicMock()

    with (
        patch.object(
            ClientProviderRegistry,
            "instantiates_clientprovider",
            side_effect=KeyError("No provider"),
        ),
        patch.object(CollectorRegistry, "instantiates_collector", return_value=mock_collector),
    ):
        config = {"gitlab": {"prod": {"url": "test"}}}
        with caplog.at_level("WARNING"):
            collectors = instantiate_collectors(config)

        assert (("gitlab", "prod")) in collectors
        assert "No client provider found" in caplog.text


def test_instantiate_collectors_collector_key_error(caplog):
    with (
        patch.object(
            ClientProviderRegistry,
            "instantiates_clientprovider",
            side_effect=KeyError("No provider"),
        ),
        patch.object(
            CollectorRegistry, "instantiates_collector", side_effect=KeyError("No collector")
        ),
        caplog.at_level("ERROR"),
    ):
        config = {"gitlab": {"prod": {"url": "test"}}}
        instantiate_collectors(config)
        assert "Plugin not found" in caplog.text


def test_instantiate_collectors_general_error(caplog):
    with (
        patch.object(
            ClientProviderRegistry,
            "instantiates_clientprovider",
            side_effect=Exception("Major error"),
        ),
        caplog.at_level("ERROR"),
    ):
        config = {"gitlab": {"prod": {"url": "test"}}}
        instantiate_collectors(config)
        assert "Error during initialization" in caplog.text


def test_instantiate_collectors_none_params_defaults_to_empty_dict() -> None:
    """instantiate_collectors treats None params as an empty dict and injects instance_id."""
    mock_provider = MagicMock()
    mock_provider.instantiate_client.return_value = MagicMock()
    mock_collector = MagicMock()

    with (
        patch.object(
            ClientProviderRegistry, "instantiates_clientprovider", return_value=mock_provider
        ),
        patch.object(CollectorRegistry, "instantiates_collector", return_value=mock_collector),
    ):
        # params=None triggers the `if params is None: params = {}` branch
        config = {"gitlab": {"prod": None}}
        collectors = instantiate_collectors(config)

    assert ("gitlab", "prod") in collectors


def test_instantiate_collectors_instance_id_already_in_params() -> None:
    """instantiate_collectors does not overwrite an instance_id that was already set in params."""
    mock_provider = MagicMock()
    mock_provider.instantiate_client.return_value = MagicMock()
    mock_collector = MagicMock()

    with (
        patch.object(
            ClientProviderRegistry, "instantiates_clientprovider", return_value=mock_provider
        ) as mock_instantiate,
        patch.object(CollectorRegistry, "instantiates_collector", return_value=mock_collector),
    ):
        # params already contains instance_id, the injection branch should be skipped
        config = {"gitlab": {"prod": {"instance_id": "custom-id", "url": "http://test"}}}
        instantiate_collectors(config)

    _, call_params = mock_instantiate.call_args[0]
    # The existing instance_id must not have been overwritten
    assert call_params["instance_id"] == "custom-id"
