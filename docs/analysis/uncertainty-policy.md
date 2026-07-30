# Uncertainty Policy

## Result Status

`analysis_runs.result_status` values:

- `STANDARD`: configured sufficiency rules are met.
- `PROVISIONAL`: output is usable but has documented limitations.
- `INSUFFICIENT_DATA`: output should not force consumption MBTI.

## Provisional Reasons

Common reasons:

- `INSUFFICIENT_TRANSACTION_COUNT`
- `SHORT_ANALYSIS_PERIOD`
- `MISSING_CATEGORY_DATA`
- `MISSING_MERCHANT_DATA`
- `LOW_AXIS_COVERAGE`
- `LOW_AXIS_SCORE_MARGIN`
- `AXIS_SCORE_TIE`
- `SYNTHETIC_DATA`

## MBTI Output

When data is insufficient, `consumption_mbti_results.mbti_type` remains `NULL`. Qwen3 may explain limitations but must not invent a missing final type.

## AI Report Impact

Qwen3 failure does not invalidate deterministic results. `ai_reports.status` records report generation separately with `COMPLETED`, `FALLBACK_COMPLETED`, or `FAILED`.
