# AI Phase 2 - Grounded Report

## Status
VERIFYING
## Goal
Generate user-friendly Qwen3 4B reports from deterministic results only.
## Why
Users need readable explanations without unsupported claims.
## Prerequisites
AI Phase 1. AN Phase 3 and BE analysis persistence provide later orchestration inputs.
## In Scope
Prompt versioning, grounded input filtering, report validation, fallback handling.
## Out of Scope
Score calculation, MBTI decision, raw transaction summarization, analysis orchestration hookup, `ai_reports` persistence.
## Responsible Modules
`backend/app/ai`, tests, docs/security.
## Contracts
AI report input/output and validation contracts.
## Data Changes
None. `ai_reports` persistence remains a later backend phase.
## Security Considerations
Strict prompt minimization and no secret/raw financial transfer.
## Implementation Tasks
- Implement grounded report input DTO.
- Implement Pydantic output schema.
- Implement JSON extraction and one repair attempt.
- Implement evidence number validation.
- Implement unsupported claim and prohibited wording checks.
- Implement timeout/provider failure template fallback.
- Record prompt version, model, latency, fallback status, repair status, and validation flags.
## Test Scenarios
Success, sparse data, hallucination validation failure, provider failure.
## Completion Criteria
Reports cite only supplied evidence and preserve limitations.
## Branch
`feat/ai-phase-2-grounded-report`
## Dependencies
AI Phase 1, AN Phase 3, BE Phase 5/6.
