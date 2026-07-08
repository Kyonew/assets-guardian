# 🔑 Credentials & Configuration

This guide explains how to configure the **Dolibarr plugin** in `config.yml`, how to generate the credentials Assets Guardian needs, and the minimum permissions to grant on the Dolibarr side.

The plugin connects to the **Dolibarr REST API** to collect user identities (state, MFA, superadmin flag), groups, group memberships, and module permissions. It is **read-only**: no data is ever written to Dolibarr.

## 📡 Connection method

| | |
| :--- | :--- |
| **Protocol** | REST API over HTTPS |
| **Endpoint** | `https://<your-dolibarr>/api/index.php` |
| **Authentication** | Per-user API key, sent in the `DOLAPIKEY` HTTP header |

## ⚙️ `config.yml` section

Add one block per Dolibarr instance you want to audit:

```yaml
dolibarr:
  main: # Arbitrary instance label
    url: "https://dolibarr.company.com/api/index.php"
    credentials:
      dolapikey: "${DOLIBARR_MAIN_TOKEN}"
```

| Field | Required | Description |
| :--- | :--- | :--- |
| `url` | ✅ | Full URL of the Dolibarr REST API, **including** the `/api/index.php` suffix. |
| `credentials.dolapikey` | ✅ | The Dolibarr API key (`DOLAPIKEY`) of the account used by Assets Guardian. See [Generating the credentials](#) below. |

> ⚠️ **Warning:** Never write the API key in plain text in `config.yml`. Use the `${VAR_NAME}` syntax to reference an environment variable, it is resolved at startup (see [GETTING_STARTED.md](#)).
>
> 💡 **Tip:** You can declare several instances (e.g. `prod`, `test`) under the `dolibarr:` key, each with its own `url` and its own API key.

## 🔐 Environment variables

Declare the referenced variables in your `.env` file (or inject them via your shell, Docker, or CI/CD secrets):

```bash
# .env
DOLIBARR_MAIN_TOKEN=usi35xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 **Tip:** When running several instances, embed the instance label in the variable name (`DOLIBARR_PROD_TOKEN`, `DOLIBARR_TEST_TOKEN`, ...) to keep `.env` readable.

## 🛠️ Generating the credentials

**Prerequisites:** a Dolibarr **Administrateur système** account. Only an administrator can enable modules, manage permissions, and generate API keys.

### Step 1: Enable the REST API module

1. In Dolibarr, go to **Home → Setup → Modules/Applications**.
2. In the **Interfaces & Connectors** category, find **Web services API REST (server)**.
3. Enable the module.

Once enabled, the API (and its interactive explorer) is served at:

```text
https://<your-dolibarr>/api/index.php
https://<your-dolibarr>/api/index.php/explorer/   ← interactive API explorer (Swagger)
```

### Step 2: Create a dedicated service account (recommended)

The API key is **tied to a Dolibarr user** and inherits exactly that user's permissions. Rather than reusing a real (human) administrator account, create a dedicated read-only user (e.g. `svc-assets-guardian`):

1. Go to **Users & Groups → New user**.
2. Give it an explicit login and disable what it does not need (no email notifications, etc.).

> 💡 **Tip:** A dedicated account makes the audit traffic identifiable in Dolibarr logs and lets you revoke Assets Guardian's access without impacting anyone.

### Step 3: Grant the minimum permissions

On the service account's card, open the **Permissions** tab and grant only the read permissions of the **Users & Groups** (the `Consulter les autres utilisateurs, les groupes et leurs permissions` permission only) module:

| Why Assets Guardian needs it |
| :--- |
| `GET /users`, `GET /users/{id}`:  collect the user list and their details (state, MFA, admin flag) |
| `GET /users/{id}?includepermissions=1`: collect module permissions per user |
| `GET /users/groups`, `GET /users/{id}/groups`: collect groups and memberships |

> ⚠️ **Warning:** Do not grant the `superadmin` flag or any write permission. The plugin only performs `GET` requests, anything beyond read access on `Users & Groups` is unnecessary exposure.

### Step 4: Generate the API key (`DOLAPIKEY`)

1. Open the service account's user card and click **Modify**.
2. In the **Key for API** field, click the generation icon (dice) to generate a new key.
3. Save the user card, then copy the generated key into your `.env` file.

> ⚠️ **Warning:** A user without an API key cannot use the REST API at all, even if the module is enabled and permissions are granted.

## ✅ Verifying the setup

Run the built-in health check, it validates connectivity and credentials for every configured instance:

```bash
assets-guardian check
```

Or test the API manually with `curl`:

```bash
curl -H "DOLAPIKEY: <your-api-key>" \
     -H "Accept: application/json" \
     "https://<your-dolibarr>/api/index.php/users?limit=1"
```

A `200` response with a JSON payload means the module, key, and permissions are correctly set up.

## 🧯 Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `401 Unauthorized` | Invalid `dolapikey`, or the user has no API key | Regenerate the key (Step 4) and update your `.env` |
| `403 Forbidden` | The service account lacks read permissions | Grant the *Users & Groups* read permissions (Step 3) |
| `404 Not Found` on every endpoint | REST API module disabled, or `url` missing the `/api/index.php` suffix | Enable the module (Step 1) and set `url` to the **full** API URL, e.g. `https://dolibarr.company.com/api/index.php` |
| Health check fails but `curl` works | The health check reads `GET /users/1`, user ID `1` may not exist or not be readable | Verify the service account can read the user with ID 1 via the API explorer |

## 🛡️ Security recommendations

- Treat the `DOLAPIKEY` like a password: it grants the full rights of its owner, with no expiration date.
- Keep the key out of version control: `.env` is git-ignored, `config.yml` must only contain the `${...}` reference.
- Rotate the key periodically by regenerating it on the user card (the old key is revoked instantly).
- Prefer a dedicated read-only service account over a human account (see Step 2).
