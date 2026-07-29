# ADR-0002. Development Tracking Structure

## Status

Accepted

## Context

UFC already has initial planning, architecture, evidence, and troubleshooting documents. The MVP now needs a development tracking structure that connects those documents to phase-specific implementation and verification work.

## Decision

Add dedicated documentation areas for:

- Component architecture boundaries
- API and analysis contracts
- Phase plans, progress, and verification
- Security data classification and test planning

Each phase folder keeps `plan.md`, `progress.md`, and `verification.md`. Reusable troubleshooting details remain under `docs/troubleshooting`.

## Consequences

- Every implementation phase must update its plan, progress, and verification files.
- Contract changes must be documented with implementation changes.
- MVP exclusions remain visible across phase planning.
- Phase documents should not duplicate long troubleshooting writeups.
