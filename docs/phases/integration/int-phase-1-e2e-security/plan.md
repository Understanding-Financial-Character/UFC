# INT Phase 1 - E2E Security

## Status
NOT_STARTED
## Goal
Verify the complete local MVP workflow with security boundaries.
## Why
Independent phases do not prove the integrated product path.
## Prerequisites
Backend, analysis, AI, and frontend MVP slices.
## In Scope
End-to-end auth, group, transaction, analysis, report, and owner-access checks.
## Out of Scope
Production deployment.
## Responsible Modules
Compose, tests, docs/evidence.
## Contracts
All MVP runtime contracts.
## Data Changes
No new schema unless explicitly approved.
## Security Considerations
No cross-owner access, no raw secret/report leakage, no raw LLM transaction prompts.
## Implementation Tasks
Build E2E validation path and evidence.
## Test Scenarios
Happy path, owner denial, insufficient data, Qwen fallback.
## Completion Criteria
E2E local path verified.
## Branch
`feat/int-phase-1-e2e-security`
## Dependencies
Prior MVP phases.
