# BE Phase 5 - Analysis Persistence Progress

## Current Status
VERIFYING
## Implemented
- SQLAlchemy models for `analysis_runs`, `behavior_metrics`, `consumption_mbti_results`, and `ai_reports`.
- Execution `status` and result-quality `result_status` are separated on `analysis_runs`.
- `result_status` values are `STANDARD`, `PROVISIONAL`, and `INSUFFICIENT_DATA`.
- `provisional_reasons` are stored as structured JSON.
- `consumption_mbti_results.mbti_type` is nullable.
- Repository validation rejects a forced MBTI when the owning run is `INSUFFICIENT_DATA`.
- `behavior_metrics.metric_metadata.axisContributions` stores axis-level weighted contribution data.
- Axis score directions are copied from `backend/app/analysis/constants.py` into persisted MBTI results.
- `ai_reports` supports `COMPLETED`, `FALLBACK_COMPLETED`, and `FAILED`.
- Schema versions and snapshot hash fields are stored on analysis result tables.
- Alembic migration `20260730_0005_analysis_persistence`.
- DB/repository tests for persistence, constraints, nullable MBTI, AI report status, and axis contribution validation.
## Remaining
Commit, push, and PR link.
## Contract Changes
Analysis output persistence contract updated.
## Migration Changes
`20260730_0005_analysis_persistence` adds analysis result enums and four analysis result tables.
## Linked PR
Not assigned.
## Commits
Pending.
## Blockers
None.
## Handover Notes
Do not store analysis execution status on `groups`. BE Phase 6 should orchestrate run creation and status transitions using these persistence models.
