# Troubleshooting Entra ID Auth with Declarative Agents + Dev Proxy

## 1. `invalid_client` — Missing Service Principal

**Error:** `AADSTS7000215: Invalid client secret provided`

**Cause:** `aadApp/create` only creates the app registration, not the enterprise app (service principal). Without a service principal, Entra can't authenticate the app.

**Fix:** Add `generateServicePrincipal: true` to the `aadApp/create` step. Requires schema `v1.11` or later.

## 2. `AADSTS650053` — Unqualified Scopes

**Error:** `AADSTS650053: The application asked for scope 'Dishes.Read' that doesn't exist on the resource`

**Cause:** Bare scope names like `Dishes.Read` default to the Microsoft Graph resource. Custom scopes must include the full app URI.

**Fix:** Fully qualify all scopes in the OpenAPI spec:

```yaml
# Wrong
Dishes.Read
# Correct
api://${{ENTRA_APP_CLIENT_ID}}/Dishes.Read
```

## 3. `Something went wrong` — Client Secret Cleared by Manifest Update

**Error:** Generic "Something went wrong" after successful Entra authentication. Auth code is issued, but token exchange fails.

**Cause:** The `aadApp/update` provisioning step clears `passwordCredentials` from the Entra app when applying the manifest. The client secret created by `aadApp/create` becomes orphaned — it's stored in the env file but no longer exists on the app. The Copilot platform then fails when exchanging the auth code because the secret is invalid.

**Fix:** After provisioning, verify the app has credentials:

```bash
az ad app show --id <CLIENT_ID> --query passwordCredentials
```

If empty, add one:

```bash
az ad app credential reset --id <CLIENT_ID> --append
```

Consider adding a post-provision script step to regenerate the secret.

## 4. `401 Unauthorized` — Dev Proxy Audience Mismatch

**Error:** `IDX10214: Audience validation failed` from Dev Proxy's CrudApiPlugin

**Cause:** With `requestedAccessTokenVersion: 2` in the Entra manifest, v2.0 tokens use the raw app ID (GUID) as the `aud` claim — not the identifier URI (`api://GUID`). The Dev Proxy `entraAuthConfig.audience` was set to `api://CLIENT_ID`, which didn't match the token.

**Fix:** Set the Dev Proxy audience to the GUID only:

```json
// Wrong
"audience": "api://137e538e-25d8-4b89-aaa1-edb7daac8078"
// Correct
"audience": "137e538e-25d8-4b89-aaa1-edb7daac8078"
```

## 5. PKCE + OAuth Update Required

**Error:** Token exchange failures even with correct credentials.

**Cause:** The Copilot platform requires PKCE for the authorization code flow and needs `oauth/update` to keep the registration in sync.

**Fix:** Add `isPKCEEnabled: true` to `oauth/register` and add an `oauth/update` step after it in the provisioning lifecycle.
