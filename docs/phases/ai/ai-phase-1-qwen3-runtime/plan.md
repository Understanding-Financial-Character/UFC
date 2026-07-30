# AI Phase 1 - Qwen3 Runtime

## Status
VERIFYING
## Goal
Prepare Ollama-backed Qwen3 4B runtime boundary.
## Why
AI reports need a local provider boundary before prompt/report behavior is implemented.
## Prerequisites
Analysis output contract.
## In Scope
Provider interface, Ollama config, health checks, model selection docs, timeout and model-missing handling, fake/template providers for tests.
## Out of Scope
Prompt finalization, analysis orchestration connection, full transaction forwarding, score calculation, rule engine.
## Responsible Modules
`backend/app/ai`, Compose AI profile, docs.
## Contracts
AI provider config.
## Data Changes
None.
## Security Considerations
No raw transactions, tokens, ciphertext, secrets, or user identifiers in prompts.
## Implementation Tasks
- Add `ReportGenerator` protocol.
- Add `OllamaQwenReportGenerator`.
- Add `FakeReportGenerator`.
- Add `TemplateReportGenerator`.
- Add LLM temperature and timeout settings.
- Add Ollama health/model check.
- Test connection, timeout, missing model, and invalid response handling.
## Test Scenarios
Runtime unavailable, model missing, provider timeout.
## Completion Criteria
Provider boundary and runtime checks verified.
## Branch
`feat/ai-phase-1-qwen3-runtime`
## Dependencies
AN Phase 3 contracts.
