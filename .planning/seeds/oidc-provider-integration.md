---
name: oidc-provider-integration
description: Swap mock OIDC authentication for real enterprise identity provider when IDP is determined
metadata:
  type: seed
  trigger_condition: Enterprise identity provider (Okta, Azure AD, Keycloak, or LDAP) is confirmed and credentials/config are available
  planted_date: 2026-05-21
---

# Seed: OIDC Real Provider Integration

## Context
MVP starts with mock OIDC that returns a fixed test user. When the enterprise confirms which identity provider to use, trigger this work.

## What to Do
1. Implement real OIDC adapter in `backend/app/auth/oidc.py` using the confirmed provider's configuration (client ID, client secret, discovery URL, callback URL)
2. Update `current_user.py` to resolve real tokens instead of mock
3. Add provider-specific config to environment variables / `.env`
4. Test auth flow end-to-end with real provider
5. Verify audit events now link to real user IDs and department info

## Dependencies
- [[key-decisions]] — mock auth strategy decision
- Enterprise must provide: IDP type, discovery endpoint, client credentials, user attribute mapping (department/group)