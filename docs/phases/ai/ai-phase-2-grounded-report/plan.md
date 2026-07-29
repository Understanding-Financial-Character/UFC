# AI Phase 2 - Grounded Report

## Status
NOT_STARTED
## Goal
Generate user-friendly Qwen3 4B reports from deterministic results only.
## Why
Users need readable explanations without unsupported claims.
## Prerequisites
AI Phase 1, AN Phase 3, BE analysis persistence.
## In Scope
Prompt versioning, grounded input filtering, report validation, fallback handling.
## Out of Scope
Score calculation, MBTI decision, raw transaction summarization.
## Responsible Modules
`backend/app/ai`, `backend/app/orchestration`, tests, docs/security.
## Contracts
AI report input/output and validation contracts.
## Data Changes
Uses `ai_reports` from BE Phase 5.
## Security Considerations
Strict prompt minimization and no secret/raw financial transfer.
## Implementation Tasks
Implement prompt, provider call, parser, validator, fallback.
## Test Scenarios
Success, sparse data, hallucination validation failure, provider failure.
## Completion Criteria
Reports cite only supplied evidence and preserve limitations.
## Branch
`feat/ai-phase-2-grounded-report`
## Dependencies
AI Phase 1, AN Phase 3, BE Phase 5/6.
