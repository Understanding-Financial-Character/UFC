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
