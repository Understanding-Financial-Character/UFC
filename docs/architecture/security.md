# Security Architecture

## Scope

Security controls must match the MVP scope: mock or uploaded transaction data, member MBTI inputs, calculated analysis metrics, and AI reports.

Actual bank account connection, transfer execution, and credit score processing are excluded from the MVP.

## Principles

- Store the minimum data needed for MVP analysis.
- Do not store real account numbers or highly sensitive banking identifiers.
- Treat uploaded transaction data as sensitive financial behavior data.
- Send only necessary structured evidence to the LLM API.
- Keep secrets in environment variables or managed secret storage, never in source code.

## Data Protection Boundary

FastAPI is the security boundary for data access. React Web, mock data generators, and AI integrations must use backend-approved contracts.

## Related Documents

- `docs/security/data-classification.md`
- `docs/security/authentication-authorization.md`
- `docs/security/data-protection.md`
- `docs/security/secrets-key-management.md`
- `docs/security/security-test-plan.md`
