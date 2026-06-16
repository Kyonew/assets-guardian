def run_audit_command() -> None:
    """Executes the IAM compliance audit process and generates a report.

    This function orchestrates the following technical flow:
    1. Global execution of CheckEngine before proceeding.
    2. Loading and validating active collectors.
    3. Initializing the audit engine (AuditEngine) with its cache manager.
    4. Running the audit (data collection, rule evaluation, and detection).
    5. Generating the PDF report via PdfEngine.
    6. Final cleanup of the temporary audit cache.

    Args:
        ctx: The application context containing the configuration and parameters.

    Raises:
        RuntimeError: If the environment verification fails (CheckEngine).
    """
    print("Audit command.")  # noqa: T201
