from enum import StrEnum
from pathlib import Path


class PathType(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class Location:
    """Representation and validation of a file location (local or remote).

    This class parses a prefixed path (e.g., 'local:./outputs/file.xlsx'), identifies
    its type, and validates its existence.

    Attributes:
        raw_path: The original raw path with prefix (e.g., local:./outputs).
        path_type: The path type (LOCAL, REMOTE).
        clean_path: The path without the prefix.
    """

    raw_path: str
    path_type: PathType
    clean_path: str
    is_local: bool
    is_remote: bool

    def __init__(self, raw_path: str) -> None:
        """Initializes a new Location instance.

        Args:
            raw_path: The prefixed path (e.g., 'local:./outputs/file.xlsx').
        """
        self.raw_path = raw_path
        self.path_type = self.__determine_path_type()
        self.clean_path = self.__extract_clean_path()
        self.is_local = self.path_type == PathType.LOCAL
        self.is_remote = self.path_type == PathType.REMOTE

    def __determine_path_type(self) -> PathType:
        """Identifies the path type based on the prefix.

        Returns:
            PathType: The path type (LOCAL, REMOTE).
        """

        if self.raw_path.startswith(f"{PathType.REMOTE}:"):
            return PathType.REMOTE

        if self.raw_path.startswith(f"{PathType.LOCAL}:"):
            return PathType.LOCAL

        raise ValueError(f"Invalid or missing prefix in: {self.raw_path!r}")

    def __extract_clean_path(self) -> str:
        """Extracts the clean path after the ':' separator.

        Returns:
            str: The cleaned path or the raw path if no separator is found.
        """

        if ":" in self.raw_path:
            return self.raw_path.split(":", 1)[1]

        return self.raw_path

    def validate_location(
        self,
        is_folder: bool = False,
        require_exists: bool = False,
    ) -> None:
        """Validates the consistency of the path.

        Args:
            is_folder: If True, asserts that the path points to a directory.
            require_exists: If True, physical existence of the path is required.

        Raises:
            NotImplementedError: If the prefix is 'remote' (unsupported currently).
            ValueError: If the prefix is missing or invalid.
            NotADirectoryError: If is_folder is True but the path is not a directory.
            FileNotFoundError: If require_exists is True but the path is not found.
        """
        if self.is_remote:
            raise NotImplementedError("Validation of remote paths is not supported yet.")

        path_obj = Path(self.clean_path)

        if require_exists and not path_obj.exists():
            if is_folder:
                raise NotADirectoryError(f"Directory {self.clean_path!r} not found.")
            raise FileNotFoundError(f"File {self.clean_path!r} does not exist.")

        if is_folder and path_obj.exists() and not path_obj.is_dir():
            raise NotADirectoryError(f"Path {self.clean_path!r} exists but is not a directory.")
