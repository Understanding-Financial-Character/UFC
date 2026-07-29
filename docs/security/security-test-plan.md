# Security Test Plan

## Phase 0

- Confirm no secrets are introduced in documentation.
- Confirm MVP exclusions remain documented.
- Confirm restricted data is not added to fixtures or examples.

## BE Phase 3

- `SEC-01`: Passwords and refresh tokens are not stored in plaintext.
- `SEC-02`: Users cannot read another user's groups.
- `SEC-03`: Admin user summaries do not return raw email.
- `SEC-04`: API responses do not expose `password_hash`, `email_ciphertext`, or `email_lookup_hmac`.
- `SEC-05`: Required security settings are validated before app startup.
- `SEC-06`: Failed login logs do not include password or token values.
- `SEC-07`: Tampered ciphertext cannot be decrypted.
- Login rate limit blocks repeated failed attempts.
- Refresh and logout token flow works.

## Future Backend Phase

- Validate authentication and authorization checks.
- Verify API errors do not expose stack traces or secrets.
- Test access control for group, transaction, analysis, and report resources.

## Future AI Phase

- Verify prompts do not include unnecessary raw transaction data.
- Verify provisional analysis wording is preserved.
- Verify LLM failures return normalized API errors.

## Future Frontend Phase

- Verify sensitive values are not stored in browser logs.
- Verify share views do not expose raw transaction data.
