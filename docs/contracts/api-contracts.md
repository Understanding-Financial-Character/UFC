# API Contracts

## Purpose

This document defines how UFC manages API contracts during MVP development.

Contracts are documented before implementation and updated in the same PR as any API behavior change.

## Contract Ownership

- Backend owns request validation, response shape, status codes, and persistence semantics.
- Frontend consumes documented contracts and should not depend on undocumented response fields.
- AI analysis consumes backend-defined analysis input and output contracts.

## Change Rules

- Additive optional fields are allowed when documented.
- Required field changes require contract update, implementation update, and verification evidence.
- Removing or renaming fields requires an ADR or explicit phase decision note.
- Error responses must follow `docs/contracts/error-contract.md`.
- Analysis inputs and outputs must follow the dedicated analysis contract documents.

## Initial MVP API Areas

- Groups and members
- Member MBTI registration
- Transaction upload or mock scenario selection
- Analysis request and status
- Spending MBTI result
- AI report retrieval
- Share card metadata

## Status

Phase 0 defines management rules only. Concrete endpoint paths and schemas will be finalized in the backend phase before implementation.
