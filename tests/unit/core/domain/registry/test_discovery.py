from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from assets_guardian.core.domain.models.context import AssetsGuardianMode, Context
from assets_guardian.core.domain.registry.discovery import (
    discover_all,
    discover_default_rules,
    load_client,
    load_collector,
    load_pdf_builders,
    load_rules,
    load_sheet_builders,
)


@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=Context)
    ctx.mode = AssetsGuardianMode.AUDIT
    ctx.app_config.integrations = ["test_plugin"]
    return ctx


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_discover_default_rules_success(mock_import):
    discover_default_rules()
    mock_import.assert_called_once_with("assets_guardian.plugins.default_rules")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_discover_default_rules_import_error(mock_import):
    mock_import.side_effect = ImportError
    discover_default_rules()  # Should not raise


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_discover_default_rules_other_error(mock_import):
    mock_import.side_effect = Exception("error")
    discover_default_rules()  # Should not raise


@patch("assets_guardian.core.domain.registry.discovery.DIR_PLUGINS")
def test_discover_all_no_dir(mock_dir, mock_ctx):
    mock_dir.exists.return_value = False
    discover_all(mock_ctx)
    assert not mock_dir.iterdir.called


@patch("assets_guardian.core.domain.registry.discovery.DIR_PLUGINS")
@patch("assets_guardian.core.domain.registry.discovery.load_client")
@patch("assets_guardian.core.domain.registry.discovery.load_collector")
@patch("assets_guardian.core.domain.registry.discovery.load_rules")
@patch("assets_guardian.core.domain.registry.discovery.load_pdf_builders")
@patch("assets_guardian.core.domain.registry.discovery.discover_default_rules")
def test_discover_all_success(
    mock_def, mock_pdf, mock_rules, mock_coll, mock_client, mock_dir, mock_ctx
):
    mock_dir.exists.return_value = True
    plugin_path = MagicMock(spec=Path)
    plugin_path.is_dir.return_value = True
    plugin_path.name = "test_plugin"
    mock_dir.iterdir.return_value = [plugin_path]

    discover_all(mock_ctx)

    mock_def.assert_called_once()
    mock_client.assert_called_once()
    mock_coll.assert_called_once()
    mock_rules.assert_called_once()
    mock_pdf.assert_called_once()

    # Test with hidden dir
    hidden_path = MagicMock(spec=Path)
    hidden_path.is_dir.return_value = True
    hidden_path.name = ".hidden"
    mock_dir.iterdir.return_value = [plugin_path, hidden_path]
    discover_all(mock_ctx)  # Should skip .hidden

    # Test repeated discovery (branch _DISCOVERED)
    discover_all(mock_ctx)


@patch("assets_guardian.core.domain.registry.discovery.DIR_PLUGINS")
@patch("assets_guardian.core.domain.registry.discovery.load_sheet_builders")
def test_discover_all_sync(mock_sheet, mock_dir, mock_ctx):
    mock_ctx.mode = AssetsGuardianMode.SYNC
    mock_dir.exists.return_value = True
    plugin_path = MagicMock(spec=Path)
    plugin_path.is_dir.return_value = True
    plugin_path.name = "test_plugin"
    mock_dir.iterdir.return_value = [plugin_path]

    discover_all(mock_ctx)
    mock_sheet.assert_called_once()


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_client(mock_import):
    path = MagicMock(spec=Path)
    (path / "client.py").exists.return_value = True
    load_client(path, "p")
    mock_import.assert_called_once_with("assets_guardian.plugins.p.client")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_client_error(mock_import):
    path = MagicMock(spec=Path)
    (path / "client.py").exists.return_value = True
    mock_import.side_effect = Exception("error")
    load_client(path, "p")  # Should not raise


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_collector(mock_import):
    path = MagicMock(spec=Path)
    (path / "collector.py").exists.return_value = True
    load_collector(path, "p")
    mock_import.assert_called_once_with("assets_guardian.plugins.p.collector")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_rules(mock_import):
    path = MagicMock(spec=Path)
    (path / "rules.py").exists.return_value = True
    load_rules(path, "p")
    mock_import.assert_called_once_with("assets_guardian.plugins.p.rules")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_sheet_builders(mock_import):
    path = MagicMock(spec=Path)
    (path / "sheet_builders.py").exists.return_value = True
    load_sheet_builders(path, "p")
    mock_import.assert_called_once_with("assets_guardian.plugins.p.sheet_builders")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_pdf_builders(mock_import):
    path = MagicMock(spec=Path)
    (path / "pdf_builder.py").exists.return_value = True
    load_pdf_builders(path, "p")
    mock_import.assert_called_once_with("assets_guardian.plugins.p.pdf_builder")


def test_load_components_missing_files():
    path = MagicMock(spec=Path)
    (path / "client.py").exists.return_value = False
    (path / "collector.py").exists.return_value = False
    (path / "rules.py").exists.return_value = False
    (path / "sheet_builders.py").exists.return_value = False
    (path / "pdf_builder.py").exists.return_value = False

    with patch(
        "assets_guardian.core.domain.registry.discovery.importlib.import_module"
    ) as mock_import:
        load_client(path, "p")
        load_collector(path, "p")
        load_rules(path, "p")
        load_sheet_builders(path, "p")
        load_pdf_builders(path, "p")

        assert not mock_import.called


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_collector_error(mock_import):
    path = MagicMock(spec=Path)
    (path / "collector.py").exists.return_value = True
    mock_import.side_effect = Exception("error")
    load_collector(path, "p")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_rules_error(mock_import):
    path = MagicMock(spec=Path)
    (path / "rules.py").exists.return_value = True
    mock_import.side_effect = Exception("error")
    load_rules(path, "p")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_sheet_builders_error(mock_import):
    path = MagicMock(spec=Path)
    (path / "sheet_builders.py").exists.return_value = True
    mock_import.side_effect = Exception("error")
    load_sheet_builders(path, "p")


@patch("assets_guardian.core.domain.registry.discovery.importlib.import_module")
def test_load_pdf_builders_error(mock_import):
    path = MagicMock(spec=Path)
    (path / "pdf_builder.py").exists.return_value = True
    mock_import.side_effect = Exception("error")
    load_pdf_builders(path, "p")


@patch("assets_guardian.core.domain.registry.discovery.DIR_PLUGINS")
@patch("assets_guardian.core.domain.registry.discovery.load_client")
@patch("assets_guardian.core.domain.registry.discovery.load_collector")
def test_discover_all_skips_plugin_absent_from_config(
    mock_coll, mock_client, mock_dir, mock_ctx
) -> None:
    """discover_all() skips plugins that are not listed in app_config.integrations."""
    mock_ctx.mode = AssetsGuardianMode.SYNC
    mock_dir.exists.return_value = True

    plugin_path = MagicMock(spec=Path)
    plugin_path.is_dir.return_value = True
    plugin_path.name = "unknown_plugin"
    mock_dir.iterdir.return_value = [plugin_path]

    # The plugin is NOT in the integrations config
    mock_ctx.app_config.integrations = {}

    discover_all(mock_ctx)

    # No loading should have been attempted for the absent plugin
    mock_client.assert_not_called()
    mock_coll.assert_not_called()
