"""Tests for the domain ports defining collector, mapper, and repository interfaces."""

from unittest.mock import MagicMock

import pytest

from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.identity import Identity
from assets_guardian.core.domain.ports.collector import Collector
from assets_guardian.core.domain.ports.mapper import IMapper
from assets_guardian.core.domain.ports.repository import IRepository


class ConcreteCollector(Collector):
    """A concrete implementation of the Collector interface for testing purposes."""

    @property
    def source_name(self) -> str:
        return "test"

    @property
    def instance_id(self) -> str:
        return "test-id"

    def health_check(self) -> bool:
        return True


def test_collector_collect_identities():
    """Verify that collect_identities successfully gathers, maps, and returns identity objects."""
    repo = MagicMock(spec=IRepository)
    mapper = MagicMock(spec=IMapper)
    collector = ConcreteCollector(None, {})
    collector._repository = repo
    collector._mapper = mapper

    repo.get_raw_users.return_value = [{"raw": "user"}]
    mapper.to_identity.return_value = MagicMock(spec=Identity)

    results = list(collector.collect_identities())
    assert len(results) == 1
    repo.get_raw_users.assert_called_once()
    mapper.to_identity.assert_called_once_with({"raw": "user"})


def test_collector_collect_assets():
    """Verify that collect_assets successfully gathers, maps, and returns asset objects."""
    repo = MagicMock(spec=IRepository)
    mapper = MagicMock(spec=IMapper)
    collector = ConcreteCollector(None, {})
    collector._repository = repo
    collector._mapper = mapper

    repo.get_raw_assets.return_value = [{"raw": "asset"}]
    mapper.to_asset.return_value = MagicMock(spec=Asset)

    results = list(collector.collect_assets())
    assert len(results) == 1
    repo.get_raw_assets.assert_called_once()
    mapper.to_asset.assert_called_once_with({"raw": "asset"})


def test_collector_collect_accesses():
    """Verify that collect_accesses successfully gathers, maps, and returns access permission objects associated with assets."""
    repo = MagicMock(spec=IRepository)
    mapper = MagicMock(spec=IMapper)
    collector = ConcreteCollector(None, {})
    collector._repository = repo
    collector._mapper = mapper

    asset = MagicMock(spec=Asset)
    asset.external_id = "123"

    repo.get_raw_assets.return_value = [{"raw": "asset"}]
    mapper.to_asset.return_value = asset

    repo.get_raw_accesses.return_value = [{"asset_id": "123"}]
    mapper.to_access.return_value = MagicMock(spec=Access)

    results = list(collector.collect_accesses())
    assert len(results) == 1
    mapper.to_access.assert_called_once_with({"asset_id": "123"}, asset=asset)


def test_collector_optional_methods():
    """Verify that optional hook methods in Collector return empty collections by default."""
    collector = ConcreteCollector(None, {})
    assert collector.collect_groups() == []
    assert collector.collect_permissions() == []


def test_abstract_methods_raise():
    """Verify that attempting to instantiate abstract ports or accessing non-implemented properties raises exceptions."""

    class IncompleteCollector(Collector):
        @property
        def source_name(self) -> str:
            return "s"

        @property
        def instance_id(self) -> str:
            return "i"

        def health_check(self) -> bool:
            return True

    # Testing Collector abstract properties
    class TrulyIncompleteCollector(Collector):
        pass

    incomplete = TrulyIncompleteCollector(None, {})
    with pytest.raises(NotImplementedError):
        _ = incomplete.source_name

    with pytest.raises(NotImplementedError):
        _ = incomplete.instance_id

    # Testing Mapper and Repository raise TypeError on instantiation
    class IncompleteMapper(IMapper):
        pass

    with pytest.raises(TypeError):
        IncompleteMapper()  # type: ignore

    class IncompleteRepository(IRepository):
        pass

    with pytest.raises(TypeError):
        IncompleteRepository()  # type: ignore
