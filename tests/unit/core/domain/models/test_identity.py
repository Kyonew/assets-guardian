"""Tests for the Identity model representing users and service account accounts."""

from datetime import UTC, datetime
from ipaddress import IPv4Address, IPv6Address

import pytest

from assets_guardian.core.domain.models.identity import Identity, IdentityState, IdentityType


@pytest.fixture
def valid_identity_data() -> dict:
    """Provide a dictionary of valid initialization parameters for Identity model."""
    return {
        "source": "gitlab",
        "external_id": "ext-456",
        "identity_type": IdentityType.HUMAN,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "username": "jdoe",
        "first_name": "Jane",
        "last_name": "Doe",
        "company": "Corp Inc",
        "description": "Developer",
        "state": IdentityState.ACTIVE,
        "mfa_enabled": True,
        "is_privileged": False,
        "is_external": False,
        "created_at": datetime(2023, 1, 1, tzinfo=UTC),
        "created_by": "admin",
        "last_activity_at": datetime(2023, 6, 1, tzinfo=UTC),
        "last_sign_in_at": datetime(2023, 5, 1, tzinfo=UTC),
        "last_sign_in_ip": IPv4Address("1.2.3.4"),
        "comments": "Regular user",
        "metadata": {"role": "dev"},
    }


def test_identity_creation_success(valid_identity_data) -> None:
    """Verify that an Identity instance is initialized successfully when valid inputs are provided."""
    identity = Identity(**valid_identity_data)
    assert identity.source == "gitlab"
    assert identity.identity_type == IdentityType.HUMAN
    assert identity.last_sign_in_ip == IPv4Address("1.2.3.4")


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("source", 123),
        ("external_id", None),
        ("identity_type", "human"),  # Must be the Enum instance
        ("name", ["list"]),
        ("email", 42),
        ("state", "active"),  # Must be the Enum instance
        ("mfa_enabled", "yes"),
        ("is_privileged", 1),
        ("last_sign_in_ip", "1.2.3.4"),  # Must be IPv4Address/IPv6Address
        ("metadata", []),
    ],
)
def test_identity_type_validation(valid_identity_data, field, invalid_value) -> None:
    """Verify that Identity raises TypeError when fields receive invalid types."""
    data = valid_identity_data.copy()
    data[field] = invalid_value
    with pytest.raises(TypeError):
        Identity(**data)


@pytest.mark.parametrize(
    "field",
    ["source", "external_id", "name"],
)
def test_identity_mandatory_fields_empty_raises(valid_identity_data, field) -> None:
    """Verify that Identity raises ValueError when mandatory fields are empty string."""
    data = valid_identity_data.copy()
    data[field] = ""
    with pytest.raises(ValueError, match="must be a non-empty value"):
        Identity(**data)


def test_identity_ipv6_valid(valid_identity_data) -> None:
    """Verify that Identity accepts IPv6 addresses for the last_sign_in_ip field."""
    data = valid_identity_data.copy()
    data["last_sign_in_ip"] = IPv6Address("::1")
    identity = Identity(**data)
    assert identity.last_sign_in_ip == IPv6Address("::1")


def test_identity_immutability(valid_identity_data) -> None:
    """Verify that Identity fields are frozen and cannot be modified after instantiation."""
    identity = Identity(**valid_identity_data)
    with pytest.raises(AttributeError):
        identity.name = "New Name"  # type: ignore


def test_identity_slots(valid_identity_data) -> None:
    """Verify that Identity prevents dynamic attribute addition via __slots__ constraints."""
    identity = Identity(**valid_identity_data)
    with pytest.raises((AttributeError, TypeError)):
        identity.unknown = "value"  # type: ignore
