<!--
  TEMPLATE: How to use this file:
  1. Copy it into your plugin folder: src/assets_guardian/plugins/<your_plugin>/CREDENTIALS.md
  2. Replace every `<...>` placeholder (kept in code spans so markdownlint stays quiet) and every `template` occurrence with your plugin's values.
  3. Resolve the `TODO` comments, then delete them (this header included).
  Real-world examples: plugins/gitlab/CREDENTIALS.md and plugins/dolibarr/CREDENTIALS.md
-->

# 🔑 Credentials & Configuration

This guide explains how to configure the **`<Service>` plugin** in `config.yml`, how to generate the credentials Assets Guardian needs, and the minimum permissions to grant on the `<Service>` side.

The plugin connects to the **`<Service>` API** to collect user identities (`<state, MFA, admin flag, ...>`), assets (`<projects, groups, ...>`), and each user's memberships. It is **read-only**: no data is ever written to `<Service>`.

<!-- TODO: Adjust the two paragraphs above: plugin name, API used, and exactly what is collected. Keep the read-only statement if it holds. -->

## 📡 Connection method

| | |
| :--- | :--- |
| **Protocol** | `<REST API over HTTPS, MySQL, ...>` |
| **Endpoint** | `https://<your-service>/<api-base-path>` |
| **Authentication** | `<Credential type, and how it is sent (HTTP header, ...)>` |

## ⚙️ `config.yml` section

Add one block per `<Service>` instance you want to audit:

```yaml
template: # TODO: must match the plugin's SOURCE_NAME (see constants.py)
  main: # Arbitrary instance label
    url: "https://<your-service>/<api-base-path>"
    credentials:
      api_token: "${TEMPLATE_MAIN_TOKEN}" # TODO: one key per credential field expected by the client
      any_other_field: "${TEMPLATE_MAIN_OTHER}" # Optional: add as many extra keys as your client needs
    any_other_setting: "<value>" # Optional: non-secret settings live at the instance level
```

The `credentials` block is a **free-form mapping**: Assets Guardian does not enforce any schema. Each plugin's client defines the keys it expects and reads them itself (e.g. `personnal_access_token` for GitLab, `dolapikey` for Dolibarr). Add one key per secret or connection parameter your client needs: a `username`/`password` pair, a `client_id`/`client_secret`, a database name, ...

The same principle applies to the **instance block itself**: `url` and `credentials` are only conventions, the whole block is passed verbatim to the plugin's client and collector. You can therefore add any top-level setting your plugin needs (a timeout, a scope filter, a feature flag, ...). Rule of thumb: secrets go under `credentials`, plain settings go at the instance level.

| Field | Required | Description |
| :--- | :--- | :--- |
| `url` | ✅ | Full URL of the `<Service>` API, **including** the `<api-base-path>` suffix. |
| `credentials.api_token` | ✅ | The `<credential type>` of the account used by Assets Guardian. See **Generating the credentials** below. |
| `credentials.<any_other_field>` | Plugin-specific | Any extra field your client reads from the `credentials` mapping. Document each one here with its exact expected format. |
| `<any_other_setting>` | Plugin-specific | Any extra instance-level setting your client or collector reads. Document each one here, with its default when omitted. |

<!-- TODO: One row per configuration field (rename/remove the `any_other_*` rows accordingly). Document required suffixes and formats precisely: a wrong `url` is the most common setup mistake. -->

> ⚠️ **Warning:** Never write the token in plain text in `config.yml`. Use the `${VAR_NAME}` syntax to reference an environment variable, it is resolved at startup (see [GETTING_STARTED.md](../../../../docs/markdown/GETTING_STARTED.md)). This applies to **every** key under `credentials`, not just the token.
>
> 💡 **Tip:** You can declare several instances (e.g. `prod`, `test`) under the `template:` key, each with its own `url` and its own token.

## 🔐 Environment variables

Declare the referenced variables in your `.env` file (or inject them via your shell, Docker, or CI/CD secrets):

```bash
# .env
TEMPLATE_MAIN_TOKEN=xxxxxxxxxxxxxxxxxxxx
```

<!-- TODO: Show the real token format/prefix if it has one (e.g. `glpat-...`), it helps users spot copy/paste mistakes. -->

> 💡 **Tip:** When running several instances, embed the instance label in the variable name (`TEMPLATE_PROD_TOKEN`, `TEMPLATE_TEST_TOKEN`, ...) to keep `.env` readable.

## 🛠️ Generating the credentials

**Prerequisites:** `<the account/role needed to perform the steps below, and why it is required>`.

<!-- TODO: Adapt the steps to your service, keeping the numbered-step structure. Add service-specific steps where needed (e.g. Dolibarr starts with an "Enable the REST API module" step). -->

### Step 1: Create a dedicated service account (recommended)

The `<credential type>` is **tied to a `<Service>` user** and inherits that user's permissions. Rather than reusing a real (human) account, create a dedicated user (e.g. `svc-assets-guardian`):

1. Go to **`<menu path>`**.
2. Give it an explicit name and login, and disable what it does not need (no email notifications, etc.).

> 💡 **Tip:** A dedicated account makes the audit traffic identifiable in `<Service>` logs and lets you revoke Assets Guardian's access without impacting anyone.

### Step 2: Grant the minimum permissions

`<How to grant the permissions/role/scopes on the service account, kept to the minimum the plugin needs.>`

| Why Assets Guardian needs it |
| :--- |
| `GET /<endpoint>`: `<what the plugin collects with it>` |
| `GET /<endpoint>`: `<what the plugin collects with it>` |

<!-- TODO: List every endpoint/query the plugin's repository actually reads, and the permission each one requires. -->

> ⚠️ **Warning:** Do not grant write permissions. The plugin only reads data, anything beyond read access is unnecessary exposure.

### Step 3: Generate the `<credential type>`

1. `<Where to go, signed in as the service account.>`
2. `<How to create the credential: give it an explicit name (e.g. assets-guardian), set an expiration date if supported.>`
3. `<Which scope(s) to select, and why.>`
4. Copy the generated token into your `.env` file.

> ⚠️ **Warning:** `<Display/retention rules, e.g. "the token is displayed only once, right after creation. If you lose it, revoke it and generate a new one.">`

## ✅ Verifying the setup

Run the built-in health check, it validates connectivity and credentials for every configured instance:

```bash
assets-guardian check
```

Or test the API manually with `curl`:

```bash
curl -H "<Auth header>: <your-token>" \
     "https://<your-service>/<api-base-path>/<health-check-endpoint>"
```

A `200` response with `<the expected payload>` means the credentials are correctly set up.

<!-- TODO: Use the same endpoint as the plugin's health_check() so the manual test and the built-in check are equivalent. -->

## 🧯 Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `401 Unauthorized` | Token invalid, expired, or revoked | Regenerate the token (Step 3) and update your `.env` |
| `403 Forbidden` | The service account lacks the required permissions | Grant the minimum permissions (Step 2) |
| `404 Not Found` on every endpoint | `url` is missing the `<api-base-path>` suffix, or points to the wrong host | Set `url` to the **full API** URL |
| `<Service-specific symptom>` | `<Likely cause>` | `<Fix>` |

<!-- TODO: Keep the generic rows that apply, then add the failure modes specific to your service (see the GitLab/Dolibarr files for real examples, e.g. a health check that passes while collection fails). -->

## 🛡️ Security recommendations

- Treat the token like a password: `<what it exposes if it leaks>`.
- Keep the token out of version control: `.env` is git-ignored, `config.yml` must only contain the `${...}` reference.
- `<Expiration/rotation policy: set an expiration date if supported, rotate the credential periodically, revoke it instantly if it leaks.>`
- Prefer a dedicated read-only service account over a human account (see Step 1).
