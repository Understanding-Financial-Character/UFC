# Security Test Plan

## Phase 0

- Confirm no secrets are introduced in documentation.
- Confirm MVP exclusions remain documented.
- Confirm restricted data is not added to fixtures or examples.

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
