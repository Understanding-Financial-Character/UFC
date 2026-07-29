# Phase 0 Foundation Plan

## Phase Goal

Establish development tracking standards that connect PRD scope, architecture, contracts, security rules, phase progress, and verification evidence.

## Implementation Scope

- Reconfirm MVP included and excluded scope.
- Document frontend, backend, and AI responsibility boundaries.
- Define API contract management rules.
- Define phase status and completion criteria.
- Define security data classification standards.
- Record that analysis results are behavioral interpretations and may be provisional.
- Define branch, PR, and document update rules.

## Excluded Scope

- Runtime backend API implementation
- Frontend screens
- Database schema and migrations
- LLM prompt implementation
- Real bank account connection
- Transfers and automatic payments
- Credit score analysis
- Financial product recommendation

## Modules Expected To Change

- `docs/architecture`
- `docs/contracts`
- `docs/phases`
- `docs/security`
- `README.md` only if document entry links change

## Prerequisites

- `main` is clean and up to date with `origin/main`.
- Existing project decisions and architecture documents are read before editing.
- No uncommitted user changes are present.

## Product Completion Criteria

- Required Phase 0 document structure exists.
- MVP scope and exclusions are clearly documented.
- Responsibility boundaries are documented.
- API and analysis contract management rules are documented.
- Security data classification and secret handling standards are documented.
- Phase progress and verification files reflect actual work and commands.
- First vertical slice contract requirements are documented before backend implementation starts.

## Delivery Criteria

- Phase branch is pushed.
- PR is linked in `progress.md`.
- Review findings are resolved.
- PR is merged.
- Merge commit or squash commit is recorded.
- Completion date is recorded.
