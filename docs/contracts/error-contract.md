# Error Contract

## Purpose

Defines the shared error response shape for MVP APIs.

## Response Shape

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "request_id": "string"
  }
}
```

## Error Categories

| Code | HTTP status | Meaning |
| --- | --- | --- |
| `VALIDATION_ERROR` | `400` | Request payload or file input is invalid. |
| `NOT_FOUND` | `404` | Requested resource does not exist or is not accessible. |
| `CONFLICT` | `409` | Request conflicts with current resource state. |
| `AI_REPORT_UNAVAILABLE` | `503` | LLM report generation failed or is temporarily unavailable. |
| `INTERNAL_ERROR` | `500` | Unexpected server failure. |

## Rules

- API errors must not expose secrets, stack traces, or raw database errors.
- Validation errors should identify fields when safe.
- Financial data values should not be repeated in error messages unless required for user correction.
- `details` may include field names, enum values, and validation ranges.
- `details` must not include raw uploaded transaction rows, API keys, account identifiers, or full LLM payloads.
