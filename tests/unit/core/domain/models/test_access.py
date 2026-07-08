"""Tests for the Access model representing user permissions and access rights on assets."""

from datetime import UTC, datetime

import pytest

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset


@pytest.fixture
def valid_asset() -> Asset:
    """Provide a valid mock Asset instance for testing."""
    return Asset(source="test", external_id="ext-1", asset_type="type", name="name")


@pytest.fixture
def valid_access_data(valid_asset) -> dict:
    """Provide a dictionary of valid initialization parameters for Access model."""
    return {
        "source": "gitlab",
        "access_type": "permission",
        "name": "Maintainer",
        "description": "Full access",
        "asset": valid_asset,
        "state": "active",
        "start_at": datetime(2023, 1, 1, tzinfo=UTC),
        "ends_at": datetime(2024, 1, 1, tzinfo=UTC),
        "comments": "Critical access",
        "metadata": {"reason": "lead dev"},
    }


def test_access_creation_success(valid_access_data) -> None:
    """Verify that an Access instance is initialized successfully when valid inputs are provided."""
    access = Access(**valid_access_data)
    assert access.source == "gitlab"
    assert isinstance(access.asset, Asset)


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("source", 123),
        ("access_type", None),
        ("name", []),
        ("asset", "not-an-asset"),
        ("state", 42),
        ("start_at", "2023-01-01"),
        ("metadata", "string"),
    ],
)
def test_access_type_validation(valid_access_data, field, invalid_value) -> None:
    """Verify that Access raises TypeError when fields receive invalid types."""
    data = valid_access_data.copy()
    data[field] = invalid_value
    with pytest.raises(TypeError):
        Access(**data)


@pytest.mark.parametrize(
    "field",
    ["source", "access_type", "name"],
)
def test_access_mandatory_fields_empty_raises(valid_access_data, field) -> None:
    """Verify that Access raises ValueError when mandatory fields are empty string."""
    data = valid_access_data.copy()
    data[field] = ""
    with pytest.raises(ValueError, match="must be a non-empty value"):
        Access(**data)


def test_access_immutability(valid_access_data) -> None:
    """Verify that Access fields are frozen and cannot be modified after instantiation."""
    access = Access(**valid_access_data)
    with pytest.raises(AttributeError):
        access.source = "new-source"  # type: ignore


def test_access_slots(valid_access_data) -> None:
    """Verify that Access prevents dynamic attribute addition via __slots__ constraints."""
    access = Access(**valid_access_data)
    with pytest.raises((AttributeError, TypeError)):
        access.invalid = 1  # type: ignore
