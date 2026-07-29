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

- `VALIDATION_ERROR`: Request payload or file input is invalid.
- `NOT_FOUND`: Requested resource does not exist or is not accessible.
- `CONFLICT`: Request conflicts with current resource state.
- `ANALYSIS_NOT_READY`: Analysis result is still pending or unavailable.
- `ANALYSIS_LIMITED_DATA`: Analysis can run only as a provisional result.
- `AI_REPORT_UNAVAILABLE`: LLM report generation failed or is temporarily unavailable.
- `INTERNAL_ERROR`: Unexpected server failure.

## Rules

- API errors must not expose secrets, stack traces, or raw database errors.
- Validation errors should identify fields when safe.
- Financial data values should not be repeated in error messages unless required for user correction.
