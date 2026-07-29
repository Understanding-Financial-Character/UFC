# Analysis Output Contract

## Purpose

Defines the conceptual result produced by the deterministic analysis layer and consumed by frontend and AI report generation.

## Schema Version

Current draft full analysis schema version: `1.0`.

Current implemented AI Phase 1 behavior metrics schema version: `behavior-metrics-v1`.

## AI Phase 1 Behavior Metrics Contract

AI Phase 1 produces deterministic behavior metrics only. It does not calculate spending MBTI, persist analysis results, call an LLM, or shape final UI report data.

Required fields:

- `schemaVersion`: string, required, current value `behavior-metrics-v1`
- `metrics`: object, required
- `evidence`: array, required

`metrics`:

```json
{
  "categoryConcentration": 0.64,
  "spendingVolatility": 0.31,
  "repeatPurchaseRatio": 0.42,
  "weekendSpendingRatio": 0.28,
  "plannedSpendingRatio": 0.57
}
```

Metric values are rounded to two decimal places using half-up rounding. A metric value is `null` when its minimum data requirement is not met.

`evidence`:

```json
[
  {
    "metric": "categoryConcentration",
    "value": 0.64,
    "basis": "FOOD 카테고리가 전체 지출의 64%를 차지합니다."
  }
]
```

Evidence is emitted for every metric, including skipped metrics. Skipped metric evidence uses `value: null` and states the missing minimum data condition.

### AI Phase 1 Metric Rules

`categoryConcentration`:

- Formula: largest category spending amount divided by total spending amount
- Minimum data: 1 transaction
- Missing policy: `category` is required by input schema

`spendingVolatility`:

- Formula: population standard deviation of daily spending totals divided by average daily spending total
- Normalization: capped at `1.0`
- Minimum data: spending on at least 2 distinct dates
- Missing policy: not calculated with fewer than 2 distinct spending dates

`repeatPurchaseRatio`:

- Formula with explicit marker: count of `isRecurring: true` transactions divided by transactions where `isRecurring` is present
- Formula without explicit marker: transactions whose `merchantKey` appears more than once divided by transactions with `merchantKey`
- Minimum data: 2 transactions with the selected repeat signal
- Missing policy: explicit `isRecurring` markers take precedence; if none exist, `merchantKey` repetition is used; otherwise not calculated

`weekendSpendingRatio`:

- Formula: Saturday and Sunday spending amount divided by total spending amount
- Minimum data: 1 transaction
- Missing policy: `occurredAt` is required by input schema

`plannedSpendingRatio`:

- Formula: planned spending amount divided by spending amount where `isPlanned` is present
- Minimum data: 1 transaction with `isPlanned`
- Missing policy: transactions without `isPlanned` are excluded from the denominator; metric is not calculated when no planned marker exists

AI Phase 1 output is deterministic: the same normalized input must produce the same output.

## Required Fields

- `schema_version`: string, required, current value `1.0`
- `analysis_id`: UUID string, required
- `group_id`: UUID string, required
- `status`: enum, required, one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
- `result_status`: enum, required when `status` is `COMPLETED`, one of `STANDARD`, `PROVISIONAL`
- `provisional_reasons`: string enum array, required, empty when `result_status` is `STANDARD`
- `analysis_period`: object, required
- `transaction_count`: integer, required, minimum 0
- `spending_mbti`: MBTI enum string, nullable until `status` is `COMPLETED`
- `axis_scores`: object, required when `status` is `COMPLETED`
- `confidence`: object, required when `status` is `COMPLETED`
- `evidence_metrics`: object, required when `status` is `COMPLETED`
- `member_comparison_summary`: object, required when `status` is `COMPLETED`
- `graph_nodes`: array, required, may be empty before completion
- `graph_edges`: array, required, may be empty before completion
- `limitations`: array of strings, required, may be empty

## Enums

`provisional_reasons` values:

- `INSUFFICIENT_TRANSACTION_COUNT`
- `SHORT_ANALYSIS_PERIOD`
- `MISSING_CATEGORY_DATA`
- `MISSING_MERCHANT_DATA`
- `SYNTHETIC_DATA`
- `LOW_AXIS_SCORE_MARGIN`

`confidence.level` values:

- `LOW`
- `MEDIUM`
- `HIGH`

`STANDARD` means the configured MVP data sufficiency rules were met. It does not mean the result is a personality diagnosis or permanent characterization.

## Object Shapes

`analysis_period`:

```json
{
  "start": "2026-05-01",
  "end": "2026-07-29"
}
```

`axis_scores`:

```json
{
  "ei": { "left": "I", "right": "E", "score": 0.62 },
  "sn": { "left": "S", "right": "N", "score": 0.58 },
  "tf": { "left": "T", "right": "F", "score": 0.55 },
  "jp": { "left": "J", "right": "P", "score": 0.71 }
}
```

Axis score range is `0.0` to `1.0`. Scores close to `0.5` should produce `LOW_AXIS_SCORE_MARGIN`.

`confidence`:

```json
{
  "level": "LOW",
  "score": 0.42
}
```

Confidence score range is `0.0` to `1.0`.

`graph_nodes`:

```json
[
  {
    "id": "node-category-food",
    "type": "CATEGORY",
    "label": "외식",
    "weight": 0.32
  }
]
```

Node field rules:

- `id`: string, required, unique within graph
- `type`: enum, required, one of `SPENDING_MBTI`, `MEMBER_MBTI`, `CATEGORY`, `TIME_PATTERN`, `BEHAVIOR_PATTERN`
- `label`: string, required
- `weight`: number, optional, range `0.0` to `1.0`

`graph_edges`:

```json
[
  {
    "source": "node-category-food",
    "target": "node-spending-mbti",
    "type": "SUPPORTS_AXIS",
    "weight": 0.64
  }
]
```

Edge field rules:

- `source`: string, required, must reference a node id
- `target`: string, required, must reference a node id
- `type`: enum, required, one of `SUPPORTS_AXIS`, `RELATED_TO`, `DIFFERS_FROM`, `MATCHES`
- `weight`: number, optional, range `0.0` to `1.0`

## Example

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "group_id": "uuid",
  "status": "COMPLETED",
  "result_status": "PROVISIONAL",
  "provisional_reasons": ["INSUFFICIENT_TRANSACTION_COUNT"],
  "analysis_period": {
    "start": "2026-05-01",
    "end": "2026-07-29"
  },
  "transaction_count": 8,
  "spending_mbti": "ENFP",
  "axis_scores": {
    "ei": { "left": "I", "right": "E", "score": 0.62 },
    "sn": { "left": "S", "right": "N", "score": 0.58 },
    "tf": { "left": "T", "right": "F", "score": 0.55 },
    "jp": { "left": "J", "right": "P", "score": 0.71 }
  },
  "confidence": {
    "level": "LOW",
    "score": 0.42
  },
  "evidence_metrics": {},
  "member_comparison_summary": {},
  "graph_nodes": [],
  "graph_edges": [],
  "limitations": ["거래 건수가 적어 잠정 결과입니다."]
}
```

## Uncertainty Rules

Analysis output must explicitly mark results as provisional when:

- Transaction count is below the minimum threshold.
- Analysis period is too short.
- Required category or merchant data is missing.
- Data is synthetic or scenario-based.
- Axis scores are too close to call.

## AI Report Dependency

AI reports must be generated from this output and must not introduce unsupported claims.

## Status

This is a Phase 0 draft contract. Backend and AI phases may refine it, but field changes must follow `docs/contracts/api-contracts.md`.
