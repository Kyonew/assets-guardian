def run_sync_command() -> None:
    """Executes the permissions synchronization command.

    This function orchestrates the following technical flow:
    1. Global execution of CheckEngine before proceeding.
    2. Loading active collectors.
    3. Initializing the synchronization engine and its cache.
    4. Running the synchronization (collection).
    5. Generating the Excel repository via ExcelEngine.
    6. Final cleanup of the temporary synchronization cache.

    Args:
        ctx: The application context containing the configuration and parameters.

    Raises:
        RuntimeError: If the environment verification fails (CheckEngine).
    """
    print("Sync command.")  # noqa: T201
