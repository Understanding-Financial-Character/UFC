# AI Phase Progress

## Status

COMPLETED

## Implemented Work

- Added concrete `analysis-input-v1` Pydantic schemas for members and normalized transactions.
- Added concrete `behavior-metrics-v1` Pydantic output schemas.
- Added deterministic behavior metric calculation under `backend/app/analysis`.
- Added category concentration, spending volatility, repeat purchase ratio, weekend spending ratio, and planned spending ratio.
- Added fixed half-up rounding to two decimal places.
- Added metric evidence generation for calculated and skipped metrics.
- Added minimum-data and missing-value policies to the analysis output contract.
- Added tests for normal, concentrated, repeated, volatile, sparse/missing, and deterministic rerun scenarios.

## Changed Contracts

- `docs/contracts/analysis-input-contract.md` now documents `analysis-input-v1`.
- `docs/contracts/analysis-output-contract.md` now documents `behavior-metrics-v1` and AI Phase 1 metric formulas.

## Remaining Work

- Persisted analysis result schema remains out of scope.
- Spending MBTI type calculation remains out of scope.
- LLM prompt/client/report generation remains out of scope.
- Transaction upload API remains out of scope.

## Linked Branch, PR, Commits

- Branch: `feat/ai-phase-1-behavior-metrics`
- PR: Not assigned
- Commits: None
