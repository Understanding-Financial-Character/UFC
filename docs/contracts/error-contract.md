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
    "traceId": "string"
  }
}
```

## Error Categories

| Code | HTTP status | Meaning |
| --- | --- | --- |
| `VALIDATION_ERROR` | `400` | Request payload or file input is invalid. |
| `AUTHENTICATION_REQUIRED` | `401` | Authentication credentials are missing, invalid, expired, or locked. |
| `PERMISSION_DENIED` | `403` | Authenticated user does not have the required role or permission. |
| `NOT_FOUND` | `404` | Requested resource does not exist or is not accessible. |
| `CONFLICT` | `409` | Request conflicts with current resource state. |
| `RATE_LIMITED` | `429` | Request exceeded an endpoint-specific rate limit. |
| `DATABASE_UNAVAILABLE` | `503` | Database readiness check failed. |
| `AI_REPORT_UNAVAILABLE` | `503` | LLM report generation failed or is temporarily unavailable. |
| `INTERNAL_ERROR` | `500` | Unexpected server failure. |

## Rules

- API errors must not expose secrets, stack traces, or raw database errors.
- Validation errors should identify fields when safe.
- Financial data values should not be repeated in error messages unless required for user correction.
- `details` may include field names, enum values, and validation ranges.
- `details` must not include raw uploaded transaction rows, API keys, account identifiers, or full LLM payloads.
- `traceId` must match the request trace identifier and be returned in the `X-Trace-Id` response header.
- Validation error details must be sanitized to `field`, `type`, and `message`; raw `input` and raw validator context must not be returned.
