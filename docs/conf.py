import sys
from datetime import UTC, datetime
from pathlib import Path

# Source code lives in src/ — required for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Project
project = "Assets Guardian (0.0.0)"
copyright = f"{datetime.now(UTC).year}, Apizee"  # noqa: A001
author = "Apizee"

# Extensions
extensions = [
    "sphinx.ext.autodoc",  # Auto-doc from docstrings
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.viewcode",  # Links to source code
    "sphinx.ext.autosummary",  # Auto summary tables
    "sphinx_click",  # Auto-doc for the Click CLI
    "myst_parser",  # Markdown file support
    "sphinxcontrib.mermaid",  # Mermaid diagram support
]

# Autodoc
autodoc_mock_imports = [
    "mysql.connector",
    "fpdf",
]
autodoc_default_options = {
    "members": True,
    # "undoc-members": True,  # don't use autodoc to discover attributes
    "show-inheritance": True,
    "private-members": False,
}
autodoc_member_order = "groupwise"
autoclass_content = "both"
autosummary_generate = True
autosummary_generate_overwrite = True

# Napoleon
napoleon_use_ivar = True

# HTML
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,  # -1
    "collapse_navigation": False,
    "sticky_navigation": True,
}
html_favicon = "_images/ag_favicon.png"
html_static_path = ["_static"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

suppress_warnings = [
    "autodoc.mocked_object",
    "toc.not_included",
    # Some pages keep GitHub-flavoured targets MyST cannot resolve: emoji heading anchors, anchors on H4+ headings (myst_heading_anchors = 3), and internal/ pages linking to repo-root files.  # noqa: E501
    "myst.xref_missing",
]

# Markdown
myst_heading_anchors = 3  # generates H1-H3 anchors to fix xref_missing warnings
myst_fence_as_directive = ["mermaid"]  # treat ```mermaid``` as a directive
