# AI Phase 1 - Qwen3 Runtime

## Status
NOT_STARTED
## Goal
Prepare Ollama-backed Qwen3 4B runtime boundary.
## Why
AI reports need a local provider boundary before prompt/report behavior is implemented.
## Prerequisites
Analysis output contract.
## In Scope
Provider interface, Ollama config, health checks, model selection docs.
## Out of Scope
Report generation logic, score calculation, rule engine.
## Responsible Modules
`backend/app/ai`, Compose AI profile, docs.
## Contracts
AI provider config.
## Data Changes
None.
## Security Considerations
No raw transactions, tokens, ciphertext, secrets, or user identifiers in prompts.
## Implementation Tasks
Implement provider in future phase.
## Test Scenarios
Runtime unavailable, model missing, provider timeout.
## Completion Criteria
Provider boundary and runtime checks verified.
## Branch
`feat/ai-phase-1-qwen3-runtime`
## Dependencies
AN Phase 3 contracts.
