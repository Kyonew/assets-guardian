# 🚀 Getting started

Before installing anything, pick your mode based on **two questions**, then install **only** the prerequisites for the cell you land in, you will never need all of them.

1. **What do you want to do?** *Use* Assets Guardian to run audits, or *develop* it (contribute, write plugins)?
2. **Where do you want it to run?** Directly on your **host** (Python + uv), or inside a **container** (Docker)?

| | 🐍 **On your host** (Python + uv) | 🐳 **In a container** |
| :--- | :--- | :--- |
| **Use it** <br/> *(operators, auditors, IT)* | **Standalone install**: installs a global `assets-guardian` command on your `PATH`, run it from any audit folder. | **Docker image**: build once, run audits in an isolated container with your `config/` (read-only) and `outputs/` mounted as volumes, credentials passed via env vars or an env file. |
| **Develop it** <br/> *(contributors)* | **Local dev**: full dev environment (`uv sync --all-groups`), run from source with `uv run assets-guardian …`, all linters/tests/hooks available. | **Dev Container**: a fully provisioned, reproducible VS Code environment. The entire toolchain is set up for you inside a Docker container. <br/><br/> **Docker image**: IDE-agnostic alternative, bind-mount your source into the container and use `uv` directly in the container. |

**Prerequisites per mode**

| Mode | Requirements |
| :--- | :--- |
| 🐍 **Standalone install** | [Python 3.13](https://www.python.org/downloads/) and [uv](https://github.com/astral-sh/uv) (replacing standard `pip` and manual virtual environment configurations). |
| 🐳 **Docker image** | A container engine only: [Docker](https://docs.docker.com/get-docker/). No local Python setup needed, applies to both the *use* and *develop* Docker variants. |
| 🐍 **Local dev** | Same as *Standalone install*. |
| 💻 **Dev Container** | [VS Code](https://code.visualstudio.com/) (or any [Dev Containers](https://containers.dev/)-compatible IDE) + the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), and a container engine ([Docker](https://docs.docker.com/get-docker/) or compatible). |

> 💡 **Tip:** The two axes are independent: Docker is not only for production. The same engine powers three modes: the `use` image (audits in isolation), the `develop` image (validate your changes in the exact production container), and the Dev Container (full VS Code environment, workspace live-mounted).
>
> 💡 **Tip:** [`make`](https://www.gnu.org/software/make/) is optional in every mode, it provides shortcuts for common commands regardless of where the tool runs.

## 📦 Installation

### 🔗 Clone the repository

All modes start from the source:

```bash
# Over SSH: recommended if you have an SSH key configured
git clone git@github.com:apizee/assets-guardian.git

cd assets-guardian/
```

> 💡 **Tip:** All the commands in the sections below assume you are running them from the root of this cloned directory.

### 🐍 Standalone install

#### Installation

```bash
make install
```

Without `make`:

```bash
uv tool install .
```

Verify:

```bash
assets-guardian --version
```

The `assets-guardian` command is now available globally on your `PATH`.

> 💡 **Tip:** If your shell can't find the command, run `uv tool update-shell` and restart your terminal.

#### Upgrade

```bash
make upgrade
```

Without `make`:

```bash
uv tool install . --reinstall
```

Verify:

```bash
assets-guardian --version
```

#### Uninstall

```bash
make uninstall
```

Without `make`:

```bash
uv tool uninstall assets-guardian
```

Verify:

```bash
assets-guardian
```

### 🐍 Local dev

```bash
make setup
```

Without `make`:

```bash
uv sync --all-groups
uv run pre-commit install
```

Verify:

```bash
uv run assets-guardian --version
```

### 🐳 Docker image (`use`)

```bash
make docker-build
```

Without `make`:

```bash
docker build -t assets-guardian .
```

The image is built once. See [Running](#running) for mounting volumes and passing credentials.

### 💻 Dev Container

Open the repository folder in VS Code. When prompted, click **Reopen in Container**, or open the Command Palette (`Ctrl+Shift+P`) and run **Dev Containers: Reopen in Container**.

| Command | Description |
| :--- | :--- |
| `Ctrl+Shift+P` → **Dev Containers: Reopen in Container** | Opens the current folder in a Dev Container |
| `Ctrl+Shift+P` → **Dev Containers: Reopen in WSL** | Opens the current folder in WSL (if you prefer to use WSL rather than the Dev Container) |
| `Ctrl+Shift+P` → **Dev Containers: Reopen Locally** | Return to the local environment |
| `Ctrl+Shift+P` → **Dev Containers: Rebuild Container** | Rebuilds the container (after modifying the `devcontainer.json` or the Dockerfile) |
| `Ctrl+Shift+P` → **Dev Containers: Rebuild Container Without Cache** | Rebuilds the container without Docker cache, to start from scratch |
| `Ctrl+Shift+P` → **Dev Containers: Show Container Log** | Displays the container creation logs (useful for debugging a failing build) |

### 🐳 Docker image (`develop`)

```bash
make docker-build
```

Without `make`:

```bash
docker build -t assets-guardian .
```

The image is built once. See [Running](#running) for mounting volumes and passing credentials.

> 💡 **Tip:** Rebuild the image after each change to dependencies or the Dockerfile, source code changes are reflected live via the volume mount.

## ⚙️ Setup configurations

No matter which mode you installed (🐍 **Standalone install**, 🐍 **Local dev**, 🐳 **Docker** or 💻 **Dev Container**), the Assets Guardian configuration is the same and shared across all of them.

### 📁 Configuration Files

You need a `config/` directory with all files required:

```text
config/
├── config.yml           # Central hub & plugin activation
├── template.config.yml  # A file for validation purpose before running
├── rules_config.yml     # IAM policies & rule registry
├── employees.json       # HR database (source of truth about identity)
├── excel_config.json    # Excel report styling
└── pdf_config.json      # PDF report styling
```

> 💡 **Tip:** You can use the `config/` from the repository as based for your configuration, don't forget to remove the `template.` prefix.
>
> ⚠️ **Warning:** You need to conserve the `template.config.yml` for validation purpose before running.

### 📑 File Details

| File | Description | Key Notes |
| :--- | :--- | :--- |
| **`config.yml`** | Central hub for env profiles, global logs, and paths. | **Plugins:** Only activated if explicitly defined here. |
| **`template.config.yml`** | Validation schema for `config.yml`. | **Do not delete or rename:** required at startup to validate the main config. |
| **`rules_config.yml`** | IAM policies registry (MFA, inactivity thresholds). | **Strict execution:** Rules are evaluated **only** if explicitly defined or inherited under a plugin section. |
| **`employees.json`** | List of active employees and access profiles. | Used to detect shadow accounts. **Must be populated manually.** |
| **`excel_config.json`** | Visual and structural guidelines for Excel reports. | Configures fields validation and timezones. |
| **`pdf_config.json`** | Visual and structural guidelines for PDF reports. | Configures brand colors, fonts, and checkboxes. |

> 💡 **Tip:** Remember, you can simply copy the templates to get started: `cp config/template.* config/`.

#### 📄 The `config.yml` file

The central configuration hub. Every run reads this file first.

```yaml
env: "dev"                        # Active environment label (dev, test or prod)

author:
  fullname: "First name LAST NAME"  # Displayed in report headers
  email: "...@example.com"          # Displayed in report headers

logging:
  console_level: "INFO"             # Verbosity printed to stdout (DEBUG, INFO, WARNING, ERROR)
  file_level: "DEBUG"               # Verbosity written to the log file
  file-basename: "assets-guardian"  # Log file name prefix
  max-size: 10                      # Max log file size in MB before rotation
  max-files: 3                      # Number of rotated log files to keep

paths:
  excel: "local:outputs/assets_guardian.xlsx"   # Output Excel report
  pdf:   "local:outputs/audit_report.pdf"       # Output PDF report
  rules: "local:config/rules_config.yml"        # Path to the rules registry
  employees: "local:config/employees.json"      # Path to the HR database

cache:
  batch_size: 64                  # Number of items fetched per API call
  cache_dir: ".assets-guardian_cache"  # Directory for local API response cache
```

##### The `env` parameter

Controls the execution mode of the application. Three values are accepted: `dev`, `test`, and `prod`.

```yaml
env: "dev"
```

**Cache behaviour**: after a `sync` run, temporary API-response cache files are only deleted when `env` is `prod`. In `dev` and `test` they are kept on disk so subsequent runs skip already-fetched data, which significantly reduces collection time during development.

> 💡 **Tip:** You can override this value at runtime without editing the file by setting the `ENV` environment variable (e.g. `ENV=prod assets-guardian sync`). The environment variable always takes priority over the value in `config.yml`.

##### The `author` section

Metadata about the person running the audit. Both fields are displayed in report headers and written into the Excel file's author columns.

```yaml
author:
  fullname: "First name LAST NAME"
  email: "...@example.com"
```

| Field | Description |
| :--- | :--- |
| `fullname` | Full name of the auditor, written into the Excel and PDF report columns. |
| `email` | Professional email, used as the sender address for any notification or alert email sent by Assets Guardian. |

> ⚠️ **Warning:** `email` is required whenever Assets Guardian sends emails (alerts, scheduled reports, notifications). If missing, Assets Guardian will stop at startup and raise an error before any command runs.
>
> 💡 **Tip:** Outside of email-sending contexts, this section is optional. If omitted, the author fields in generated reports will be left blank.

##### The `logging` section

Controls what gets written to the console and to the rotating log file.

```yaml
logging:
  console_level: "INFO"
  file_level: "DEBUG"
  file-basename: "assets-guardian"
  max-size: 10     # MB
  max-files: 3
```

| Field | Default | Description |
| :--- | :---: | :--- |
| `console_level` | `INFO` | Minimum level printed to stdout |
| `file_level` | `DEBUG` | Minimum level written to the log file |
| `file-basename` | `assets-guardian` | Prefix for the log file name (e.g. `assets-guardian.log`) |
| `max-size` | `10` | Maximum log file size in MB before rotation |
| `max-files` | `5` | Number of rotated log files to keep |

Valid levels (from least to most verbose): `CRITICAL` → `ERROR` → `WARNING` → `INFO` → `DEBUG`.

> 💡 **Tip:** The `-v` / `--verbose` CLI flag forces `console_level` to `DEBUG`, and `-q` / `--quiet` forces it to `CRITICAL`, regardless of what is set here. The log file level is never affected by CLI flags, the file always follows the key: `file_level` in `config.yml` file.

##### The `paths` section

Locations of every file that Assets Guardian reads or writes. All values must use the `local:` prefix, which resolves relative to the working directory.

```yaml
paths:
  excel: "local:outputs/assets_guardian.xlsx"
  pdf:   "local:outputs/audit_report.pdf"
  rules: "local:config/rules_config.yml"
  employees: "local:config/employees.json"
```

| Field | Default | Description |
| :--- | :--- | :--- |
| `excel` | `local:outputs/assets_guardian.xlsx` | Output Excel report |
| `pdf` | `local:outputs/audit_report.pdf` | Output PDF report |
| `rules` | `local:config/rules_config.yml` | Input IAM rules registry |
| `employees` | `local:config/employees.json` | Input HR database |

> 💡 **Tip:** Each path can also be set via a dedicated environment variable (`PATH_EXCEL`, `PATH_PDF`, `PATH_RULES`, `PATH_EMPLOYEES`), which takes priority over the config file. This is useful to redirect outputs in a CI pipeline without editing the file.
>
> 🔭 **Coming soon:** A `remote:` prefix is planned to support remote locations such as SharePoint. This will allow Assets Guardian to read its configuration and write its reports directly to a SharePoint document library, without any local file system dependency.

##### Plugin sections

Add one block per plugin instance you want to audit:

```yaml
gitlab:
  prod: # Arbitrary environment label
    url: "https://gitlab.company.com/api/v4"
    credentials:
      personnal_access_token: "${GITLAB_PROD_TOKEN}"
  test: # Arbitrary environment label
    url: "https://gitlab-test.company.com/api/v4"
    credentials:
      personnal_access_token: "${GITLAB_TEST_TOKEN}"

dolibarr:
  my_instance: # Arbitrary environment label
    url: "https://dolibarr.company.com/api/index.php"
    credentials:
      dolapikey: "${DOLIBARR_TOKEN}"

microsoft365:
  main: # Arbitrary environment label
    url: "https://graph.microsoft.com/.default"
    credentials:
      tenant_id: "${M365_TENANT_ID}"
      application_id: "${M365_APPLICATION_ID}"
      client_secret: "${M365_CLIENT_SECRET}"
```

> ⚠️ **Warning:** A plugin section must be present (and not commented out) for the corresponding plugin to run. Plugins with no section are silently skipped.
>
> 💡 **Tip:** Each plugin ships with a `CREDENTIALS.md` file that explains the required credentials fields, how to generate them on the target platform, and the minimum permissions Assets Guardian needs.

#### 🔑 Environment variables

You may have noticed placeholders like `${M365_APPLICATION_ID}` or `${M365_CLIENT_SECRET}` in the configuration above. These are environment variable references, they keep sensitive credentials out of `config.yml` and out of version control. You can supply them via a `.env` file or directly as OS-level environment variables.

Assets Guardian accepts environment variables from any standard source, use whichever fits your setup:

- **`.env` file** *(quickest for local use)*: copy the provided template and fill in only the variables you need.

  ```bash
  cp .env.template .env
  # then edit .env, comment out anything you don't use...
  ```

- **Shell / OS environment**: export variables directly in your terminal or shell profile.

  ```bash
  export GITLAB_MAIN_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
  ```

- **Docker**: pass them via `--env-file` or `-e` at runtime, no `.env` file required on the host.

  ```bash
  docker run --env-file .env assets-guardian ...
  # or individually: docker run -e GITLAB_MAIN_TOKEN=... assets-guardian ...
  ```

- **CI/CD secrets**: inject them as pipeline environment variables (GitHub Actions secrets, GitLab CI variables, etc.), nothing to store on disk.

##### Injecting environment variables into `config.yml` (recommended)

The recommended way to handle secrets is to **never write them in plain text** inside `config.yml`. Instead, reference your environment variables using the `${VAR_NAME}` syntax directly in the YAML file:

```yaml
gitlab:
  prod:
    credentials:
      personnal_access_token: "${GITLAB_PROD_TOKEN}"
```

At startup, Assets Guardian reads your `.env` file and expands all `${...}` placeholders before parsing the YAML. Your secrets stay out of the file, the only thing committed to version control is the reference, not the value.

> 💡 **Tip:** This approach makes it trivial to switch between environments (dev, test, prod) by swapping the `.env` file, without ever touching `config.yml`.

##### How `get_config_value` resolves configuration

Internally, Assets Guardian uses `get_config_value` ([`loader.py`](https://github.com/apizee/assets-guardian/blob/main/src/assets_guardian/core/config/loader.py)) whenever it reads a value from the configuration. This function applies a strict **priority chain**:

```mermaid
flowchart TD
    subgraph LOAD["① Loading: load_yaml_config()"]
        SYS["🖥️ System env vars\n(shell / CI / Docker)"]
        ENV_FILE[".env file"]
        ENV_FILE -->|"setdefault\nnever overwrites"| MERGED["os.environ\n(merged env)"]
        SYS -->|always present| MERGED
        MERGED -->|"os.path.expandvars()\nresolves \${VAR} in YAML"| PARSED["config.yml\nparsed dict"]
    end

    subgraph RESOLVE["② Resolution: get_config_value()"]
        Q1{"env_override?\ndefault: True"} -->|Yes| Q2{"Env var\nset?"}
        Q2 -->|Yes| R1["✅ env value"]
        Q2 -->|No| Q3{"Key in\nYAML dict?"}
        Q1 -->|No| Q3
        Q3 -->|Yes| R2["✅ YAML value"]
        Q3 -->|No| Q4{"Default\nprovided?"}
        Q4 -->|Yes| R3["✅ default"]
        Q4 -->|No| R4["❌ KeyError"]
    end

    LOAD --> RESOLVE
```

The environment variable name is derived automatically from the YAML key path by uppercasing it and replacing `:` and `-` with `_`. For example:

| YAML key path | Derived env variable |
| :--- | :--- |
| `logging:level` | `LOGGING_LEVEL` |
| `gitlab:prod:credentials:personnal_access_token` | `GITLAB_PROD_CREDENTIALS_PERSONNAL_ACCESS_TOKEN` |

This means you can override **any** configuration value at runtime by setting the corresponding environment variable, without modifying `config.yml` at all. This is particularly useful in CI/CD pipelines or containerised deployments where injecting env vars is more practical than managing files.

> 💡 **Tip:** The `${VAR}` interpolation in `config.yml` and the env-variable override in `get_config_value` are two independent mechanisms that complement each other. The interpolation makes secrets explicit and readable in the file, the override priority lets CI infrastructure inject values without a config file at all.

#### 📄 The `template.config.yml` file

A reference copy of `config.yml` with placeholder values. Assets Guardian validates your `config.yml` against this file at startup.

**Do not delete or rename it.** It is not a backup, it is required at runtime. Keep it alongside `config.yml` at all times.

> 💡 **Tip:** When you add a new plugin section or a new field to `config.yml`, mirror the change in `template.config.yml` with an appropriate placeholder value, otherwise validation will fail.

#### 📄 The `rules_config.yml` file

The IAM policy registry. It declares which rules are active for each plugin and configures their thresholds.

Rules are grouped using a YAML anchor (`define: &default_rules`) so they can be inherited by any plugin with `<<: *default_rules`. A rule is only evaluated if it appears under the plugin's section, even if the rule is implemented in the plugin's code, it will be silently ignored at runtime if it has no entry here.

Each rule entry requires a `description` and a `severity`. All additional fields (thresholds, IPs, flags, etc.) are passed directly to the rule as free-form parameters, what is accepted depends entirely on **the rule's own implementation**.

**Built-in default rules:**

| Rule ID | Description | Severity | Extra configurable fields |
| :--- | :--- | :---: | :--- |
| `DEFAULT-001` | Account without MFA enabled | `DANGER` | - |
| `DEFAULT-002` | Inactivity threshold exceeded | `HIGH` (dynamic) | `inactivity_threshold_days_warning`, `inactivity_threshold_days_danger`, `inactivity_threshold_days_critical` |
| `DEFAULT-003` | Account with excessive permissions | `DANGER` | - |
| `DEFAULT-004` | Connection from an unusual location | `WARNING` | `company_network_ip` |

**Severity levels** (from lowest to highest): `INFO` → `WARNING` → `HIGH` → `DANGER` → `CRITICAL`

**Example:**

```yaml
define: &default_rules
  DEFAULT-001:
    description: "Account without MFA enabled."
    severity: "DANGER"
  DEFAULT-002:
    description: "Inactivity threshold exceeded for an account."
    severity: "HIGH"
    inactivity_threshold_days_warning: 90
    inactivity_threshold_days_danger: 180
    inactivity_threshold_days_critical: 365
  DEFAULT-003:
    description: "Account with excessive permissions."
    severity: "DANGER"
  DEFAULT-004:
    description: "Connection from an unusual location."
    severity: "WARNING"
    company_network_ip: "192.168.1.2"   # Your corporate network IP/range

gitlab:
  <<: *default_rules          # Inherit all default rules
  COMPLIANCE-001:              # Plugin-specific rule
    description: "Connection from an unusual location."
    severity: "HIGH"

dolibarr:
  <<: *default_rules

microsoft365:
  <<: *default_rules
```

> ⚠️ **Warning:** Removing a rule from a plugin section disables it entirely for that plugin, even if it is defined in `&default_rules`.

#### 📄 The `employees.json` file

The HR source of truth. Assets Guardian cross-references every account found during an audit against this list to detect shadow accounts (accounts that belong to no known employee).

It is a JSON array of employee objects:

```json
[
    {
        "first_name": "John",
        "last_name": "DOE",
        "email": ["john.doe@company.com", "jdoe@company.com"],
        "username": ["jdoe", "john.doe"],
        "profiles": "R&D, Support"
    }
]
```

| Field | Description |
| :--- | :--- |
| `first_name` | Employee's first name |
| `last_name` | Employee's last name (usually uppercase by convention) |
| `email` | List of professional email addresses associated with this employee, used as primary identifiers for account matching |
| `username` | List of login handles used across audited platforms, allows matching a single employee to multiple accounts |
| `profiles` | Comma-separated list of job profiles / departments, used to detect privilege mismatches with matrix |

> ⚠️ **Warning:** This file must be maintained manually. Any account found on an audited platform that cannot be matched to an entry here will be flagged as a potential shadow account.

#### 📄 The `excel_config.json` file

Controls cell validation rules and conditional formatting applied to the **generic sheets** of the generated Excel report (e.g. "Access Review Scope List"). Plugin-specific sheets are **not** configured here, each plugin ships its own embedded JSON that governs its own columns and is not meant to be edited by the user.

**Structure:**

```text
{
    "Sheet Name": [
        {
            "column_name": "Column Header",
            "rules": [ ... ]
        }
    ]
}
```

Two `rule_type` values are supported:

**`list_validation`**: restricts a cell to a dropdown of allowed values.

| Field | Required | Description |
| :--- | :---: | :--- |
| `rule_type` | ✅ | `"list_validation"` |
| `column_name` | ✅ | Exact column header as it appears in the sheet |
| `validate` | ✅ | Always `"list"` |
| `source` | ✅ | Array of allowed string values |
| `ignore_blank` | - | Allow blank cells (default: `true`) |

**`conditional_format`**: highlights cells based on their value.

| Field | Required | Description |
| :--- | :---: | :--- |
| `rule_type` | ✅ | `"conditional_format"` |
| `column_name` | ✅ | Exact column header as it appears in the sheet |
| `format` | ✅ | Color name to apply (see palette below) |
| `criteria` | - | `"is_empty"`, `"is_not_empty"`, `"=="`, `"!="` (default: `"is_not_empty"`) |
| `value` | - | Comparison value: string, number, boolean, or array of values to match against |

**Available colors:**

| Name | Background | Font |
| :--- | :--- | :--- |
| `green` | `#C6EFCE` | `#006100` |
| `yellow` | `#FFEB9C` | `#9C5700` |
| `red` | `#FFC7CE` | `#9C0006` |
| `orange` | `#FBE2D5` | `#BD5015` |
| `blue` | `#CFEEFC` | `#145F82` |
| `black` | `#000000` | `#FFFFFF` |
| `white` | `#FFFFFF` | `#000000` |

---

**Full example:**

```json
{
    "Access Review Scope List": [
        {
            "column_name": "Access Review Method",
            "rules": [
                {
                    "rule_type": "list_validation",
                    "validate": "list",
                    "source": ["Automated (Assets Guardian)", "Partial Automated", "Manual"],
                    "ignore_blank": true
                },
                {
                    "rule_type": "conditional_format",
                    "format": "green",
                    "criteria": "==",
                    "value": "Automated (Assets Guardian)"
                },
                {
                    "rule_type": "conditional_format",
                    "format": "yellow",
                    "criteria": "==",
                    "value": ["Partial Automated", "Manual"]
                }
            ]
        },
        {
            "column_name": "Status",
            "rules": [
                {
                    "rule_type": "conditional_format",
                    "format": "red",
                    "criteria": "is_empty"
                }
            ]
        }
    ]
}
```

> 💡 **Tip:** A column entry can carry both a `list_validation` and one or more `conditional_format` rules simultaneously, they are applied independently.

#### 📄 The `pdf_config.json` file

Controls the visual appearance of the generated PDF audit report. The file has three top-level sections: `settings`, `colors`, and `fonts`. All sections are optional, only the values you want to override need to be specified, the rest fall back to built-in defaults.

**Structure:**

```text
{
    "settings": { ... },
    "colors":   { "<role>": { "r": 0, "g": 0, "b": 0 }, ... },
    "fonts":    { "<role>": { "family": "...", "style": "...", "size": 0 }, ... }
}
```

**`settings`**

| Field | Default | Description |
| :--- | :---: | :--- |
| `show_checkboxes` | `true` | Render an empty checkbox next to each finding (useful for manual review sign-off) |
| `checkbox_size` | `3.5` | Checkbox size in mm |
| `timezone` | `"UTC"` | Timezone used to format all timestamps in the report (any valid IANA name, e.g. `"Europe/Paris"`) |

**`colors`**

Each entry maps a color role to an RGB triplet `{"r": 0–255, "g": 0–255, "b": 0–255}`.

| Key | Default | Used for |
| :--- | :--- | :--- |
| `CRITICAL` | `255, 0, 0` | Severity label color for CRITICAL findings |
| `DANGER` | `255, 69, 0` | Severity label color for DANGER findings |
| `WARNING` | `255, 165, 0` | Severity label color for WARNING findings |
| `INFO` | `0, 122, 255` | Severity label color for INFO findings |
| `header_bg` | `208, 208, 208` | Background color for table headers (used by plugin builders) |
| `text` | `0, 0, 0` | Fallback text color when no severity color matches |

**`fonts`**

Each entry maps a font role to a font definition `{"family": "...", "style": "...", "size": N}`.

Font `style` follows FPDF conventions: `"B"` bold, `"I"` italic, `"BI"` bold-italic, `""` regular.

| Key | Default | Used for |
| :--- | :--- | :--- |
| `title` | `{ "family": "helvetica", "style": "B", "size": 16 }` | Cover page main title |
| `subtitle` | `{ "family": "helvetica", "style": "B", "size": 14 }` | Cover page subtitle |
| `heading` | `{ "family": "helvetica", "style": "B", "size": 12 }` | Section headings and summary labels |
| `body` | `{ "family": "helvetica", "style": "", "size": 10 }` | Finding descriptions and body text |
| `severity` | `{ "family": "helvetica", "style": "B", "size": 18 }` | Severity group label inside finding sections, if omitted, inherits the previous font |

---

**Full example (all defaults shown):**

```json
{
    "settings": {
        "show_checkboxes": true,
        "checkbox_size": 3.5,
        "timezone": "Europe/Paris"
    },
    "colors": {
        "CRITICAL":  { "r": 255, "g": 0, "b": 0 },
        "DANGER":    { "r": 255, "g": 69, "b": 0 },
        "WARNING":   { "r": 255, "g": 165, "b": 0 },
        "INFO":      { "r": 0, "g": 122, "b": 255 },
        "header_bg": { "r": 208, "g": 208, "b": 208 },
        "text":      { "r": 0, "g": 0, "b": 0 }
    },
    "fonts": {
        "title": { "family": "helvetica", "style": "B", "size": 16 },
        "subtitle": { "family": "helvetica", "style": "B", "size": 14 },
        "heading": { "family": "helvetica", "style": "B", "size": 12 },
        "body": { "family": "helvetica", "style": "", "size": 10 },
        "severity": { "family": "helvetica", "style": "B", "size": 18 }
    }
}
```

> 💡 **Tip:** You only need to include the keys you want to change. For example, to only adjust the timezone and make CRITICAL findings red-pink, a minimal config is sufficient, everything else keeps its default value.

## ▶️ Running

### 🛡️ Assets Guardian commands

Assets Guardian exposes three primary commands:

- `check`: Runs a global **checkup** of configuration files, output volume permissions, and Assets Guardian–remote instance connectivity for all enabled plugins.
- `sync`: Connects to all configured platform instances, retrieves their data, and **creates**/**updates** the corresponding Excel (`.xlsx`) database accordingly.
- `audit`: Evaluates the configured security policies, executes comparison checks over time across all instances, and **generates** the detailed PDF audit report.

These flags can be applied globally to any command. Note that they must be placed **before** the subcommand (e.g., `uv run assets-guardian --verbose <sync>`).

| Option / Flag | Description | Default / Behavior |
| :--- | :--- | :--- |
| `--config <path>` | Custom path to the application configuration file. | `config/config.yml` |
| `-v`, `--verbose` | Forces console logs to `DEBUG` level for deep troubleshooting. | `False` |
| `-q`, `--quiet` | Mutes non-critical logs. Only `CRITICAL` issues will show. | `False` |
| `--dry-run` | Simulation mode. Executes logic without applying real side effects. | `False` |
| `--no-interaction` | Disables all interactive prompts (perfect for automation/CI). | `False` |
| `--help` | Displays the help menu with all available options and exits. | - |
| `--version` | Displays the version of the tool and exits. | - |

### ▶️ Running by mode

The exact invocation pattern depends on which mode you installed. Replace `<command>` with `check`, `sync`, or `audit`. Global options (`--verbose`, `--dry-run`, etc.) always go **before** the subcommand.

#### 🐍 Standalone (with `assets-guardian`)

The `assets-guardian` command is on your `PATH` and can be invoked directly from any audit folder.

```bash
assets-guardian [options] <command>
```

Examples:

```bash
assets-guardian check
assets-guardian sync
assets-guardian --verbose audit
```

#### 🐍 Local dev (with `uv`)

Prefix every command with `uv run` to run from the project's virtual environment.

```bash
uv run assets-guardian [options] <command>
```

Examples:

```bash
uv run assets-guardian check
uv run assets-guardian sync
uv run assets-guardian --verbose audit
```

> 💡 **Tip:** Makefile shortcuts: `make local-check`, `make local-sync`, `make local-audit`.

#### 🐳 Docker image (use)

Mount the four required directories and pass credentials via an env file. The Docker image's entrypoint is `assets-guardian`, so options and subcommands are appended directly.

```bash
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/.assets-guardian_cache:/app/.assets-guardian_cache \
  --env-file .env \
  assets-guardian [options] <command>
```

> 💡 **Tip:** Makefile shortcuts: `make docker-check`, `make docker-sync`, `make docker-audit`.

#### 💻 Dev Container (VS Code)

Once the Dev Container is open in VS Code, the full toolchain is available, all three invocation modes work:

**Via `uv run` (preferred)**:

```bash
uv run assets-guardian [options] <command>
```

**Directly on `PATH`**:

```bash
assets-guardian [options] <command>
```

**Via Docker**: (docker-in-docker is available in the Dev Container):

```bash
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/.assets-guardian_cache:/app/.assets-guardian_cache \
  --env-file .env \
  assets-guardian [options] <command>
```

> 💡 **Tip:** Makefile shortcuts (`make local-check`, `make docker-check`, etc.) also work as-is.

#### 🐳 Docker image (develop)

Same as the *use* variant, with an additional `src/` bind-mount so that source code changes are reflected in the running container without rebuilding the image (the package is installed as editable inside the container).

```bash
docker run --rm \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/.assets-guardian_cache:/app/.assets-guardian_cache \
  --env-file .env \
  assets-guardian [options] <command>
```

> ⚠️ **Warning:** Only source code changes under `src/` are picked up live. Any change to dependencies (`pyproject.toml`, `uv.lock`) or the `Dockerfile` itself requires a full rebuild (`make docker-build`).
