# AN Phase 2 - Behavior Metrics

## Status
IN_PROGRESS
## Goal
Calculate deterministic behavior metrics from quality-checked analysis input.
## Why
Rule-based MBTI and Qwen reports need grounded metrics and evidence.
## Prerequisites
AN Phase 1 or a documented test stub.
## In Scope
Behavior metrics, evidence, deterministic output, rounding, minimum sample rules.
## Out of Scope
Rule engine, Qwen provider, DB persistence, API endpoints.
## Responsible Modules
`backend/app/analysis`, `backend/tests`, `docs/contracts`, `docs/analysis`.
## Contracts
Behavior metrics DTOs.
## Data Changes
None in this phase unless later explicitly approved.
## Security Considerations
Do not include raw identities or full transaction arrays in downstream AI payloads.
## Implementation Tasks
Tracked by PR #6.
## Test Scenarios
Normal, concentrated, repeat, volatile, missing/sparse, deterministic rerun.
## Completion Criteria
PR #6 or successor merged and verification recorded.
## Branch
`feat/ai-phase-1-behavior-metrics`
## Dependencies
AN Phase 1 or test stub.
