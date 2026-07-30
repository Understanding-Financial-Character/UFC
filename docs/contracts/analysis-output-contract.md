# Analysis Output Contract

## Purpose

Defines deterministic analysis outputs consumed by backend persistence, frontend result views, and Qwen3 report generation.

## Status

Target contract. Behavior metrics are tracked by AN Phase 2 / PR #6 and are not completed on `main`.

## Schema Versions

- `behavior-metrics-v1`
- `axis-scores-v1`
- `consumption-mbti-v1`
- `grounded-ai-report-v1`

## Behavior Metrics

```json
{
  "schemaVersion": "behavior-metrics-v1",
  "metrics": {},
  "evidence": []
}
```

Behavior metrics must include calculation evidence and minimum-data handling. Missing inputs produce unavailable metrics, not zero.

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

- Pydantic schema validation.
- Numeric evidence consistency check.
- Unsupported claim check.
- Real personality or financial diagnosis wording check.
- Financial product recommendation check.
- JSON parse/schema failure gets one repair attempt.
- Repeated failure, timeout, or provider failure returns template fallback.
- Metadata records prompt version, model, latency, fallback status, repair status, and validation flags.

Qwen3 must not recalculate or change the supplied spending MBTI.

AI Phase 2 does not connect analysis orchestration or `ai_reports` persistence. Those remain BE orchestration and analysis persistence phase responsibilities.
