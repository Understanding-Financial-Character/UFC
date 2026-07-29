# Data Protection

## Storage

PostgreSQL stores MVP relational data. Sensitive data must be minimized and scoped to MVP use.

BE Phase 3 stores email as:

- `email_ciphertext`
- `email_lookup_hmac`
- `email_key_version`

AES-256-GCM is used for field encryption. Email lookup uses HMAC over the normalized email value.

Encrypted email uses AES-GCM additional authenticated data bound to the user context: `user:{user_id}:email`. Moving ciphertext between users fails decryption instead of silently returning another user's email.

## Logging

Logs must not include:

- Raw transaction uploads
- Account identifiers
- API keys
- Access tokens and refresh tokens
- Passwords
- LLM request secrets
- Full AI prompt payloads containing sensitive metrics

API responses must not expose password hashes, refresh token hashes, ciphertext fields, or raw encrypted storage fields.

## LLM Data Handling

Only structured evidence required for explanation should be sent to the LLM API.

The AI layer should receive metrics and labels, not unnecessary raw transaction details.

## Retention

Retention policy is not implemented in Phase 0. Before production-like data is used, retention and deletion rules must be documented and implemented.
