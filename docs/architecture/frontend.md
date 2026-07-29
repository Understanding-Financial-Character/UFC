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

Server state remains owned by FastAPI and PostgreSQL.
