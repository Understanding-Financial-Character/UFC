# AN Phase 2 - Behavior Metrics Progress

## Current Status
IMPLEMENTED
## Implemented
- `behavior-features-v1` schema constants and frozen dataclass outputs.
- 18 deterministic behavior feature results from `NormalizedTransaction` rows.
- Available/unavailable feature states with raw value, normalized score, unit, sample count, and evidence.
- NULL marker denominator exclusion for shared, planned, and recurring ratios.
- Amount-based and count-based ratio separation.
- Weekly volatility with zero-division and cap handling.
- Median/MAD outlier detection with deterministic fallback.
- Defensive non-`WITHDRAWAL` filtering in the feature engine.
- Unit tests for required AN Phase 2 scenarios.
## Remaining
No AN Phase 2 implementation work remains. Axis weighting, rule engine, DB persistence, API routing, and Qwen3 usage remain later phases.
## Contract Changes
`analysis-output-contract.md` now documents `behavior-features-v1`, feature status, units, and implemented feature codes.
## Migration Changes
None.
## Linked PR
PR #6 was reviewed as prior art; this branch is the AN Phase 2 successor implementation.
## Commits
Pending final commit.
## Blockers
None.
## Handover Notes
Feature output applies no axis weights and makes no MBTI judgment. Rule-engine phases should consume only `AVAILABLE` features.
