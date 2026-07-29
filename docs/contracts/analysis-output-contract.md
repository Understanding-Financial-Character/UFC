# Analysis Output Contract

## Purpose

Defines the conceptual result produced by the deterministic analysis layer and consumed by frontend and AI report generation.

## Schema Version

Current draft schema version: `1.0`.

## Required Fields

- `schema_version`: string, required, current value `1.0`
- `analysis_id`: UUID string, required
- `group_id`: UUID string, required
- `status`: enum, required, one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
- `result_status`: enum, required when `status` is `COMPLETED`, one of `FINAL`, `PROVISIONAL`
- `provisional_reasons`: string enum array, required, empty when `result_status` is `FINAL`
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
