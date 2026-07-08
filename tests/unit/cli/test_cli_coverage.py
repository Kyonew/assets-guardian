"""Coverage test assertions for CLI execution flows when check engine fails."""

from unittest.mock import MagicMock, patch

import pytest

from assets_guardian.cli.audit import run_audit_command
from assets_guardian.cli.sync import run_sync_command
from assets_guardian.core.domain.models.context import Context


@pytest.fixture
def mock_ctx():
    """Provide a mock Context with preset GitLab integrations and cache path configurations."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.integrations = {"gitlab": {"prod": {}}}
    ctx.app_config.paths.pdf.clean_path = "report.pdf"
    ctx.app_config.paths.pdf_config.clean_path = "pdf_config.json"
    ctx.app_config.paths.rules_config.clean_path = "rules.yml"
    ctx.app_config.cache.batch_size = 64
    ctx.app_config.cache.cache_dir = ".test_cache"
    return ctx


def test_run_audit_command_check_failure(mock_ctx):
    """Verify that run_audit_command raises a RuntimeError if the config check fails."""
    with patch("assets_guardian.cli.audit.CheckEngine") as mock_check_cls:
        mock_check = mock_check_cls.return_value
        mock_check.run.return_value = False

        with pytest.raises(RuntimeError, match="Configuration error"):
            run_audit_command(mock_ctx)


def test_run_sync_command_check_failure(mock_ctx):
    """Verify that run_sync_command raises a RuntimeError if the config check fails."""
    with patch("assets_guardian.cli.sync.CheckEngine") as mock_check_cls:
        mock_check = mock_check_cls.return_value
        mock_check.run.return_value = False

        with pytest.raises(RuntimeError, match="Configuration error"):
            run_sync_command(mock_ctx)
