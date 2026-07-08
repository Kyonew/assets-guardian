# 🔑 Credentials & Configuration

This guide explains how to configure the **GitLab plugin** in `config.yml`, how to generate the credentials Assets Guardian needs, and the minimum permissions to grant on the GitLab side.

The plugin connects to the **GitLab REST API** (v4) to collect user identities (state, MFA, admin flag, sign-in IPs), assets (projects and groups), and each user's project and group memberships. It is **read-only**: no data is ever written to GitLab.

## 📡 Connection method

| | |
| :--- | :--- |
| **Protocol** | REST API (v4) over HTTPS |
| **Endpoint** | `https://<your-gitlab>/api/v4` |
| **Authentication** | Personal access token (PAT), sent in the `Authorization: Bearer` HTTP header |

## ⚙️ `config.yml` section

Add one block per GitLab instance you want to audit:

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
```

| Field | Required | Description |
| :--- | :--- | :--- |
| `url` | ✅ | Full URL of the GitLab REST API, **including** the `/api/v4` suffix (e.g. `https://gitlab.company.com/api/v4`). |
| `credentials.personnal_access_token` | ✅ | The personal access token of the account used by Assets Guardian. See **Generating the credentials** below. |

> ⚠️ **Warning:** Never write the token in plain text in `config.yml`. Use the `${VAR_NAME}` syntax to reference an environment variable, it is resolved at startup (see [GETTING_STARTED.md](#)).
>
> 💡 **Tip:** You can declare several instances (e.g. `prod`, `test`) under the `gitlab:` key, each with its own `url` and its own token.

## 🔐 Environment variables

Declare the referenced variables in your `.env` file (or inject them via your shell, Docker, or CI/CD secrets):

```bash
# .env
GITLAB_PROD_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
GITLAB_TEST_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
```

> 💡 **Tip:** When running several instances, embed the instance label in the variable name (`GITLAB_PROD_TOKEN`, `GITLAB_TEST_TOKEN`, ...) to keep `.env` readable.

## 🛠️ Generating the credentials

**Prerequisites:** a GitLab account with the **Administrator** access level. Only an administrator can list all users (including blocked ones), see their MFA status and admin flag, and read other users' memberships.

### Step 1: Create a dedicated service account (recommended)

The personal access token is **tied to a GitLab user** and inherits that user's access level. Rather than reusing a real (human) administrator account, create a dedicated user (e.g. `svc-assets-guardian`):

1. Go to **Admin area → Overview → Users → New user**.
2. Give it an explicit name and login, and disable what it does not need (no email notifications, etc.).

> 💡 **Tip:** A dedicated account makes the audit traffic identifiable in GitLab logs and lets you revoke Assets Guardian's access without impacting anyone.

### Step 2: Grant administrator access

On the service account's card (**Admin area → Overview → Users → Edit**), set **Access level** to **Administrator**. This is required by the endpoints the plugin reads:

| Why Assets Guardian needs it |
| :--- |
| `GET /users`, `GET /users/{id}`: collect the user list and their details (state, MFA, admin flag, sign-in IPs), the admin-only attributes are hidden from regular users |
| `GET /users/{id}/memberships`: collect each user's project and group memberships (admin-only endpoint) |
| `GET /projects`, `GET /groups`: collect the assets that accesses are mapped to |

> ⚠️ **Warning:** The plugin only performs `GET` requests, but an administrator's personal access token is highly sensitive, see security recommendations below.

### Step 3: Generate the personal access token

1. Signed in as the service account, go to `https://<your-gitlab>/-/user_settings/personal_access_tokens` (or **avatar → Edit profile → Access tokens**).
2. Click **Add new token**, give it an explicit name (e.g. `assets-guardian`) and an expiration date.
3. Select the `read_api` scope.
4. Click **Create personal access token**, then copy the generated token (`glpat-...`) into your `.env` file.

| Scope | Required | What it grants |
| :--- | :--- | :--- |
| `read_api` | ✅ | Read-only access to the whole API (users, projects, groups, memberships), including the health check (`GET /user`) |

> 💡 **Tip:** `read_api` is all the plugin needs: it is read-only, and combined with the administrator access level it exposes every endpoint the plugin reads. Avoid the broader `api` scope (full read/write access), and skip `read_user` (a subset of `read_api`).
>
> ⚠️ **Warning:** The token is displayed only once, right after creation. If you lose it, revoke it and generate a new one.

## ✅ Verifying the setup

Run the built-in health check, it validates connectivity and credentials for every configured instance:

```bash
assets-guardian check
```

Or test the API manually with `curl`:

```bash
curl -H "Authorization: Bearer <your-token>" \
     "https://<your-gitlab>/api/v4/user"
```

A `200` response with the service account's JSON profile means the token is correctly set up.

## 🧯 Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| `401 Unauthorized` | Token invalid, expired, or revoked | Regenerate the token (Step 3) and update your `.env` |
| `403 Forbidden` on `/users/{id}/memberships` | The account is not an administrator | Grant the Administrator access level (Step 2) |
| `404 Not Found` on every endpoint | `url` is missing the `/api/v4` suffix, or points to the wrong host | Set `url` to the **full API** URL, e.g. `https://gitlab.company.com/api/v4` |
| Health check passes but collection fails or user data is incomplete (missing MFA/admin flag, blocked users absent) | The health check (`GET /user`) only validates the token, while collection requires administrator access | Use an administrator service account (Step 2) |

## 🛡️ Security recommendations

- Treat the token like a password: even limited to the read-only `read_api` scope, it exposes everything an administrator can read (full user list, MFA status, sign-in IPs, every project and group).
- Keep the token out of version control: `.env` is git-ignored, `config.yml` must only contain the `${...}` reference.
- Set an expiration date at creation and rotate the token before it expires, revoke it instantly from the access tokens page if it leaks.
- Prefer a dedicated service account over a human account (see Step 1).
