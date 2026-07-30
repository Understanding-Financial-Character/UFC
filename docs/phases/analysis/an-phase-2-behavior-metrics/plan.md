# AN Phase 2 - Behavior Metrics

## Status
IMPLEMENTED
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
Implemented `behavior-features-v1` DTOs and deterministic feature calculations from AN Phase 1 `NormalizedTransaction` rows. Reviewed PR #6 and preserved usable calculation patterns for category concentration, merchant repetition, weekend spending, planned spending, volatility, and deterministic reruns while realigning names and inputs to AN Phase 2.
## Test Scenarios
Feature-level normal calculations, nullable behavior signals, zero transactions, one transaction, repeated merchants, new merchants, weekend and night boundaries, category concentration and diversity, outliers, and defensive exclusion of non-withdrawal rows.
## Completion Criteria
Implementation, contracts, docs, and verification recorded on `feat/an-phase-2-behavior-metrics`.
## Branch
`feat/an-phase-2-behavior-metrics`
## Dependencies
AN Phase 1 or test stub.
