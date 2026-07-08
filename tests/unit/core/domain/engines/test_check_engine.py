import os
from unittest.mock import MagicMock, patch

import pytest

from assets_guardian.core.domain.engines.check_engine import CheckEngine
from assets_guardian.core.domain.models.context import AssetsGuardianMode, Context


@pytest.fixture
def engine() -> CheckEngine:
    return CheckEngine()


@pytest.fixture
def quiet_ctx() -> MagicMock:
    """Context with quiet=True to suppress console output."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.CHECK
    ctx.app_config.integrations = {}
    return ctx


@pytest.fixture
def loud_ctx() -> MagicMock:
    """Context with quiet=False to exercise all console output paths."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = False
    ctx.mode = AssetsGuardianMode.CHECK
    ctx.app_config.integrations = {}
    return ctx


# ---------------------------------------------------------------------------
# run(), top-level orchestration
# ---------------------------------------------------------------------------


def test_run_success_quiet(engine: CheckEngine, quiet_ctx: MagicMock) -> None:
    """run() returns True when all details pass and output is suppressed."""
    details = {"config": True, "employees": True, "excel": True, "folders": True, "instances": {}}
    with patch.object(engine, "run_details", return_value=details):
        assert engine.run(quiet_ctx) is True


def test_run_failure_quiet(engine: CheckEngine, quiet_ctx: MagicMock) -> None:
    """run() returns False when any detail fails."""
    details = {"config": False, "employees": True, "excel": True, "folders": True, "instances": {}}
    with patch.object(engine, "run_details", return_value=details):
        assert engine.run(quiet_ctx) is False


def test_run_not_quiet_all_ok(engine: CheckEngine, loud_ctx: MagicMock) -> None:
    """run() prints a green OPERATIONAL verdict when all checks pass and quiet=False."""
    details = {"config": True, "employees": True, "excel": True, "folders": True, "instances": {}}
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho") as mock_secho,
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
    ):
        result = engine.run(loud_ctx)

    assert result is True
    all_text = " ".join(str(c) for c in mock_secho.call_args_list)
    assert "OPERATIONAL" in all_text


def test_run_not_quiet_with_failures(engine: CheckEngine, loud_ctx: MagicMock) -> None:
    """run() prints a red ERRORS verdict and failure indicators when checks fail."""
    details = {"config": False, "employees": True, "excel": True, "folders": True, "instances": {}}
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho") as mock_secho,
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
    ):
        result = engine.run(loud_ctx)

    assert result is False
    all_text = " ".join(str(c) for c in mock_secho.call_args_list)
    assert "ERRORS" in all_text


def test_run_not_quiet_with_instances(engine: CheckEngine, loud_ctx: MagicMock) -> None:
    """run() renders per-instance connectivity rows when instances are present."""
    details = {
        "config": True,
        "employees": True,
        "excel": True,
        "folders": True,
        "instances": {"gitlab:prod": True, "gitlab:staging": False},
    }
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho"),
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
    ):
        result = engine.run(loud_ctx)

    # One instance fails so overall result is False
    assert result is False


def test_run_not_quiet_partial_instances_yellow_bilan(
    engine: CheckEngine, loud_ctx: MagicMock
) -> None:
    """run() uses click.style with fg='yellow' for the bilan when success is partial."""
    details = {
        "config": True,
        "employees": True,
        "excel": True,
        "folders": True,
        "instances": {"svc:a": True, "svc:b": False},
    }
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho"),
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
        patch(
            "assets_guardian.core.domain.engines.check_engine.click.style",
            wraps=__import__("click").style,
        ) as mock_style,
    ):
        engine.run(loud_ctx)

    style_calls = str(mock_style.call_args_list)
    assert "yellow" in style_calls


def test_run_not_quiet_all_instances_fail_red_bilan(
    engine: CheckEngine, loud_ctx: MagicMock
) -> None:
    """run() produces a red bilan when all instances are inaccessible."""
    details = {
        "config": True,
        "employees": True,
        "excel": True,
        "folders": True,
        "instances": {"svc:a": False, "svc:b": False},
    }
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho") as mock_secho,
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
    ):
        engine.run(loud_ctx)

    all_text = str(mock_secho.call_args_list)
    assert "red" in all_text


def test_run_not_quiet_no_instances_configured(engine: CheckEngine, loud_ctx: MagicMock) -> None:
    """run() shows 'No instances configured.' message when instances dict is empty."""
    details = {"config": True, "employees": True, "excel": True, "folders": True, "instances": {}}
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho"),
        patch("assets_guardian.core.domain.engines.check_engine.click.echo") as mock_echo,
    ):
        engine.run(loud_ctx)

    all_text = str(mock_echo.call_args_list)
    assert "No instances" in all_text


def test_run_not_quiet_in_sync_or_audit_mode_suppresses_console(
    engine: CheckEngine, loud_ctx: MagicMock
) -> None:
    """run() suppresses all console prints when mode is SYNC or AUDIT, even if quiet=False."""
    loud_ctx.mode = AssetsGuardianMode.SYNC
    details = {"config": True, "employees": True, "excel": True, "folders": True, "instances": {}}
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho") as mock_secho,
        patch("assets_guardian.core.domain.engines.check_engine.click.echo") as mock_echo,
    ):
        result = engine.run(loud_ctx)

    assert result is True
    mock_secho.assert_not_called()
    mock_echo.assert_not_called()


# ---------------------------------------------------------------------------
# run_details(), mode-based dispatch
# ---------------------------------------------------------------------------


def test_run_details_sync_mode_excludes_audit_keys(engine: CheckEngine) -> None:
    """run_details() omits rules_config and pdf entries in SYNC mode."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {}

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
    ):
        details = engine.run_details(ctx)

    assert "rules_config" not in details
    assert "pdf" not in details
    assert "instances" in details


def test_run_details_audit_mode_includes_rules_and_pdf(engine: CheckEngine) -> None:
    """run_details() includes rules_config and pdf entries in AUDIT mode."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.AUDIT
    ctx.app_config.integrations = {}

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_rules_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_pdf_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
    ):
        details = engine.run_details(ctx)

    assert "rules_config" in details
    assert "pdf" in details


def test_run_details_check_mode_includes_rules_and_pdf(engine: CheckEngine) -> None:
    """run_details() includes rules_config and pdf entries in CHECK (default) mode."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.CHECK
    ctx.app_config.integrations = {}

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_rules_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_pdf_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
    ):
        details = engine.run_details(ctx)

    assert "rules_config" in details
    assert "pdf" in details


def test_run_details_with_accessible_instance(engine: CheckEngine) -> None:
    """run_details() marks an instance accessible when health_check returns True."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {"gitlab": {"prod": {"url": "http://gitlab"}}}

    mock_provider = MagicMock()
    mock_provider.health_check.return_value = True

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
        patch(
            "assets_guardian.core.domain.engines.check_engine."
            "ClientProviderRegistry.instantiates_clientprovider",
            return_value=mock_provider,
        ),
    ):
        details = engine.run_details(ctx)

    assert details["instances"]["gitlab:prod"] is True


def test_run_details_with_inaccessible_instance(engine: CheckEngine) -> None:
    """run_details() marks an instance inaccessible when health_check returns False."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {"gitlab": {"prod": {"url": "http://gitlab"}}}

    mock_provider = MagicMock()
    mock_provider.health_check.return_value = False

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
        patch(
            "assets_guardian.core.domain.engines.check_engine."
            "ClientProviderRegistry.instantiates_clientprovider",
            return_value=mock_provider,
        ),
    ):
        details = engine.run_details(ctx)

    assert details["instances"]["gitlab:prod"] is False


def test_run_details_instance_connectivity_exception(engine: CheckEngine) -> None:
    """run_details() marks an instance False when connectivity check raises."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {"gitlab": {"prod": None}}

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
        patch(
            "assets_guardian.core.domain.engines.check_engine."
            "ClientProviderRegistry.instantiates_clientprovider",
            side_effect=Exception("Connection refused"),
        ),
    ):
        details = engine.run_details(ctx)

    assert details["instances"]["gitlab:prod"] is False


def test_run_details_none_params_gets_instance_id_injected(engine: CheckEngine) -> None:
    """run_details() injects instance_id into params when params is None."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {"gitlab": {"prod": None}}

    mock_provider = MagicMock()
    mock_provider.health_check.return_value = True

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
        patch(
            "assets_guardian.core.domain.engines.check_engine."
            "ClientProviderRegistry.instantiates_clientprovider",
            return_value=mock_provider,
        ) as mock_instantiate,
    ):
        engine.run_details(ctx)

    _, call_params = mock_instantiate.call_args[0]
    assert call_params.get("instance_id") == "prod"


def test_run_details_instance_id_already_in_params_not_overwritten(engine: CheckEngine) -> None:
    """run_details() does not overwrite instance_id when it is already set in params."""
    ctx = MagicMock(spec=Context)
    ctx.quiet = True
    ctx.mode = AssetsGuardianMode.SYNC
    ctx.app_config.integrations = {"gitlab": {"prod": {"instance_id": "custom", "url": "http://x"}}}

    mock_provider = MagicMock()
    mock_provider.health_check.return_value = True

    with (
        patch.object(engine, "_CheckEngine__check_config_yaml", return_value=True),
        patch.object(engine, "_CheckEngine__check_employees_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_excel_json", return_value=True),
        patch.object(engine, "_CheckEngine__check_folders", return_value=True),
        patch(
            "assets_guardian.core.domain.engines.check_engine."
            "ClientProviderRegistry.instantiates_clientprovider",
            return_value=mock_provider,
        ) as mock_instantiate,
    ):
        engine.run_details(ctx)

    _, call_params = mock_instantiate.call_args[0]
    # Pre-existing instance_id must not be replaced with the dict key "prod"
    assert call_params["instance_id"] == "custom"


# ---------------------------------------------------------------------------
# __check_config_yaml
# ---------------------------------------------------------------------------


def test_check_config_yaml_success(engine: CheckEngine, tmp_path: object) -> None:
    """Returns True when both config and template files load and validate correctly."""
    config_file = tmp_path / "config.yml"  # type: ignore[operator]
    template_file = tmp_path / "template.config.yml"  # type: ignore[operator]
    config_file.write_text("key: value")
    template_file.write_text("key: required")

    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.config_path.clean_path = str(config_file)

    with (
        patch("assets_guardian.core.domain.engines.check_engine.load_yaml_config", return_value={}),
        patch("assets_guardian.core.domain.engines.check_engine.validate_config"),
    ):
        result = engine._CheckEngine__check_config_yaml(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_config_yaml_template_not_found(engine: CheckEngine, tmp_path: object) -> None:
    """Returns False when the template.config.yml file is missing."""
    config_file = tmp_path / "config.yml"  # type: ignore[operator]
    config_file.write_text("key: value")

    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.config_path.clean_path = str(config_file)

    result = engine._CheckEngine__check_config_yaml(ctx)  # type: ignore[attr-defined]

    assert result is False


def test_check_config_yaml_validation_error(engine: CheckEngine, tmp_path: object) -> None:
    """Returns False when validate_config raises."""
    config_file = tmp_path / "config.yml"  # type: ignore[operator]
    template_file = tmp_path / "template.config.yml"  # type: ignore[operator]
    config_file.write_text("key: value")
    template_file.write_text("key: required")

    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.config_path.clean_path = str(config_file)

    with (
        patch("assets_guardian.core.domain.engines.check_engine.load_yaml_config", return_value={}),
        patch(
            "assets_guardian.core.domain.engines.check_engine.validate_config",
            side_effect=ValueError("Invalid"),
        ),
    ):
        result = engine._CheckEngine__check_config_yaml(ctx)  # type: ignore[attr-defined]

    assert result is False


# ---------------------------------------------------------------------------
# __check_rules_config_yaml
# ---------------------------------------------------------------------------


def test_check_rules_config_yaml_success(engine: CheckEngine) -> None:
    """Returns True when rules YAML loads without error."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.rules_config.clean_path = "/rules.yml"

    with patch(
        "assets_guardian.core.domain.engines.check_engine.load_yaml_config",
        return_value={"rules": []},
    ):
        result = engine._CheckEngine__check_rules_config_yaml(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_rules_config_yaml_error(engine: CheckEngine) -> None:
    """Returns False when load_yaml_config raises for the rules file."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.rules_config.clean_path = "/nonexistent/rules.yml"

    with patch(
        "assets_guardian.core.domain.engines.check_engine.load_yaml_config",
        side_effect=FileNotFoundError("not found"),
    ):
        result = engine._CheckEngine__check_rules_config_yaml(ctx)  # type: ignore[attr-defined]

    assert result is False


# ---------------------------------------------------------------------------
# __check_employees_json
# ---------------------------------------------------------------------------


def test_check_employees_json_success(engine: CheckEngine) -> None:
    """Returns True when employees JSON loads without error."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.employees.clean_path = "/employees.json"

    with patch("assets_guardian.core.domain.engines.check_engine.load_json", return_value=[]):
        result = engine._CheckEngine__check_employees_json(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_employees_json_error(engine: CheckEngine) -> None:
    """Returns False when load_json raises for the employees file."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.employees.clean_path = "/missing.json"

    with patch(
        "assets_guardian.core.domain.engines.check_engine.load_json",
        side_effect=FileNotFoundError("not found"),
    ):
        result = engine._CheckEngine__check_employees_json(ctx)  # type: ignore[attr-defined]

    assert result is False


# ---------------------------------------------------------------------------
# __check_excel_json
# ---------------------------------------------------------------------------


def test_check_excel_json_success(engine: CheckEngine) -> None:
    """Returns True when excel_config JSON loads without error."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.excel_config.clean_path = "/excel_config.json"

    with patch("assets_guardian.core.domain.engines.check_engine.load_json", return_value={}):
        result = engine._CheckEngine__check_excel_json(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_excel_json_error(engine: CheckEngine) -> None:
    """Returns False when load_json raises for the excel config file."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.excel_config.clean_path = "/bad.json"

    with patch(
        "assets_guardian.core.domain.engines.check_engine.load_json",
        side_effect=ValueError("Invalid JSON"),
    ):
        result = engine._CheckEngine__check_excel_json(ctx)  # type: ignore[attr-defined]

    assert result is False


# ---------------------------------------------------------------------------
# __check_pdf_json
# ---------------------------------------------------------------------------


def test_check_pdf_json_success(engine: CheckEngine) -> None:
    """Returns True when pdf_config JSON loads without error."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.pdf_config.clean_path = "/pdf_config.json"

    with patch("assets_guardian.core.domain.engines.check_engine.load_json", return_value={}):
        result = engine._CheckEngine__check_pdf_json(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_pdf_json_error(engine: CheckEngine) -> None:
    """Returns False when load_json raises for the pdf config file."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.paths.pdf_config.clean_path = "/bad.json"

    with patch(
        "assets_guardian.core.domain.engines.check_engine.load_json",
        side_effect=FileNotFoundError("not found"),
    ):
        result = engine._CheckEngine__check_pdf_json(ctx)  # type: ignore[attr-defined]

    assert result is False


# ---------------------------------------------------------------------------
# __check_folders
# ---------------------------------------------------------------------------


def test_check_folders_all_exist_readable_writable(engine: CheckEngine) -> None:
    """Returns True when every folder exists and has full permissions."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    with (
        patch(
            "assets_guardian.core.domain.engines.check_engine.Path",
            side_effect=lambda _: MagicMock(exists=lambda: True),
        ),
        patch("assets_guardian.core.domain.engines.check_engine.os.access", return_value=True),
    ):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_folders_rw_missing_creates_successfully(engine: CheckEngine) -> None:
    """Returns True when missing r+w folders are created via mkdir (read-only 'config' exists)."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    def path_factory(path_str: str) -> MagicMock:
        m = MagicMock()
        # The read-only "config" folder must exist; r+w folders are missing but creatable
        m.exists.return_value = str(path_str) == "config"
        return m

    with (
        patch("assets_guardian.core.domain.engines.check_engine.Path", side_effect=path_factory),
        patch("assets_guardian.core.domain.engines.check_engine.os.access", return_value=True),
    ):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is True


def test_check_folders_read_only_folder_missing_returns_false(engine: CheckEngine) -> None:
    """Returns False when the read-only 'config' folder does not exist."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    def path_factory(path_str: str) -> MagicMock:
        m = MagicMock()
        # Simulate the read-only 'config' folder as missing
        m.exists.return_value = str(path_str) != "config"
        return m

    with (
        patch("assets_guardian.core.domain.engines.check_engine.Path", side_effect=path_factory),
        patch("assets_guardian.core.domain.engines.check_engine.os.access", return_value=True),
    ):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is False


def test_check_folders_not_readable_returns_false(engine: CheckEngine) -> None:
    """Returns False when any folder is not readable."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    with (
        patch(
            "assets_guardian.core.domain.engines.check_engine.Path",
            side_effect=lambda _: MagicMock(exists=lambda: True),
        ),
        patch(
            "assets_guardian.core.domain.engines.check_engine.os.access",
            side_effect=lambda _, mode: mode != os.R_OK,
        ),
    ):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is False


def test_check_folders_not_writable_returns_false(engine: CheckEngine) -> None:
    """Returns False when an r+w folder is not writable."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    with (
        patch(
            "assets_guardian.core.domain.engines.check_engine.Path",
            side_effect=lambda _: MagicMock(exists=lambda: True),
        ),
        patch(
            "assets_guardian.core.domain.engines.check_engine.os.access",
            side_effect=lambda _, mode: mode != os.W_OK,
        ),
    ):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is False


def test_run_not_quiet_all_instances_accessible_green_bilan(
    engine: CheckEngine, loud_ctx: MagicMock
) -> None:
    """run() passes fg='green' to click.style for the bilan when all instances succeed."""
    details = {
        "config": True,
        "employees": True,
        "excel": True,
        "folders": True,
        "instances": {"svc:a": True, "svc:b": True},
    }
    with (
        patch.object(engine, "run_details", return_value=details),
        patch("assets_guardian.core.domain.engines.check_engine.click.secho"),
        patch("assets_guardian.core.domain.engines.check_engine.click.echo"),
        patch(
            "assets_guardian.core.domain.engines.check_engine.click.style",
            wraps=__import__("click").style,
        ) as mock_style,
    ):
        result = engine.run(loud_ctx)

    assert result is True
    style_calls = str(mock_style.call_args_list)
    assert "green" in style_calls


def test_check_folders_mkdir_fails_returns_false(engine: CheckEngine) -> None:
    """Returns False when mkdir raises for a missing r+w folder."""
    ctx = MagicMock(spec=Context)
    ctx.app_config.cache.cache_dir = ".cache"

    def path_factory(path_str: str) -> MagicMock:
        m = MagicMock()
        m.exists.return_value = False
        m.mkdir.side_effect = PermissionError("Permission denied")
        return m

    with patch("assets_guardian.core.domain.engines.check_engine.Path", side_effect=path_factory):
        result = engine._CheckEngine__check_folders(ctx)  # type: ignore[attr-defined]

    assert result is False
