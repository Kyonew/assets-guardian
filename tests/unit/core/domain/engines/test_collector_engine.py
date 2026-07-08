"""Tests for the collector engine."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from assets_guardian.core.cache.cache import CacheManager
from assets_guardian.core.domain.engines.collector_engine import CollectorEngine, CollectorResult
from assets_guardian.core.domain.models.access import Access
from assets_guardian.core.domain.models.asset import Asset
from assets_guardian.core.domain.models.context import AssetsGuardianMode
from assets_guardian.core.domain.models.identity import Identity


@pytest.fixture
def mock_cache():
    """Provide a mock cache manager for tests."""
    return MagicMock(spec=CacheManager)


@pytest.fixture
def mock_collector():
    """Provide a mock collector with basic metadata configured."""
    collector = MagicMock()
    collector.source_name = "test_source"
    collector.instance_id = "test_instance"
    return collector


def test_collector_engine_init(mocker):
    """Verify that CollectorEngine initializes cache correctly, allowing overrides."""
    mocker.patch("assets_guardian.core.domain.engines.collector_engine.CacheManager")
    engine = CollectorEngine()
    assert engine.cache is not None

    custom_cache = MagicMock(spec=CacheManager)
    engine2 = CollectorEngine(cache=custom_cache)
    assert engine2.cache == custom_cache


def test_collector_engine_run_collect_no_cache(mock_cache, mock_collector):
    """Verify that collection is performed and cached when no checkpoint exists."""
    engine = CollectorEngine(cache=mock_cache)
    mock_cache.has_checkpoint.return_value = False
    mock_cache.get_file_path.return_value = Path("dummy")

    mock_collector.collect_identities.return_value = iter([MagicMock(spec=Identity)])
    mock_collector.collect_assets.return_value = iter([MagicMock(spec=Asset)])
    mock_collector.collect_accesses.return_value = iter([MagicMock(spec=Access)])

    mock_cache.load_iterable.side_effect = [
        [MagicMock(spec=Identity)],
        [MagicMock(spec=Asset)],
        [MagicMock(spec=Access)],
    ]

    result = engine.run_collect(mock_collector, AssetsGuardianMode.AUDIT)

    assert result.success is True
    assert mock_cache.save.call_count == 3
    assert mock_collector.collect_identities.called
    assert mock_collector.collect_assets.called
    assert mock_collector.collect_accesses.called


def test_collector_engine_run_collect_with_cache(mock_cache, mock_collector):
    """Verify that collection is skipped when a valid checkpoint exists in sync mode."""
    engine = CollectorEngine(cache=mock_cache)
    mock_cache.has_checkpoint.return_value = True
    mock_cache.get_file_path.return_value = Path("dummy")

    result = engine.run_collect(mock_collector, AssetsGuardianMode.SYNC)

    assert result.success is True
    assert not mock_collector.collect_identities.called
    assert not mock_cache.save.called


def test_collector_engine_run_collect_exception(mock_cache, mock_collector):
    """Verify error propagation when the cache check raises an exception."""
    engine = CollectorEngine(cache=mock_cache)
    mock_cache.get_file_path.return_value = Path("dummy")
    mock_cache.has_checkpoint.side_effect = Exception("Checkpoint error")

    result = engine.run_collect(mock_collector, AssetsGuardianMode.AUDIT)

    assert result.success is False
    assert result.error == "Checkpoint error"


def test_collector_result_default_values():
    """Verify default field values of the CollectorResult model."""
    res = CollectorResult(source_name="s", instance_id="i")
    assert res.success is True
    assert res.identities == []
    assert res.assets == []
    assert res.accesses == []
    assert res.error is None
