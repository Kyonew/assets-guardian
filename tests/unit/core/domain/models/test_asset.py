"""Tests for the Asset model representing application or infrastructure resources."""

from datetime import UTC, datetime

import pytest

from assets_guardian.core.domain.models.asset import Asset


@pytest.fixture
def valid_asset_data() -> dict:
    """Provide a dictionary of valid initialization parameters for Asset model."""
    return {
        "source": "gitlab",
        "external_id": "ext-123",
        "asset_type": "repository",
        "name": "my-repo",
        "description": "A test repository",
        "state": "active",
        "created_at": datetime(2023, 1, 1, tzinfo=UTC),
        "created_by": "user1",
        "comments": "No comments",
        "metadata": {"env": "prod"},
    }


def test_asset_creation_success(valid_asset_data) -> None:
    """Verify that an Asset instance is initialized successfully when valid inputs are provided."""
    asset = Asset(**valid_asset_data)
    assert asset.source == "gitlab"
    assert asset.external_id == "ext-123"
    assert asset.name == "my-repo"
    assert asset.description == "A test repository"
    assert asset.metadata == {"env": "prod"}


@pytest.mark.parametrize(
    "field, invalid_value, expected_error",
    [
        ("source", 123, TypeError),
        ("external_id", None, TypeError),
        ("asset_type", [], TypeError),
        ("name", {}, TypeError),
        ("description", 1.0, TypeError),
        ("state", datetime.now(tz=UTC), TypeError),
        ("created_at", "2023-01-01", TypeError),
        ("created_by", 42, TypeError),
        ("comments", ["list"], TypeError),
        ("metadata", "string", TypeError),
    ],
)
def test_asset_type_validation(valid_asset_data, field, invalid_value, expected_error) -> None:
    """Verify that Asset raises TypeError when fields receive invalid types."""
    data = valid_asset_data.copy()
    data[field] = invalid_value
    with pytest.raises(expected_error):
        Asset(**data)


@pytest.mark.parametrize(
    "field",
    ["source", "external_id", "asset_type", "name"],
)
def test_asset_mandatory_fields_empty_raises(valid_asset_data, field) -> None:
    """Verify that Asset raises ValueError when mandatory fields are empty string."""
    data = valid_asset_data.copy()
    data[field] = ""
    with pytest.raises(ValueError, match="must be a non-empty value"):
        Asset(**data)


def test_asset_optional_fields_can_be_none(valid_asset_data) -> None:
    """Verify that optional fields default to None when omitted."""
    # We remove the optional fields
    data = {
        "source": "src",
        "external_id": "ext",
        "asset_type": "type",
        "name": "name",
    }
    asset = Asset(**data)
    assert asset.description is None
    assert asset.state is None
    assert asset.created_at is None
    assert asset.metadata is None


def test_asset_immutability(valid_asset_data) -> None:
    """Verify that Asset fields are frozen and cannot be modified after instantiation."""
    asset = Asset(**valid_asset_data)
    with pytest.raises(AttributeError):
        asset.source = "new-source"  # type: ignore


def test_asset_slots(valid_asset_data) -> None:
    """Verify that Asset prevents dynamic attribute addition via __slots__ constraints."""
    asset = Asset(**valid_asset_data)
    with pytest.raises((AttributeError, TypeError)):
        asset.new_field = "unexpected"  # type: ignore
