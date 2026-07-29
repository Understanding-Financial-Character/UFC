# Data Protection

## Storage

PostgreSQL stores MVP relational data. Sensitive data must be minimized and scoped to MVP use.

## Logging

Logs must not include:

- Raw transaction uploads
- Account identifiers
- API keys
- LLM request secrets
- Full AI prompt payloads containing sensitive metrics

## LLM Data Handling

Only structured evidence required for explanation should be sent to the LLM API.

The AI layer should receive metrics and labels, not unnecessary raw transaction details.

## Retention

Retention policy is not implemented in Phase 0. Before production-like data is used, retention and deletion rules must be documented and implemented.
