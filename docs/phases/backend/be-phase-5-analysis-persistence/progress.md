# BE Phase 5 - Analysis Persistence Progress

## Current Status
VERIFYING
## Implemented
- SQLAlchemy models for `analysis_runs`, `behavior_metrics`, `consumption_mbti_results`, and `ai_reports`.
- Execution `status` and result-quality `result_status` are separated on `analysis_runs`.
- `analysis_runs.result_status` is nullable until completion and is set through repository completion flow.
- `FAILED`, `PENDING`, and `RUNNING` runs must keep `result_status` null at DB constraint level.
- `result_status` values are `STANDARD`, `PROVISIONAL`, and `INSUFFICIENT_DATA`.
- `provisional_reasons` are stored as structured JSON and validated against analysis provisional reason values.
- `behavior_metrics` stores AN Phase 2 `BehaviorFeatureResult` core fields: `feature_code`, `status`, `raw_value`, `normalized_score`, `unit`, and `sample_count`.
- `UNAVAILABLE` behavior features must not store `raw_value` or `normalized_score`; `AVAILABLE` behavior features must not store `unavailable_reason`.
- `consumption_mbti_results.mbti_type` is nullable.
- `consumption_mbti_results.result_status` duplicates the owning run result status so DB constraints reject forced MBTI for `INSUFFICIENT_DATA`.
- `behavior_metrics.metric_metadata.axisContributions` stores axis-level weighted contribution data.
- Axis score directions are copied from `backend/app/analysis/constants.py` into persisted MBTI results.
- `ai_reports` supports `COMPLETED`, `FALLBACK_COMPLETED`, and `FAILED`.
- AI report status, fallback fields, and failure fields are cross-validated by repository and DB constraints.
- Schema versions and snapshot hash fields are stored on analysis result tables.
- Child result rows inherit `snapshot_hash` from the owning analysis run.
- Analysis persistence models use PostgreSQL JSONB via SQLAlchemy type variants.
- Alembic migration `20260730_0005_analysis_persistence`.
- DB/repository tests for persistence, constraints, nullable MBTI, AI report status, and axis contribution validation.
## Remaining
Commit, push, and PR link.
## Contract Changes
Analysis output persistence contract updated with behavior feature core fields, nullable run result status lifecycle, snapshot inheritance, and AI report fallback consistency.
## Migration Changes
`20260730_0005_analysis_persistence` adds analysis result enums and four analysis result tables.
## Linked PR
Not assigned.
## Commits
- `96758c0` feat: add analysis persistence schema
- `c4d6ee4` fix: align analysis persistence contracts
- `6f47f45` fix: tighten analysis persistence invariants
## Blockers
None.
## Handover Notes
Do not store analysis execution status on `groups`. BE Phase 6 should orchestrate run creation and status transitions using these persistence models.

BE Phase 6 must complete the run and save result rows in one DB transaction without an intermediate commit, because MBTI result persistence currently requires the owning run to be `COMPLETED` so it can copy the finalized `result_status`.
