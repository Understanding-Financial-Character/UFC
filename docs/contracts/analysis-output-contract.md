# Analysis Output Contract

## Purpose

Defines deterministic analysis outputs consumed by backend persistence, frontend result views, and Qwen3 report generation.

## Status

Behavior feature output is implemented by AN Phase 2. `consumption-mbti-v1` is implemented by AN Phase 3. Grounded AI report output remains a separate AI contract.

## Schema Versions

- `behavior-features-v1`
- `axis-scores-v1`
- `consumption-mbti-v1`
- `grounded-ai-report-v1`

## Behavior Metrics

```json
{
  "schemaVersion": "behavior-features-v1",
  "features": [
    {
      "featureCode": "SHARED_EXPENSE_RATIO",
      "status": "AVAILABLE",
      "rawValue": 0.42,
      "normalizedScore": 0.42,
      "unit": "AMOUNT_RATIO",
      "sampleCount": 18,
      "evidence": ["공동지출 42000원이 표본 금액 100000원의 42.0%입니다."]
    }
  ],
  "policyVersion": "behavior-policy-v1",
  "categoryMappingVersion": "category-map-v2",
  "analysisTimezone": "Asia/Seoul",
  "sourceType": "CSV",
  "isSynthetic": false
}
```

Behavior features include calculation evidence and minimum-data handling. Missing inputs produce `status=UNAVAILABLE` with `rawValue=null` and `normalizedScore=null`, not zero.
`sourceType` is the canonical provenance value. `isSynthetic` is a derived marker on the behavior metrics result, and the rule engine treats `MOCK` and `INTERNAL_TEST` sources as synthetic even if a caller supplies a contradictory boolean.

Feature units:

- `AMOUNT_RATIO`: amount numerator divided by amount denominator
- `COUNT_RATIO`: count numerator divided by count denominator
- `SCORE`: already normalized score such as entropy diversity or capped volatility

Implemented AN Phase 2 feature codes:

- `SHARED_EXPENSE_RATIO`
- `WEEKEND_SOCIAL_SPENDING_RATIO`
- `NIGHT_SPENDING_RATIO`
- `TRAVEL_EXPERIENCE_RATIO`
- `PRACTICAL_SPENDING_RATIO`
- `CATEGORY_CONCENTRATION`
- `CATEGORY_DIVERSITY_SCORE`
- `NEW_MERCHANT_RATIO`
- `REPEAT_MERCHANT_RATIO`
- `EXPERIENCE_SPENDING_RATIO`
- `SAVING_EDUCATION_RATIO`
- `RELATIONSHIP_SPENDING_RATIO`
- `SHARED_EXPERIENCE_RATIO`
- `GIFT_ANNIVERSARY_RATIO`
- `PLANNED_EXPENSE_RATIO`
- `RECURRING_EXPENSE_RATIO`
- `WEEKLY_EXPENSE_VOLATILITY`
- `OUTLIER_RATIO`

AN Phase 2 consumes only `NormalizedTransaction` rows from preprocessing. It defensively ignores non-`WITHDRAWAL` transaction types if they are passed by mistake.

Calendar features use the analysis timezone, fixed to `Asia/Seoul` for the MVP. `NormalizedTransaction.occurred_at` remains UTC-normalized from AN Phase 1, but weekend and night predicates convert it to the analysis timezone before reading weekday or hour.

`NEW_MERCHANT_RATIO` is `UNAVAILABLE` in AN Phase 2 because true new-merchant status requires a merchant baseline before the analysis window. `REPEAT_MERCHANT_RATIO` is calculated within the current window as visits after the first occurrence, so first visits and repeat visits are not double-counted.

`WEEKLY_EXPENSE_VOLATILITY` requires observation start/end context, includes calendar weeks with zero spending, records raw coefficient of variation in `rawValue`, and caps `normalizedScore` at `1.0`.

## Axis Scores

Axis score direction is fixed:

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

Axis scoring uses only available features and renormalizes remaining weights.

## Consumption MBTI Result

```json
{
  "schemaVersion": "consumption-mbti-v1",
  "ruleVersion": "consumption-mbti-v1",
  "mbtiType": "ENFP",
  "axisScores": {
    "EI": 0.62,
    "SN": 0.58,
    "TF": 0.55,
    "JP": 0.71
  },
  "axisCoverage": {
    "EI": 1.0,
    "SN": 0.75,
    "TF": 0.9,
    "JP": 0.8
  },
  "axisMargins": {
    "EI": 12.0,
    "SN": 8.0,
    "TF": 5.0,
    "JP": 21.0
  },
  "confidence": {
    "level": "LOW",
    "score": 0.42
  },
  "resultStatus": "PROVISIONAL",
  "provisionalReasons": ["SN_LOW_AXIS_COVERAGE"],
  "primaryEvidence": [
    {
      "axis": "SN",
      "featureCode": "CATEGORY_DIVERSITY_SCORE",
      "direction": "HIGH",
      "weight": 0.25,
      "normalizedWeight": 0.3333,
      "featureScore": 0.8,
      "contributionScore": 0.8,
      "contribution": 0.2667,
      "highPoleSupport": 0.8,
      "lowPoleSupport": 0.2,
      "signedContribution": 0.2,
      "decidedPoleContribution": 0.2667,
      "evidence": ["Category diversity score 0.8000 from 4 category amount buckets."]
    }
  ]
}
```

`mbtiType` is nullable when data is insufficient.

Rule-engine behavior:

- Each axis is scored independently.
- Higher axis scores mean E, N, F, and P respectively.
- Unavailable features are excluded from that axis and remaining feature weights are renormalized.
- Axis coverage is the configured available weight divided by total configured axis weight.
- Coverage below `0.50` defers that axis and prevents final `mbtiType` generation.
- Coverage from `0.50` to below `0.70` keeps the axis decision but marks the result provisional.
- Exact score ties at `0.50` defer the axis, add `AXIS_SCORE_TIE`, and prevent final `mbtiType` generation.
- Non-zero margin below `5.0` points keeps the axis decision but adds `LOW_AXIS_SCORE_MARGIN`.
- Mock or generated data adds `SYNTHETIC_DATA`.
- Primary evidence is axis-specific, limited to the top contributing features per axis, so the same feature can contribute separately to multiple axes. Full contribution traces remain available on each axis result.
- Feature contributions expose high-pole support, low-pole support, signed contribution, and decided-pole contribution so low-pole decisions retain meaningful evidence.

`resultStatus` values:

- `STANDARD`
- `PROVISIONAL`
- `INSUFFICIENT_DATA`

## AI Report Dependency

Qwen3 report generation receives only:

- Consumption MBTI
- Axis scores
- Confidence
- Top evidence
- Member MBTI summary
- Limitations
- Result status

Qwen3 must not receive user email, user name or nickname, internal user id, full transaction arrays, raw transaction memo text, tokens, ciphertext, or secrets.

Qwen3 failure does not invalidate deterministic analysis output.

Evidence items sent to Qwen3 must include a value type:

```json
{
  "metric": "CATEGORY_CONCENTRATION",
  "value": 0.64,
  "valueType": "RATIO",
  "basis": "FOOD 카테고리가 전체 지출의 64%를 차지"
}
```

`valueType` values:

- `RATIO`: decimal ratio such as `0.64`; reports may use `0.64` or `64%`.
- `PERCENTAGE`: percentage value such as `64`; reports may use `64` or `64%`.
- `COUNT`: count value; reports may use the original number only.
- `AMOUNT`: monetary amount; reports may use the original number only.
- `DURATION`: duration value; reports may use the original number only.
- `SCORE`: score value; reports may use the original number only.
- `TEXT`: non-numeric value.

Numeric grounding must not convert count, amount, duration, score, or text evidence into percentages.

## Grounded AI Report

AI Phase 2 defines `grounded-ai-report-v1`.

Required report fields:

```json
{
  "headline": "ENFP 소비 리포트",
  "summary": "제공된 근거를 바탕으로 한 요약입니다.",
  "strengths": ["근거 기반 장점"],
  "commonPoints": ["구성원 MBTI와 소비 MBTI의 공통점"],
  "differences": ["구성원 MBTI와 소비 MBTI의 차이점"],
  "observationPoints": ["관찰 포인트"],
  "conversationQuestions": ["대화 질문"],
  "disclaimer": "실제 성격 진단이나 금융 진단이 아닙니다."
}
```

Validation requirements:

- Strict Pydantic schema validation. Unknown output fields are rejected.
- Numeric evidence consistency check against the same top evidence prompt context sent to Qwen3.
- Limited unsupported claim check. MVP validation records `unsupportedClaims=false` and `unsupportedClaimsCheck=LIMITED` because full natural-language entailment is out of scope.
- Real personality or financial diagnosis wording check.
- Financial product recommendation check.
- JSON parse/schema failure gets one repair attempt.
- Repeated failure, timeout, or provider failure returns template fallback that is built from structured metric/value fields instead of raw evidence text.
- Metadata records prompt version, model, latency, fallback status, repair status, and validation flags.

Qwen3 must not recalculate or change the supplied spending MBTI.

## Persistence Contract

BE Phase 5 persists deterministic analysis and AI report records in four tables. BE Phase 6 orchestrates writes to those tables:

- `analysis_runs`: execution status, `result_status`, provisional reasons, analysis period, source marker, schema/analysis version, minimized `AnalysisInput` snapshot, snapshot hash, and optional `retried_from_analysis_id`.
- `behavior_metrics`: AN Phase 2 `BehaviorFeatureResult` rows with `feature_code`, `status`, `raw_value`, `normalized_score`, `unit`, `sample_count`, evidence, schema/calculation version, snapshot hash, and `metric_metadata.axisContributions`.
- `consumption_mbti_results`: nullable `mbti_type`, duplicated `result_status`, axis scores, fixed E/N/F/P score directions, confidence, coverage, limitations, schema/rule version, and snapshot hash.
- `ai_reports`: report status, generated content when available, failure/fallback fields, model, prompt version, repair status, validation result, schema version, and snapshot hash.

`analysis_runs.status` is execution state and must not be mixed with `analysis_runs.result_status`. `READY`, `ANALYZING`, `REPORT_GENERATING`, `PENDING`, and `RUNNING` rows keep `result_status=NULL`. Terminal successful states `COMPLETED`, `PARTIALLY_COMPLETED`, and `COMPLETED_WITH_FALLBACK` set `result_status` after preprocessing, feature calculation, and rule execution determine result quality. `FAILED` rows keep `result_status=NULL`. `result_status=INSUFFICIENT_DATA` must keep `consumption_mbti_results.mbti_type` as `NULL`.

`analysis_input_snapshot` stores only the DTO fields passed into deterministic analysis. It excludes account numbers, card numbers, bank credentials, raw CSV text, and transaction descriptions; merchant values are stored as normalized `merchant_key`. `snapshot_hash` is calculated from this immutable snapshot so a failed run can be retried against the same input.

Child persistence rows inherit `snapshot_hash` from `analysis_runs`; callers must not provide divergent child snapshot hashes.

AI report fallback or failure does not change deterministic rule results. A fallback report uses `COMPLETED_WITH_FALLBACK`; a report failure after deterministic result persistence uses `PARTIALLY_COMPLETED`. If the combined preprocessing and rule status is `INSUFFICIENT_DATA`, AI report generation is skipped and the run completes with deterministic result rows only. A `PARTIALLY_COMPLETED` run with `ai_reports.status=FAILED` can retry report generation by updating the existing `ai_reports` row; this retry does not create a new analysis run or recalculate deterministic outputs. Report retry must use the persisted input snapshot for member MBTI summary so the generated report does not mix current group state with historical metric/rule evidence.
