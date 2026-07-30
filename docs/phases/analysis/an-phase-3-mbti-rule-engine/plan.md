# AN Phase 3 - Consumption MBTI Rule Engine

## Status
IMPLEMENTED
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
Implemented `consumption-mbti-v1.yaml`, rule loader, axis scorer, confidence helper, and golden tests.
## Test Scenarios
Strong E/I, S/N, T/F, J/P, borderline, insufficient data, nullable feature coverage, synthetic data, outlier contribution, and conflicting signals.
## Completion Criteria
Rule outputs verified against golden scenarios.
## Branch
`feat/an-phase-3-consumption-mbti-rule-engine`
## Dependencies
AN Phase 2.
