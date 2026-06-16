# Changelog

All notable changes to **Assets Guardian** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-05

First public, open-source release of Assets Guardian: a modular, multi-source, multi-instance Identity and Access Management (IAM) governance tool that audits identities, access rights and security compliance across an IT environment and consolidates everything into a single unified format.

### Added

- **Compliance audit engine** that collects identities and access rights from every enabled source and evaluates them against an extensible, rule-based policy.
- **Command-line interface** with `check` (config, connectivity & permissions diagnostics), `sync` (build/update the Excel inventory) and `audit` (evaluate rules & generate the PDF report) commands.
- **Reporting**:
  - Excel IAM inventory/register, with instance-specific sheet naming and filtering.
  - PDF audit reports.
- **Plugin architecture**: self-contained connectors, activated on demand via `config.yml`, with multi-instance support and no changes required to the core:
  - **GitLab** plugin: audits users, groups, projects and access rights.
  - **Dolibarr** plugin: audits users, groups and access rights.
- Project version dynamically retrieved from `pyproject.toml`.
- **Documentation & governance**: Sphinx-generated docs, a software-architecture overview and a plugin-creation guide, plus open-source governance files: `LICENSE.txt` (GPLv3), `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` and `SECURITY.md`.

[0.1.1]: https://github.com/apizee/assets-guardian/releases/tag/v0.1.1
