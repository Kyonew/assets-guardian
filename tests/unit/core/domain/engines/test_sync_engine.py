"""Tests for the sync engine."""

from unittest.mock import MagicMock

from assets_guardian.core.cache.cache import CacheManager
from assets_guardian.core.domain.engines.sync_engine import SyncEngine
from assets_guardian.core.domain.models.context import AssetsGuardianMode


def test_sync_engine_init():
    """Verify that SyncEngine initializes cache and collector engine dependencies correctly."""
    cache = MagicMock(spec=CacheManager)
    engine = SyncEngine(cache=cache)
    assert engine.cache == cache
    assert engine.collector_engine is not None


def test_sync_engine_run_no_collectors(mocker, caplog):
    """Verify SyncEngine behavior and warnings when run without any collectors."""
    mocker.patch("assets_guardian.core.domain.engines.sync_engine.CacheManager")
    engine = SyncEngine()
    with caplog.at_level("WARNING"):
        engine.run(collectors=[])
    assert "No collectors provided to SyncEngine." in caplog.text


def test_sync_engine_run_success(mocker):
    """Verify that SyncEngine successfully triggers collector runs in sync mode."""
    cache = MagicMock(spec=CacheManager)
    engine = SyncEngine(cache=cache)

    collector = MagicMock()
    collector.source_name = "test_source"
    collector.instance_id = "test_instance"

    mock_run_collect = mocker.patch.object(engine.collector_engine, "run_collect")

    engine.run(collectors=[collector])

    # Should run collect with SYNC mode
    mock_run_collect.assert_called_once_with(collector, mode=AssetsGuardianMode.SYNC)
