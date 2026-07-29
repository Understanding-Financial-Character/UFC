# AN Phase 3 - Consumption MBTI Rule Engine

## Status
NOT_STARTED
## Goal
Implement the versioned rule engine that maps metrics to axis scores and nullable consumption MBTI.
## Why
Consumption MBTI must be deterministic and not decided by Qwen3.
## Prerequisites
AN Phase 2 behavior metrics.
## In Scope
Feature weights, coverage, axis scores, low-margin handling, nullable final type.
## Out of Scope
Qwen report generation and persistence APIs.
## Responsible Modules
`backend/app/analysis`, `backend/tests`, `docs/analysis`.
## Contracts
Rule output DTO and score direction contract.
## Data Changes
None directly.
## Security Considerations
No raw identities or full transaction arrays.
## Implementation Tasks
Implement rule version and golden tests.
## Test Scenarios
All four axes, low coverage, low margin, insufficient data, mock provisional.
## Completion Criteria
Rule outputs verified against golden scenarios.
## Branch
`feat/an-phase-3-mbti-rule-engine`
## Dependencies
AN Phase 2.
