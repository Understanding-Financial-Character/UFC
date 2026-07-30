# Frontend Architecture

## Responsibility

React Web owns user-facing workflows and visualization.

- Group setup and member MBTI input screens
- Transaction upload or mock scenario selection screens
- Spending MBTI result screens
- Member MBTI and account MBTI comparison views
- Consumption pattern graph views
- AI report and share card presentation

## Boundaries

- Frontend does not calculate authoritative analysis scores.
- Frontend does not call the LLM API directly.
- Frontend does not store secrets, real account identifiers, or raw financial personal data outside API-approved state.
- Frontend displays analysis uncertainty when the backend marks a result as provisional.

## Contract Usage

Frontend API calls must follow `docs/contracts/api-contracts.md`.

Request and response types should be generated from or manually kept aligned with documented contracts until an OpenAPI generation workflow is introduced.

## State Ownership

- UI state: selected screen, filters, graph focus, loading state
- Server state: groups, members, transactions, analysis results, reports
- Derived display state: formatted labels, chart-friendly series, graph layout

Server state remains owned by FastAPI and PostgreSQL. Server data fetched by React is cached through RTK Query, not duplicated into feature Redux slices unless it is local UI state.

## Authentication State

- Access tokens are kept in Redux in-memory auth state and attached to API calls by RTK Query `prepareHeaders`.
- Refresh token plaintext is not stored in Redux. FE Phase 1 isolates it behind `refreshTokenStorage` for MVP browser session continuity.
- Passwords and form field contents remain local to React forms and are not copied into Redux.
- On `401 AUTHENTICATION_REQUIRED`, RTK Query performs one refresh-token rotation attempt, retries the original request on success, and clears local session state on failure.
- `403 PERMISSION_DENIED` is represented by the shared forbidden screen and role guard.
