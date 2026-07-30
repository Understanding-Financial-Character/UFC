# Analysis Output Contract

## Purpose

Defines deterministic analysis outputs consumed by backend persistence, frontend result views, and Qwen3 report generation.

## Status

Behavior feature output is implemented by AN Phase 2. Axis scoring, final consumption MBTI, and grounded AI report output remain target contracts for later phases.

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
  ]
}
```

Behavior features include calculation evidence and minimum-data handling. Missing inputs produce `status=UNAVAILABLE` with `rawValue=null` and `normalizedScore=null`, not zero.

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
  "mbtiType": "ENFP",
  "axisScores": {
    "EI": 0.62,
    "SN": 0.58,
    "TF": 0.55,
    "JP": 0.71
  },
  "confidence": {
    "level": "LOW",
    "score": 0.42
  },
  "resultStatus": "PROVISIONAL",
  "provisionalReasons": ["INSUFFICIENT_TRANSACTION_COUNT"],
  "limitations": ["거래 건수가 적어 잠정 결과입니다."]
}
```

`mbtiType` is nullable when data is insufficient.

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

AI Phase 2 does not connect analysis orchestration or `ai_reports` persistence. Those remain BE orchestration and analysis persistence phase responsibilities.
