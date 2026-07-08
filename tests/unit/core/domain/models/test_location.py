"""Tests for the Location model representing local or remote paths."""

from pathlib import Path
from unittest import mock

import pytest

from assets_guardian.core.domain.models.location import Location, PathType


def test_location_init_local() -> None:
    """Verify that a local path is correctly parsed with LOCAL PathType and is_local set to True."""
    loc = Location("local:path/to/file")
    assert loc.raw_path == "local:path/to/file"
    assert loc.clean_path == "path/to/file"
    assert loc.path_type == PathType.LOCAL
    assert loc.is_local is True
    assert loc.is_remote is False


def test_location_init_remote() -> None:
    """Verify that a remote path is correctly parsed with REMOTE PathType and is_remote set to True."""
    loc = Location("remote:hostname/path")
    assert loc.raw_path == "remote:hostname/path"
    assert loc.clean_path == "hostname/path"
    assert loc.path_type == PathType.REMOTE
    assert loc.is_local is False
    assert loc.is_remote is True


def test_location_init_unknown() -> None:
    """Verify that Location raises a ValueError when initialized with an invalid or missing prefix."""
    with pytest.raises(ValueError, match="Invalid or missing prefix"):
        Location("invalid:path")

    with pytest.raises(ValueError, match="Invalid or missing prefix"):
        Location("just_a_path")


def test_validate_location_remote_not_implemented() -> None:
    """Verify that validating remote paths raises a NotImplementedError as it is not supported yet."""
    loc = Location("remote:path")
    with pytest.raises(
        NotImplementedError, match=r"Validation of remote paths is not supported yet."
    ):
        loc.validate_location()


def test_validate_location_invalid_prefix() -> None:
    """Verify that location validation raises ValueError if the prefix is invalid."""
    with pytest.raises(ValueError, match="Invalid or missing prefix"):
        Location("invalid:path")


def test_validate_location_local_file_exists(tmp_path: Path) -> None:
    """Verify that validate_location successfully validates an existing local file."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    loc = Location(f"local:{file_path}")

    # Should not raise any exception
    loc.validate_location(require_exists=True)


def test_validate_location_local_file_not_exists_optional(tmp_path: Path) -> None:
    """Verify that validate_location succeeds when a file does not exist but is not required to exist."""
    non_existing = tmp_path / "does_not_exist.txt"
    loc = Location(f"local:{non_existing}")

    # Should not raise any exception Since require_exists is False
    loc.validate_location(require_exists=False)


def test_validate_location_local_file_not_exists_required() -> None:
    """Verify that validate_location raises FileNotFoundError when a required file does not exist."""
    loc = Location("local:non_existing.txt")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        loc.validate_location(require_exists=True)


def test_validate_location_folder_exists(tmp_path: Path) -> None:
    """Verify that validate_location successfully validates an existing folder."""
    loc = Location(f"local:{tmp_path}")

    # Should not raise exception
    loc.validate_location(is_folder=True, require_exists=True)


def test_validate_location_folder_not_directory(tmp_path: Path) -> None:
    """Verify that validate_location raises NotADirectoryError when a file is checked as a folder."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    loc = Location(f"local:{file_path}")

    with pytest.raises(NotADirectoryError, match="is not a directory"):
        loc.validate_location(is_folder=True)


def test_validate_location_folder_not_exists_required(tmp_path: Path) -> None:
    """Verify that validate_location raises NotADirectoryError when a required folder does not exist."""
    non_existing = tmp_path / "does_not_exist"
    loc = Location(f"local:{non_existing}")

    with pytest.raises(NotADirectoryError, match="not found"):
        loc.validate_location(is_folder=True, require_exists=True)


def test_location_extract_clean_path_no_colon() -> None:
    """Test the branch in __extract_clean_path when no colon is present in the path string using mocks."""
    # Mock __determine_path_type so it does not raise an exception even if the prefix is absent.
    with mock.patch.object(Location, "_Location__determine_path_type", return_value=PathType.LOCAL):
        loc = Location("path_without_colon")
        assert loc.clean_path == "path_without_colon"
