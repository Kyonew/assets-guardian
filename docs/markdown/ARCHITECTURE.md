# 🏗️ Software Architecture Documentation

> ⚠️ **Warning:** This documentation is a work in progress. Some sections may be incomplete, inaccurate, or subject to change.

## What is Assets Guardian?

Assets Guardian is an **IAM (Identity and Access Management) governance tool**. Its job is to answer, at any time:

> *Who has access to what, with what role - and does that comply with the company's security policy?*

It connects to multiple external systems (GitLab, Microsoft 365, Dolibarr, Teleport, etc.), pulls access data from each, normalizes it into a unified model, and produces two outputs:

- An **Excel workbook** - the living reference of all access rights across all systems, refreshed on every `sync`.
- A **PDF audit report** - a compliance report listing security gaps, violations, and anomalies.

The tool runs as a **non-interactive CLI**, designed for CI/CD pipelines, scheduled jobs, or manual runs by a security officer.

## System Overview

Assets Guardian is organized around a central `core/` package, a thin `cli/` entry point, shared `utils/`, and a separate `plugins/` boundary. Inside `core/`, each sub-package has a single responsibility and depends only on the packages below it.

> TODO: Make the diagram below easier to read, accurate but hard to follow (idea: add colors and arrows).

```mermaid
graph TD
    CLI["<b>CLI Layer</b><br/>cli/"]
    UTILS["<b>Utils</b><br/>utils/ - dates · ip"]
    PLUGINS["<b>Plugins</b><br/>plugins/ - gitlab · dolibarr · microsoft365 · …"]

    subgraph CORE["core/"]
        DOMAIN["<b>Domain</b><br/>domain/ - engines · models · ports · registry"]
        REPORTING["<b>Reporting</b><br/>reporting/ - Excel · PDF"]
        CLIENTS["<b>Clients</b><br/>clients/ - HTTP · MySQL"]
        PLUMBING["<b>Plumbing</b><br/>config · cache · logging"]
    end

    CLI --> DOMAIN
    CLI --> PLUMBING
    DOMAIN --> REPORTING
    DOMAIN --> PLUMBING
    PLUGINS -.->|"implements ports"| DOMAIN
    PLUGINS --> CLIENTS
    PLUGINS --> UTILS
    REPORTING --> PLUMBING
    REPORTING --> UTILS
```

| Package | Responsibility |
| --- | --- |
| **CLI** (`cli/`) | Parses arguments, builds the execution `Context`, routes to the right command handler. |
| **Core** (`core/`) | The application heart. Groups the sub-packages below, everything that is not the `cli/` entry point, the shared `utils/`, or a `plugins/` adapter lives here. |
| → **Domain** (`core/domain/`) | Orchestrates business logic through engines. Defines abstract interfaces (ports) that plugins implement. |
| → **Reporting** (`core/reporting/`) | Adapters around the report artifacts: Excel sheet builders and PDF generation. |
| → **Clients** (`core/clients/`) | Low-level technical clients (HTTP, MySQL) used by plugin adapters to reach external systems. They implement no domain port, plugins wrap them behind `IClientProvider`. |
| → **Config · Cache · Logging** (`core/config/`, `core/cache/`, `core/logging/`) | Application plumbing only: configuration loading and validation, logger setup, file-based cache. |
| **Utils** (`utils/`) | Pure stateless helpers (dates, IP) with zero project dependencies. |
| **Plugins** (`plugins/`) | Adapters for each external system. Plug into the domain via well-defined interfaces. The domain never imports from plugins. |

## Startup Sequence - Plugin Discovery

Before any command runs, the CLI bootstraps the application and dynamically discovers all active plugins. This is the mechanism that makes the system modular: plugins are loaded only if they appear in `config.yml`.

```mermaid
flowchart LR
    A([User runs CLI]) --> B[Load config.yml]
    B --> C["Build Context<br/>Init logging"]
    C --> D[discover_all]

    D --> E{"For each dir<br/>in plugins/"}
    E --> F{"In config<br/>integrations?"}
    F -- No --> G([Skip])
    F -- Yes --> H["Import client.py<br/>Import collector.py"]

    H --> I{Command?}
    I -- audit --> J["Import rules.py<br/>Import pdf_builder.py"]
    I -- sync --> K[Import sheet_builders.py]

    J --> L[(Global Registries)]
    K --> L
    H --> L
```

When a plugin module is imported, its components self-register into global registries via decorators (e.g. `@CollectorRegistry.register("gitlab")`). After discovery, engines retrieve what they need from these registries.

## Commands and Data Flows

### `sync` - Update the Excel repository

Fetches live data from all configured sources and writes it into the Excel workbook, preserving manually edited sheets.

```mermaid
sequenceDiagram
    participant CLI
    participant SyncEngine
    participant CollectorEngine
    participant Plugin as Plugin Collector
    participant ExcelEngine

    CLI->>SyncEngine: run(collectors)

    loop for each active plugin instance
        SyncEngine->>CollectorEngine: run_collect(collector)
        CollectorEngine->>Plugin: collect_identities()
        CollectorEngine->>Plugin: collect_assets()
        CollectorEngine->>Plugin: collect_accesses()
        Plugin-->>CollectorEngine: Identity[] · Asset[] · Access[]
        CollectorEngine-->>SyncEngine: CollectorResult
    end

    SyncEngine-->>CLI: results

    CLI->>ExcelEngine: generate(results, ctx)
    ExcelEngine-->>CLI: outputs/assets_guardian.xlsx
```

**Key behaviours:**

- Manual tabs (e.g. the access matrix, employee mappings) are preserved - only auto-generated tabs are overwritten.
- If a collector fails, `SyncEngine` logs the error and continues with the remaining sources.

### `audit` - Compliance audit and PDF report

Evaluates compliance rules against live data and the Excel baseline, then produces a PDF report.

```mermaid
sequenceDiagram
    participant CLI
    participant AuditEngine
    participant CollectorEngine
    participant ComplianceEngine
    participant PDFEngine

    CLI->>AuditEngine: run(collectors, ctx)

    loop for each active plugin instance
        AuditEngine->>CollectorEngine: run_collect(collector)
        CollectorEngine-->>AuditEngine: identities · assets · accesses

        AuditEngine->>AuditEngine: Load baseline from Excel
        AuditEngine->>AuditEngine: Load rules from rules_config.yml
        AuditEngine->>ComplianceEngine: run_all(live_data, baseline, matrix, profiles)
        ComplianceEngine-->>AuditEngine: Finding stream -> cached to disk
        AuditEngine-->>AuditEngine: Report (per source/instance)
    end

    AuditEngine->>PDFEngine: generate(all reports)
    PDFEngine-->>CLI: outputs/audit_report.pdf
```

**Key behaviours:**

- The **baseline** is the Excel workbook from the last `sync`. Comparison rules use it to detect changes (e.g. new accounts since last audit).
- Findings are **streamed through a file cache** to avoid loading all data into memory at once.
- Each `(source_name, instance_id)` pair produces its own `Report`, then all reports are merged into a single PDF.

### `check` - Configuration health check

Tests connectivity and authentication for all configured plugins. Does not write any files. Used for troubleshooting and CI/CD pre-flight validation.

The `CheckEngine` iterates over all configured integrations, attempts to instantiate each client, and reports pass/fail per source.

## Domain Models

> TODO: To be reviewed.

These are the core data structures shared across all engines, plugins, and reporting adapters. All models are **frozen dataclasses** - immutable once created, with field validation on construction.

```mermaid
erDiagram
    Identity {
        string external_id
        string login
        string email
        bool is_active
        bool mfa_enabled
        datetime last_activity_at
    }
    Asset {
        string external_id
        string name
        string asset_type
        string source
    }
    Access {
        string role
        string source
    }
    Finding {
        string rule_id
        string severity
        string message
        string source
    }
    Report {
        int total_count
    }

    Access }o--|| Identity : "granted to"
    Access }o--|| Asset : "on"
    Report ||--o{ Finding : "contains"
```

| Model | Description |
| --- | --- |
| **Identity** | A person or service account retrieved from an external source. |
| **Asset** | A resource being protected (repository, project, application, server). |
| **Access** | A grant: an `Identity` holds a level of access (e.g. role, groupe) on an `Asset`. |
| **Location** | Representation and validation of a file path (local or remote) via a prefixed string (`local:` or `remote:`). |
| **Validator** | Helper utility used to validate model constraints during dataclass construction. |
| **Finding** | A compliance violation or anomaly detected by a rule. |
| **Report** | Aggregates all `Finding`s produced for one source/instance pair. |
| **Context** | Immutable execution context (config, flags, mode) passed through the entire call chain. |

## Plugin System

### What a plugin contains

A plugin is a directory under `plugins/` that adapts a specific external system to the domain interfaces. Each plugin can contain the following files:

| File | Required | Purpose |
| --- | --- | --- |
| `client.py` | Yes | Authenticates with the external system and creates the client object |
| `repository.py` | Yes | Fetches raw data from the external resource |
| `mapper.py` | Yes | Normalizes raw data responses into domain models (`Identity`, `Asset`, `Access`) |
| `collector.py` | Yes | Implements `Collector` - orchestrates repositories and mappers |
| `rules.py` | No | Plugin-specific compliance rules evaluated during `audit`. Acts as the entry point that re-exports the rule classes defined in `compare.py`, `matrix.py` and `compliance.py` |
| `compare.py` | No | Comparison rules (`IComparisonRule`), live run vs the last Excel sync baseline |
| `matrix.py` | No | Matrix rules (`IMatrixRule`), active grants vs the expected access matrix |
| `compliance.py` | No | Compliance rules (`IComplianceRule`), criteria checked on live identities/assets |
| `sheet_builders.py` | No | Custom Excel sheet layouts injected during `sync` |
| `pdf_builder.py` | No | Custom PDF sections injected during `audit` report generation |
| `constants.py` | No | Source-specific constants (role names, access levels, etc.) |
| `excel_config.json` | No | Plugin-specific Excel column mapping and styling rules used during `sync` |

### Plugin interfaces

> TODO: Probably needs revisiting depending on the changes made after the review.

The domain defines four abstract interfaces that a plugin must fulfill:

```mermaid
classDiagram
    class IRepository {
        <<interface>>
        +get_raw_users() list
        +get_raw_assets() list
        +get_raw_accesses() list
    }

    class IMapper {
        <<interface>>
        +to_identity(raw) Identity
        +to_asset(raw) Asset
        +to_access(raw, asset) Access
    }

    class Collector {
        <<base class>>
        +source_name str
        +instance_id str
        +collect_identities() Iterable
        +collect_assets() Iterable
        +collect_accesses() Iterable
    }

    class IClientProvider {
        <<interface>>
        +instantiate_client() Any
        +health_check() bool
    }

    Collector --> IRepository : delegates to
    Collector --> IMapper : normalizes via
```

`Collector` is a base class with default implementations that delegate to `_repository` and `_mapper`. Plugin collectors override only the methods where they need non-standard behaviour.

### Registration via decorators

Components self-register into global registries when their module is imported. This happens automatically during the discovery phase - no manual wiring needed.

```python
# plugins/gitlab/collector.py
@CollectorRegistry.register("gitlab")
class GitlabCollector(Collector):
    ...

# plugins/gitlab/compare.py - source is inferred from the module path
@RuleRegistry.register("COMPARE-001")
class GitlabNewUserComparisonRule(IComparisonRule):
    ...

# plugins/default_rules.py - registered under source "default", available to all plugins
@RuleRegistry.register("DEFAULT-001")
class MultiFactorAuthRule(IComplianceRule):
    ...
```

One thing to note:

- **Rules inherit from a specific sub-interface**, not `IRule` directly, depending on their category:

  | Interface | Category | Purpose | Example |
  | --- | --- | --- | --- |
  | `IComplianceRule` | **Compliance** | Standard rule checking specific criteria on live identities or assets. | `DEFAULT-001` (MFA disabled) |
  | `IComparisonRule` | **Comparison** | State check comparing current live run against the last Excel sync baseline. | `COMPARE-001` (GitLab user added) |
  | `IMatrixRule` | **Matrix** | Comparing active access grants with the expected access defined in the access matrix tab. | `MATRIX-001` (Dolibarr admin compliance) |

The registries are global singletons. After discovery, the factory function `instantiate_collectors(integrations_config)` (in `core/domain/registry/collector_factory.py`) returns a ready-to-use collector instance for every configured `(source, instance)` pair, e.g. a `GitlabCollector`, without the engines ever knowing the concrete classes.

### Multi-instance support

A single plugin (e.g. `gitlab`) can be configured for multiple independent instances (e.g. `gitlab.company.com` and `gitlab.subsidiary.com`). The `instance_id` property on `Collector` ensures each instance's data remains separate throughout the pipeline, and produces its own `Report`.

```yaml
# config/config.yml
integrations:
  gitlab:
    gitlab.company.com:  # instance 1
      url: https://gitlab.company.com/api/v4
    gitlab.subsidiary.com:  # instance 2
      url: https://gitlab.subsidiary.com/api/v4
```

## Design Patterns

### Hexagonal Architecture (Ports and Adapters)

The domain layer defines **ports** (abstract interfaces in `core/domain/ports/`) and contains all business logic. Plugins implement **adapters** that fulfill these ports. The domain has zero knowledge of GitLab, REST APIs, or SQL.

```text
External systems (APIs, databases)
        ↕
  Adapters (plugins)
        ↕
  Ports (abstract interfaces)   ← boundary
        ↕
  Domain (engines + models)
```

Adding a new source or replacing an existing one never touches the core engines - only a new plugin directory is needed.

### Registry and Factory

Plugins register their classes into global registries at import time. At runtime, engines ask factories to instantiate collectors and rules by source name. The engine never imports or names a plugin class directly.

This is what allows the system to be configuration-driven: if `gitlab` is in `config.yml`, the GitLab plugin is loaded and used; if it is removed, it is ignored with no code change.

> TODO: Adding a Mermaid diagram could be interesting? Maybe a quick job for Claude?

### Template Method (Collector base class)

`Collector` provides default implementations of `collect_identities`, `collect_assets`, and `collect_accesses`. These iterate over raw results from `_repository` and normalize them via `_mapper`. A plugin collector only needs to override the methods where it requires custom behaviour (e.g. joining data from multiple API calls).

> TODO: Adding a Mermaid diagram could be interesting? Maybe a quick job for Claude?

### Strategy (Compliance rules)

Each compliance rule is an independent strategy object implementing `IRule.evaluate(...)`. The `ComplianceEngine` runs all active rules without knowing their internal logic. Rules are composable, independently testable, and can be enabled or disabled per source in `rules_config.yml`.

> TODO: Adding a Mermaid diagram could be interesting? Maybe a quick job for Claude? It could simply be an excerpt from the `rules_config.yml` file.

### Dependency Injection

Engines receive their dependencies (cache, collector engine) via constructor parameters. Plugin collectors receive their client and config at construction time. This simplifies unit testing: pass mock or stub objects into constructors without patching globals.

> TODO: A code example?

### Cache (JSON Lines)

To scale efficiently and support high-volume data retrieval without RAM spikes, the caching layer (`core/cache`) implements a **JSONL (JSON Lines) Cache Manager**:

- **Disk Streaming & Chunking**: Using `LazyCacheIterable` and `itertools.batched`, the system writes and reads collected domain objects incrementally in configurable batches. This avoids storing all raw objects in memory at once.
- **Atomic Disk Writes**: Files are written first as `.tmp` drafts and swapped atomically via `os.replace` to prevent data corruption during unexpected CLI interruptions.
- **Environment-Aware Retention**: Temporary cache files are cleared automatically in production (`AppEnv.PROD`) at the end of each command, but are retained during local development/testing (`AppEnv.DEV`) to prevent redundant external API hits.

> TODO: Adding a Mermaid diagram could be interesting? Maybe a quick job for Claude?

## Configuration Reference

### `config/config.yml` - Main configuration

The central hub. Controls which plugins are active, logging behavior, and file paths.

> TODO: A description of each config.py parameter is needed: the possible values and their purpose across Assets Guardian.

```yaml
env: "dev" # or prod

author:
  fullname: "First name LAST NAME"
  email: "...@example.com"

logging:
  console_level: "info"
  file_level: "debug"
  file-basename: "assets-guardian"
  max-size: 10 # MB
  max-files: 3

paths:
  excel: "local:outputs/assets_guardian.xlsx"
  pdf: "local:outputs/audit_report.pdf"
  rules: "local:config/rules_config.yml"
  employees: "local:config/employees.json"

cache:
  batch_size: 64
  cache_dir: ".assets-guardian_cache"

mon_plugin:
  prod:
    url: "https://mon_plugin_prod.company.com/"
    credentials:
      token: "${MON_PLUGIN_PROD_TOKEN}" # resolved from environment variable
  test:
    url: "postgresql://db_mon_plugin.company.com:5432/assets"
    credentials:
      username: "${MON_PLUGIN_PROD_USERNAME}" # resolved from environment variable
      password: "${MON_PLUGIN_PROD_PASSWORD}" # resolved from environment variable
```

Only plugins listed are discovered and loaded. Removing a plugin key (e.g. `gitlab`) disables the plugin entirely. For a complete reference, see `template.config.yml`.

### `config/rules_config.yml` - Compliance rules

Specifies which rules are active for each source, and their parameters.

> TODO: A description of the configuration options for each rule is needed...

```yaml
gitlab:
  # Load all default rules defined in plugins/default_rules.py
  <<: *default_rules

  # Configure plugin-specific rules with their appropriate parameters and severity
  COMPARE-001:
    name: "New GitLab users"
    severity: INFO

  COMPLIANCE-001:
    description: "Connection from an unusual location."
    severity: "HIGH"
    custom_parameter_1: "first custom parameter"
    custom_parameter_2: "second custom parameter"
    custom_parameter_3: "third custom parameter"

  MATRIX-001:
    description: "User not in the right group"
    severity: "HIGH"
```

Rule IDs match the `@RuleRegistry.register(rule_id)` decorator in the plugin's `rules.py`. See [Registration via decorators](#registration-via-decorators) for the three rule categories (`COMPARE-XXX`, `COMPLIANCE-XXX` and `MATRIX-XXX`).

### `config/employees.json` - HR reference

The source of truth for known identities. Used during `audit` to detect **shadow accounts**, identities found in an external system that have no corresponding HR record.

Each entry maps a real person to their known identifier in the information system like email address. The `profiles` field lists the security profiles assigned to that employee, used by matrix rules to validate their access rights.

Example of `employees.json` :

```json
[
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@company.com",
        "username": "jdoe",
        "profiles": "Marketing, Finance"
    },
    {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada.lovelace@company.com",
        "username": "alovelace",
        "profiles": "R&D, Support"
    }
]
```

## Key Technical Decisions

> TODO: Probably incomplete... Isn't this redundant with the rest of the document? It looks like a rationale for each technical dependency choice, but it drifts into software architecture choices such as the cache, or even Docker...

| Decision | Choice | Rationale |
| --- | --- | --- |
| **Language** | Python 3.13 | Rich ecosystem for Excel/PDF; strict typing available |
| **CLI framework** | Click | Clean group/subcommand model with context passing |
| **Excel** | openpyxl | Full read/write with formatting and sheet preservation |
| **PDF** | fpdf2 | Lightweight; no Java dependency unlike reportlab alternatives |
| **Package manager** | uv + hatchling | Fast, reproducible installs; replaces pip + setuptools |
| **Linting** | Ruff | Replaces flake8 + black + isort in a single fast tool |
| **Type checking** | Mypy (strict mode) | Catches interface mismatches between plugins and ports at dev time |
| **Models** | Frozen dataclasses | Immutability prevents accidental mutation in engines; slot optimization |
| **Cache & Persistence** | JSON Lines (JSONL) | Streaming data-offloading to disk using batched generators to keep RAM footprint low; crash checkpoint capabilities |
| **Containerization** | Multi-stage Docker | Minimal production image; non-root user for security |
