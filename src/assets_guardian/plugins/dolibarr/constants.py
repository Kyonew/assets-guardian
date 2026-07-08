from typing import Any

SOURCE_NAME = "dolibarr"
DEFAULT_INSTANCE_ID = ""

# Sheet names
SHEET_NAME_USERS = "Dolibarr Users"
SHEET_NAME_GROUPS = "Dolibarr Groups"

# Modules considered critical for matrix rules
CRITICAL_MODULES = frozenset({"user", "banque", "facture", "societe"})

# Labels of main modules
MODULE_LABELS: dict[str, str] = {
    "facture": "Invoicing",
    "propale": "Commercial proposals",
    "produit": "Products",
    "projet": "Projects",
    "tax": "Taxes",
    "banque": "Bank",
    "societe": "Third parties",
    "user": "Users",
}

# Read permissions in each module (for quick detection)
READ_PERMISSION_KEYS = frozenset({"lire", "read"})

# Correspondence dictionary of Dolibarr permission labels
DOLIBARR_PERMISSIONS_LABELS = {
    "facture": {
        "lire": "Read invoices",
        "creer": "Create and update invoices",
        "supprimer": "Delete invoices",
        "paiement": "Issue payments on invoices",
        "invoice_advance": {
            "validate": "Validate invoices",
            "unvalidate": "Devalidate invoices",
            "send": "Send invoices by email",
        },
    },
    "propale": {
        "lire": "Read commercial proposals",
        "creer": "Create and update commercial proposals",
        "supprimer": "Delete commercial proposals",
        "export": "Exporting commercial proposals and attributes",
        "propal_advance": {
            "validate": "Validate commercial proposals",
            "send": "Send commercial proposals to customers",
            "close": "Close commercial proposals",
        },
    },
    "produit": {
        "lire": "Read products",
        "creer": "Create/modify products",
        "supprimer": "Delete products",
        "export": "Export products",
    },
    "projet": {
        "lire": "Read projects and tasks (shared or of which I am contact)",
        "creer": "Create/modify projects and tasks (shared or of which I am contact)",
        "supprimer": "Delete projects and tasks (shared or of which I am contact)",
        "export": "Export projects",
        "all": {
            "lire": "Read all projects and tasks (including private ones not assigned to me)",
            "creer": "Create/modify all projects and tasks (including private ones not assigned to me)",  # noqa: E501
        },
    },
    "tax": {
        "charges": "Read expenses",
        "charges_advance": {
            "creer": "Create/modify expenses",
            "supprimer": "Delete expenses",
            "export": "Export expenses",
        },
    },
    "banque": {
        "lire": "Read bank account and transactions",
        "cheque": "Manage check sendings",
        "modifier": "Create/modify amount/delete bank entry",
        "configurer": "Configure bank accounts (create, manage categories)",
        "consolidate": "Reconcile bank entries",
        "export": "Export transactions and statements",
        "transfer": "Transfers between accounts",
    },
    "societe": {
        "lire": "Read third parties",
        "creer": "Create and update third parties",
        "supprimer": "Delete third parties",
        "export": "Export third parties",
    },
    "user": {
        "user": {
            "lire": "Read users",
            "supprimer": "Delete users",
        },
        "self": {
            "creer": "Modify own user",
            "password": "Change own password",  # nosec
        },
    },
}


def _get_dict_value(d: dict[str, Any], path_parts: list[str], key: str) -> str | None:
    """Traverses a dictionary along a path of keys and returns the value if it is a str."""
    current = d
    for part in path_parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    if isinstance(current, dict) and key in current:
        val = current[key]
        if isinstance(val, str):
            return val
    return None


def get_permission_label(module: str, permission_key: str) -> str:
    """Resolves the human-readable label of a Dolibarr permission key.

    Traverses ``DOLIBARR_PERMISSIONS_LABELS`` following the ``module`` path
    (e.g., ``"user.user"`` -> sub-dict ``user`` -> sub-dict ``user``), then
    falls back to the base module if the full path is not found.

    Args:
        module: Name of the Dolibarr module, possibly nested (e.g., ``"user.self"``).
        permission_key: Permission key (e.g., ``"lire"``, ``"creer"``).

    Returns:
        str: Permission label, or ``"{module}.{permission_key}"`` if not found.
    """
    parts = module.split(".")

    # Try 1: full path (e.g., user.user.lire)
    val = _get_dict_value(DOLIBARR_PERMISSIONS_LABELS, parts, permission_key)
    if val is not None:
        return val

    # Try 2: fallback to base module (e.g., user.lire)
    val = _get_dict_value(DOLIBARR_PERMISSIONS_LABELS, [parts[0]], permission_key)
    if val is not None:
        return val

    return f"{module}.{permission_key}"
